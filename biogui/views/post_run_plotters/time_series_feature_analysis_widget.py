# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Post-acquisition feature extraction and embedding visualization for time-series signals.

Feature Extraction controls are arranged in four side-by-side columns:
  Channels | Features | Processing | Display

All controls auto-trigger recomputation via a debounce timer.

Unlike the ultrasound variant (each channel is a fixed-length waveform repeated
once per acquisition, giving a natural "scan" axis), a time-series channel is
one continuous sample stream. Windows are therefore defined in *time* (ms) —
not samples — and slid directly across the whole recording, independently per
channel (channels may have different native sampling rates); the window count
is then trimmed to the shortest channel so per-channel feature columns line up
for the embedding.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from biogui.controllers.signal_filters import TimeSeriesFilter

from .bio_file_utils import group_channels_by_signal
from .embedding_utils import BASE_EXCLUDED_LABELS, LABEL_PALETTE, refresh_embedding_plot, run_embedding

_FEATURE_PENS: dict[str, tuple[int, int, int]] = {
    "mean": (220, 60, 60),
    "max": (60, 200, 60),
    "std": (60, 130, 230),
    "min": (230, 210, 50),
}

_FILTER_TYPES = ["highpass", "lowpass", "bandpass", "bandstop"]

# Mapping from user-facing combo text to internal processing key
_PROC_DISPLAY_TO_KEY: dict[str, str] = {
    "Raw data": "raw",
    "Filtered": "filtered",
}

_GB_BOLD = "QGroupBox { font-weight: bold; }"


def _vsep() -> QFrame:
    """Thin vertical separator for use between columns."""
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFrameShadow(QFrame.Shadow.Sunken)
    return sep


def _col_header(text: str) -> QLabel:
    """Bold column-header label."""
    lbl = QLabel(text)
    font = lbl.font()
    font.setBold(True)
    lbl.setFont(font)
    return lbl


class TimeSeriesFeatureAnalysisWidget(QWidget):
    """
    Feature extraction and embedding visualization tab for time-series recordings.

    Parameters
    ----------
    channels : dict[str, dict]
        Flattened per-channel data: {chName: {"data": 1D ndarray, "fs": float,
        "sigName": str, "chIdx": int}}.
    trigger_str : ndarray or None
        Trigger label strings, one per recorded packet (not one per sample).
    trigger_t : ndarray or None
        Relative time (seconds, since recording start) for each trigger_str entry.
    plot_options : dict or None
        Initial filter config ("signalFilters": {sigName: {filtType, freqs, filtOrder}}).
    parent : QWidget or None
    """

    ALL_FEATURES = ["mean", "max", "std", "min"]

    def __init__(
        self,
        channels: dict[str, dict],
        trigger_str: np.ndarray | None,
        trigger_t: np.ndarray | None,
        plot_options: dict | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        _f = self.font()
        _f.setPointSize(max(10, _f.pointSize()))
        self.setFont(_f)

        self._channels = channels
        self._channel_names = list(channels.keys())
        self._signal_groups = group_channels_by_signal(channels)
        self._trigger_str = trigger_str
        self._trigger_t = trigger_t
        self._has_labels = trigger_str is not None and trigger_t is not None

        opts = plot_options or {}
        signal_filters_cfg: dict = opts.get("signalFilters") or {}
        default_cfg: dict = next(iter(signal_filters_cfg.values()), {}) or {}
        self._filt_type: str = default_cfg.get("filtType", "bandpass")
        self._freqs: list[float] = [float(f) for f in default_cfg.get("freqs", [20.0, 450.0])]
        self._filt_order: int = int(default_cfg.get("filtOrder", 4))
        self._default_proc = "Filtered" if signal_filters_cfg else "Raw data"

        # Computed state
        self._features_data: dict = {}
        self._scan_labels_plot: list[str] = []
        self._embed_matrix: np.ndarray | None = None
        self._embed_labels: list[str] = []
        self._last_channels: list[str] = []
        self._last_features: list[str] = []

        # Debounce timer for data-changing controls
        self._recompute_timer = QTimer(self)
        self._recompute_timer.setSingleShot(True)
        self._recompute_timer.setInterval(300)
        self._recompute_timer.timeout.connect(self._on_compute)

        self._setup_ui()
        QTimer.singleShot(0, self._on_compute)

    def _schedule_recompute(self) -> None:
        self._recompute_timer.start()

    def _get_excluded_labels(self) -> set[str]:
        excl = set(BASE_EXCLUDED_LABELS)
        if hasattr(self, "_exclude_rest_cb") and self._exclude_rest_cb.isChecked():
            excl.add("rest")
        return excl

    # ------------------------------------------------------------------ #
    # UI construction                                                      #
    # ------------------------------------------------------------------ #

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        ctrl_box = QGroupBox("Feature Extraction")
        ctrl_box.setStyleSheet(_GB_BOLD)
        cl = QHBoxLayout(ctrl_box)
        cl.setSpacing(10)
        cl.setContentsMargins(8, 14, 8, 8)

        # ── Column 1 : Channels (compact grid, 2 per row) ────────────
        c1 = QVBoxLayout()
        c1.setSpacing(3)
        c1.addWidget(_col_header("Channels"))
        self._ch_cbs: dict[str, QCheckBox] = {}
        ch_grid = QGridLayout()
        ch_grid.setSpacing(4)
        for i, ch in enumerate(self._channel_names):
            cb = QCheckBox(ch)
            cb.setChecked(True)
            self._ch_cbs[ch] = cb
            cb.stateChanged.connect(self._schedule_recompute)
            ch_grid.addWidget(cb, i // 2, i % 2)
        c1.addLayout(ch_grid)
        c1.addStretch()
        cl.addLayout(c1)

        cl.addWidget(_vsep())

        # ── Column 2 : Features (single horizontal row) ──────────────
        c2 = QVBoxLayout()
        c2.setSpacing(3)
        c2.addWidget(_col_header("Features"))
        self._feat_cbs: dict[str, QCheckBox] = {}
        feat_row = QHBoxLayout()
        feat_row.setSpacing(8)
        for feat in self.ALL_FEATURES:
            cb = QCheckBox(feat)
            cb.setChecked(feat == "mean")
            self._feat_cbs[feat] = cb
            cb.stateChanged.connect(self._schedule_recompute)
            feat_row.addWidget(cb)
        feat_row.addStretch()
        c2.addLayout(feat_row)
        c2.addStretch()
        cl.addLayout(c2)

        cl.addWidget(_vsep())

        # ── Column 3 : Processing ────────────────────────────────────
        c3 = QVBoxLayout()
        c3.setSpacing(4)
        c3.addWidget(_col_header("Processing"))

        self._proc_combo = QComboBox()
        self._proc_combo.addItems(list(_PROC_DISPLAY_TO_KEY.keys()))
        self._proc_combo.setCurrentText(self._default_proc)
        self._proc_combo.currentTextChanged.connect(self._schedule_recompute)
        c3.addWidget(self._proc_combo)

        _spin_w = 78
        _lbl_w = 44

        self._filt_type_combo = QComboBox()
        self._filt_type_combo.addItems(_FILTER_TYPES)
        self._filt_type_combo.setCurrentText(self._filt_type)
        self._filt_type_combo.currentTextChanged.connect(self._on_filt_type_changed)
        c3.addWidget(self._filt_type_combo)

        self._freq1_spin = QDoubleSpinBox()
        self._freq1_spin.setRange(0.01, 100000.0)
        self._freq1_spin.setDecimals(2)
        self._freq1_spin.setMinimumWidth(_spin_w)
        self._freq1_spin.setValue(self._freqs[0] if self._freqs else 20.0)
        self._freq1_spin.valueChanged.connect(self._schedule_recompute)

        self._freq2_spin = QDoubleSpinBox()
        self._freq2_spin.setRange(0.01, 100000.0)
        self._freq2_spin.setDecimals(2)
        self._freq2_spin.setMinimumWidth(_spin_w)
        self._freq2_spin.setValue(self._freqs[1] if len(self._freqs) > 1 else 450.0)
        self._freq2_spin.setEnabled(self._filt_type in ("bandpass", "bandstop"))
        self._freq2_spin.valueChanged.connect(self._schedule_recompute)

        self._order_spin = QDoubleSpinBox()
        self._order_spin.setDecimals(0)
        self._order_spin.setRange(1, 10)
        self._order_spin.setValue(self._filt_order)
        self._order_spin.valueChanged.connect(self._schedule_recompute)

        self._win_spin = QDoubleSpinBox()
        self._win_spin.setRange(1.0, 60000.0)
        self._win_spin.setDecimals(0)
        self._win_spin.setValue(200.0)
        self._win_spin.setMinimumWidth(_spin_w)
        self._win_spin.editingFinished.connect(self._schedule_recompute)

        self._stride_spin = QDoubleSpinBox()
        self._stride_spin.setRange(1.0, 60000.0)
        self._stride_spin.setDecimals(0)
        self._stride_spin.setValue(100.0)
        self._stride_spin.setMinimumWidth(_spin_w)
        self._stride_spin.editingFinished.connect(self._schedule_recompute)

        def _param_cell(label: str, spin: QWidget, unit: str) -> QHBoxLayout:
            row = QHBoxLayout()
            row.setSpacing(3)
            lbl = QLabel(label)
            lbl.setMinimumWidth(_lbl_w)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(lbl)
            row.addWidget(spin)
            row.addWidget(QLabel(unit))
            return row

        pgrid = QGridLayout()
        pgrid.setHorizontalSpacing(12)
        pgrid.setVerticalSpacing(4)
        pgrid.addLayout(_param_cell("Freq 1", self._freq1_spin, "Hz"), 0, 0)
        pgrid.addLayout(_param_cell("Freq 2", self._freq2_spin, "Hz"), 0, 1)
        pgrid.addLayout(_param_cell("Order", self._order_spin, ""), 1, 0)
        pgrid.addLayout(_param_cell("Window", self._win_spin, "ms"), 2, 0)
        pgrid.addLayout(_param_cell("Stride", self._stride_spin, "ms"), 2, 1)
        c3.addLayout(pgrid)

        if self._has_labels:
            self._exclude_rest_cb = QCheckBox("Exclude 'rest'")
            self._exclude_rest_cb.setChecked(True)
            self._exclude_rest_cb.stateChanged.connect(self._schedule_recompute)
            c3.addWidget(self._exclude_rest_cb)

        c3.addStretch()
        cl.addLayout(c3)

        cl.addWidget(_vsep())

        # ── Column 4 : Display ───────────────────────────────────────
        c4 = QVBoxLayout()
        c4.setSpacing(4)
        c4.addWidget(_col_header("Display"))

        if self._has_labels:
            self._show_labels_cb = QCheckBox("Show labels")
            self._show_labels_cb.setChecked(True)
            self._show_labels_cb.stateChanged.connect(self._refresh_feature_plots)
            c4.addWidget(self._show_labels_cb)

        self._show_features_cb = QCheckBox("Features over time")
        self._show_features_cb.setChecked(False)
        c4.addWidget(self._show_features_cb)

        c4.addStretch()
        cl.addLayout(c4)

        root.addWidget(ctrl_box)

        # ══════════════════════════════════════════════════════════════
        # Main visualization area
        # ══════════════════════════════════════════════════════════════
        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, stretch=1)

        self._feat_pane = QGroupBox("Features over time")
        self._feat_pane.setStyleSheet(_GB_BOLD)
        feat_layout = QVBoxLayout(self._feat_pane)
        feat_layout.setContentsMargins(4, 8, 4, 4)
        self._feat_gw = pg.GraphicsLayoutWidget()
        feat_layout.addWidget(self._feat_gw)
        self._feat_pane.setVisible(False)
        splitter.addWidget(self._feat_pane)

        emb_box = QGroupBox("Embedding Visualization")
        emb_box.setStyleSheet(_GB_BOLD)
        el = QVBoxLayout(emb_box)

        emb_ctrl = QHBoxLayout()
        emb_ctrl.addWidget(QLabel("Method:"))
        self._emb_bg = QButtonGroup(self)
        for i, method in enumerate(["PCA", "t-SNE", "UMAP"]):
            rb = QRadioButton(method)
            if i == 0:
                rb.setChecked(True)
            self._emb_bg.addButton(rb, i)
            emb_ctrl.addWidget(rb)
        self._emb_bg.buttonToggled.connect(
            lambda _, checked: self._on_compute_embeddings() if checked else None
        )
        emb_ctrl.addStretch()
        el.addLayout(emb_ctrl)

        self._emb_gw = pg.GraphicsLayoutWidget()
        el.addWidget(self._emb_gw)

        splitter.addWidget(emb_box)
        splitter.setSizes([600, 400])

        self._show_features_cb.stateChanged.connect(
            lambda state: self._feat_pane.setVisible(bool(state))
        )

    def _on_filt_type_changed(self, filt_type: str) -> None:
        self._freq2_spin.setEnabled(filt_type in ("bandpass", "bandstop"))
        self._schedule_recompute()

    # ------------------------------------------------------------------ #
    # Processing helpers                                                   #
    # ------------------------------------------------------------------ #

    def _build_filter(self, sig_name: str) -> TimeSeriesFilter | None:
        group = self._signal_groups[sig_name]
        filt_type = self._filt_type_combo.currentText()
        freqs = (
            [self._freq1_spin.value(), self._freq2_spin.value()]
            if filt_type in ("bandpass", "bandstop")
            else [self._freq1_spin.value()]
        )
        filt_order = int(self._order_spin.value())

        if any(f >= group["fs"] / 2 for f in freqs):
            return None

        filt = TimeSeriesFilter(group["fs"], group["data"].shape[1])
        filt.configure({"filtType": filt_type, "freqs": freqs, "filtOrder": filt_order})
        return filt

    def _apply_processing(self, ch: str, raw: np.ndarray, step: str) -> np.ndarray:
        internal = _PROC_DISPLAY_TO_KEY.get(step, step)
        if internal == "raw":
            return raw

        sig_name = self._channels[ch]["sigName"]
        group = self._signal_groups[sig_name]
        try:
            filt = self._build_filter(sig_name)
        except Exception:
            logging.exception("Failed to build filter for '%s'", sig_name)
            return raw
        if filt is None:
            return raw

        ch_idx = group["chNames"].index(ch)
        filtered_full = filt.process(np.asarray(group["data"], dtype=float))
        return filtered_full[:, ch_idx]

    # ------------------------------------------------------------------ #
    # Feature computation                                                  #
    # ------------------------------------------------------------------ #

    @Slot()
    def _on_compute(self) -> None:
        channels = [ch for ch, cb in self._ch_cbs.items() if cb.isChecked()]
        features = [f for f, cb in self._feat_cbs.items() if cb.isChecked()]
        proc = self._proc_combo.currentText()
        win_ms = self._win_spin.value()
        stride_ms = self._stride_spin.value()

        if not channels or not features:
            return

        try:
            self._run_feature_extraction(channels, features, proc, win_ms, stride_ms)
            self._refresh_feature_plots()
            if hasattr(self, "_emb_bg"):
                self._on_compute_embeddings()
        except Exception:
            logging.exception("Feature computation failed")

    def _labels_for_windows(self, t_start_ms: np.ndarray, win_ms: float) -> list[str]:
        """Majority-vote trigger_str label for each window's time span.

        Trigger entries are timestamped events (one per packet), not a uniform-rate
        signal, so windows are matched against them via binary search on the
        (monotonic) relative-time axis rather than a fixed-fs sample grid.
        """
        trig = self._trigger_str
        trig_t = self._trigger_t
        n_trig = len(trig)
        labels: list[str] = []
        for t0 in t_start_ms:
            start_idx = np.searchsorted(trig_t, t0 / 1000.0, side="left")
            end_idx = np.searchsorted(trig_t, (t0 + win_ms) / 1000.0, side="left")
            if end_idx <= start_idx:
                end_idx = min(start_idx + 1, n_trig)
            segment = trig[start_idx:end_idx]
            if len(segment) == 0:
                labels.append("")
                continue
            values, counts = np.unique(segment, return_counts=True)
            labels.append(str(values[np.argmax(counts)]))
        return labels

    def _run_feature_extraction(
        self,
        channels: list[str],
        features: list[str],
        proc: str,
        win_ms: float,
        stride_ms: float,
    ) -> None:
        per_channel: dict[str, dict] = {}
        common_n: int | None = None

        for ch in channels:
            if ch not in self._channels:
                continue
            fs = self._channels[ch]["fs"]
            raw = np.asarray(self._channels[ch]["data"], dtype=float)
            data = self._apply_processing(ch, raw, proc)

            win_size = max(1, int(round(win_ms / 1000.0 * fs)))
            stride = max(1, int(round(stride_ms / 1000.0 * fs)))
            n_samp = len(data)
            if n_samp < win_size:
                continue
            n_windows = 1 + (n_samp - win_size) // stride
            starts = np.arange(n_windows) * stride
            windowed = np.stack([data[s : s + win_size] for s in starts], axis=0)

            feat_arrs: dict[str, np.ndarray] = {}
            for feat in features:
                if feat == "mean":
                    feat_arrs[feat] = np.mean(windowed, axis=1)
                elif feat == "max":
                    feat_arrs[feat] = np.max(windowed, axis=1)
                elif feat == "std":
                    feat_arrs[feat] = np.std(windowed, axis=1)
                elif feat == "min":
                    feat_arrs[feat] = np.min(windowed, axis=1)

            t_ms = starts / fs * 1000.0
            per_channel[ch] = {"t": t_ms, "feat": feat_arrs, "win_ms": win_ms}
            common_n = n_windows if common_n is None else min(common_n, n_windows)

        self._features_data = per_channel
        self._last_channels = channels
        self._last_features = features

        if common_n is None or common_n == 0 or not per_channel:
            self._scan_labels_plot = []
            self._embed_matrix = None
            self._embed_labels = []
            return

        excl = self._get_excluded_labels()
        ref_ch = next(iter(per_channel))
        t_ref_ms = per_channel[ref_ch]["t"][:common_n]

        if self._has_labels:
            window_labels = self._labels_for_windows(t_ref_ms, win_ms)
        else:
            window_labels = ["unknown"] * common_n
        self._scan_labels_plot = window_labels

        parts = [
            per_channel[ch]["feat"][feat][:common_n]
            for ch in channels
            if ch in per_channel
            for feat in features
        ]

        if parts:
            embed_mat = np.column_stack(parts)
            row_ok = np.isfinite(embed_mat).all(axis=1) & np.array(
                [str(lbl).strip().lower() not in excl for lbl in window_labels], dtype=bool
            )
            self._embed_matrix = embed_mat[row_ok]
            self._embed_labels = [window_labels[i] for i, ok in enumerate(row_ok) if ok]
        else:
            self._embed_matrix = None
            self._embed_labels = []

    # ------------------------------------------------------------------ #
    # Feature plots                                                        #
    # ------------------------------------------------------------------ #

    def _refresh_feature_plots(self) -> None:
        channels = self._last_channels
        features = self._last_features
        excl = self._get_excluded_labels()

        self._feat_gw.clear()
        present = [ch for ch in channels if ch in self._features_data]
        if not present:
            return

        show_labels = (
            self._has_labels
            and hasattr(self, "_show_labels_cb")
            and self._show_labels_cb.isChecked()
            and bool(self._scan_labels_plot)
        )
        x_label = "Time (ms)"
        first_vb: pg.ViewBox | None = None
        n_ch = len(present)

        for row_idx, ch in enumerate(present):
            ch_data = self._features_data[ch]
            p: pg.PlotItem = self._feat_gw.addPlot(row=row_idx, col=0)
            p.setLabel("left", ch)
            p.getAxis("left").setWidth(64)
            p.getAxis("left").enableAutoSIPrefix(False)
            p.getAxis("bottom").enableAutoSIPrefix(False)
            p.showGrid(x=True, y=True, alpha=0.25)
            p.addLegend(labelTextSize="11pt")

            if first_vb is None:
                first_vb = p.vb
            else:
                p.vb.setXLink(first_vb)

            is_bottom_ch = (row_idx == n_ch - 1) and not show_labels
            if is_bottom_ch:
                p.setLabel("bottom", x_label)
            else:
                p.hideAxis("bottom")

            t = ch_data["t"]
            feat_arrs = ch_data["feat"]
            for feat in features:
                if feat not in feat_arrs:
                    continue
                r, g, b = _FEATURE_PENS[feat]
                n = min(len(t), len(feat_arrs[feat]))
                p.plot(
                    t[:n],
                    feat_arrs[feat][:n],
                    pen=pg.mkPen((r, g, b), width=1.5),
                    name=feat,
                )

        if show_labels:
            raw_labels = np.array(self._scan_labels_plot)
            t_ref_full = self._features_data[present[0]]["t"]
            n_full = min(len(t_ref_full), len(raw_labels))
            raw_labels = raw_labels[:n_full]
            t_ref_trimmed = t_ref_full[:n_full]

            valid_mask = np.array(
                [str(lbl).strip().lower() not in excl for lbl in raw_labels], dtype=bool
            )
            labels_arr = raw_labels[valid_mask]
            t_plot = t_ref_trimmed[valid_mask]
            codes, unique_labels = pd.factorize(labels_arr, sort=True)
            c_plot = codes.astype(float)

            p_lbl: pg.PlotItem = self._feat_gw.addPlot(row=n_ch, col=0)
            p_lbl.setLabel("left", "Label")
            p_lbl.setLabel("bottom", x_label)
            p_lbl.getAxis("left").setWidth(64)
            p_lbl.getAxis("left").enableAutoSIPrefix(False)
            p_lbl.getAxis("bottom").enableAutoSIPrefix(False)
            p_lbl.showGrid(x=True, y=True, alpha=0.25)
            p_lbl.getAxis("left").setTicks(
                [[(float(i), str(lbl)) for i, lbl in enumerate(unique_labels)]]
            )
            if first_vb is not None:
                p_lbl.vb.setXLink(first_vb)

            for i, lbl in enumerate(unique_labels):
                mask = codes == i
                r, g, b = LABEL_PALETTE[i % len(LABEL_PALETTE)]
                p_lbl.plot(
                    t_plot[mask],
                    c_plot[mask],
                    pen=None,
                    symbol="s",
                    symbolSize=5,
                    symbolPen=pg.mkPen(None),
                    symbolBrush=pg.mkBrush(r, g, b, 200),
                    name=str(lbl),
                )

    # ------------------------------------------------------------------ #
    # Embedding                                                            #
    # ------------------------------------------------------------------ #

    @Slot()
    def _on_compute_embeddings(self) -> None:
        if self._embed_matrix is None or len(self._embed_matrix) == 0:
            return
        method_id = self._emb_bg.checkedId()
        method = ["PCA", "t-SNE", "UMAP"][method_id]
        try:
            X_2d, labels = run_embedding(self._embed_matrix, self._embed_labels, method)
            if X_2d is not None:
                refresh_embedding_plot(self._emb_gw, X_2d, labels, method, self._has_labels)
        except Exception:
            logging.exception("Embedding failed")
