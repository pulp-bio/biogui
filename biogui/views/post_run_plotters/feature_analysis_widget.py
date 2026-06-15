# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Post-acquisition feature extraction and embedding visualization.

Feature Extraction controls are arranged in four side-by-side columns:
  Channels | Features | Processing | Display

All controls auto-trigger recomputation via a debounce timer.
Features over time is disabled by default so the embedding fills the screen.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from biogui.views.plot_modes.ultrasound_filters import UltrasoundFilter

_NON_CHANNEL_COLUMNS = {
    "Label", "Label_str", "imu_x", "imu_y", "imu_z", "rx_id",
    "timestamp", "trigger", "trigger_str",
}

_FEATURE_PENS: dict[str, tuple[int, int, int]] = {
    "mean": (220, 60,  60),
    "max":  (60,  200, 60),
    "std":  (60,  130, 230),
    "min":  (230, 210, 50),
}

# Matplotlib "tab10" palette (RGB)
_LABEL_PALETTE = [
    (31,  119, 180), (255, 127, 14),  (44,  160, 44),  (214, 39,  40),
    (148, 103, 189), (140, 86,  75),  (227, 119, 194), (127, 127, 127),
    (188, 189, 34),  (23,  190, 207),
]

# Labels always excluded from plots / embeddings (cannot be re-enabled from UI)
_BASE_EXCLUDED_LABELS = {"init", "nan", ""}

# Mapping from user-facing combo text to internal processing key
_PROC_DISPLAY_TO_KEY: dict[str, str] = {
    "Raw data":          "raw",
    "Filtered":          "filtered",
    "Hilbert Envelope":  "env",
    "Log Compression":   "log",
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


class FeatureAnalysisWidget(QWidget):
    """
    Feature extraction and embedding visualization tab.

    Parameters
    ----------
    dataframe : pd.DataFrame
        Session dataframe from ``_build_runtime_dataframe``.
    channel_names : list[str]
        Enabled channel column names.
    num_samples : int
        Depth samples per waveform.
    meas_period_ms : float
        Time between consecutive full-round scans (ms).  0 → scan-index axis.
    plot_options : dict or None
        Initial filter config (transmissionFrequencyHz, adcSamplingFreqHz, …).
    parent : QWidget or None
    """

    ALL_FEATURES = ["mean", "max", "std", "min"]
    FIRST_DISCARD = 10

    def __init__(
        self,
        dataframe: pd.DataFrame,
        channel_names: list[str],
        num_samples: int,
        meas_period_ms: float = 0.0,
        plot_options: dict | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        _f = self.font()
        _f.setPointSize(max(10, _f.pointSize()))
        self.setFont(_f)

        self._df = dataframe
        self._channel_names = channel_names
        self._num_samples = num_samples
        self._period_ms = meas_period_ms
        self._opts: dict = dict(plot_options or {})
        self._has_labels = "Label_str" in dataframe.columns

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
        excl = set(_BASE_EXCLUDED_LABELS)
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

        # ══════════════════════════════════════════════════════════════
        # Feature Extraction group — compact 4-column layout
        # ══════════════════════════════════════════════════════════════
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
            cb.setChecked(feat == "max")
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
        # Default: Hilbert Envelope (index 2)
        self._proc_combo.setCurrentIndex(2)
        self._proc_combo.currentTextChanged.connect(self._on_proc_combo_changed)
        c3.addWidget(self._proc_combo)

        # ── 2×2 parameter grid ───────────────────────────────────────
        _spin_w = 72   # numbers-only spinbox, no suffix
        _lbl_w  = 44   # parameter label width

        self._win_spin = QSpinBox()
        self._win_spin.setRange(5, 200)
        self._win_spin.setValue(25)
        self._win_spin.setMinimumWidth(_spin_w)
        self._win_spin.editingFinished.connect(self._schedule_recompute)

        self._fa_f0_spin = QDoubleSpinBox()
        self._fa_f0_spin.setRange(0.0, 100.0)
        self._fa_f0_spin.setDecimals(2)
        self._fa_f0_spin.setSingleStep(0.25)
        self._fa_f0_spin.setMinimumWidth(_spin_w)
        self._fa_f0_spin.setValue(
            float(self._opts.get("transmissionFrequencyHz", 2.25e6) or 2.25e6) / 1e6
        )
        self._fa_f0_spin.valueChanged.connect(self._on_filter_ui_changed)

        self._fa_bw_spin = QDoubleSpinBox()
        self._fa_bw_spin.setRange(1.0, 100.0)
        self._fa_bw_spin.setDecimals(0)
        self._fa_bw_spin.setSingleStep(5.0)
        self._fa_bw_spin.setMinimumWidth(_spin_w)
        self._fa_bw_spin.setValue(
            float(self._opts.get("bandwidthFraction", 0.30) or 0.30) * 100.0
        )
        self._fa_bw_spin.valueChanged.connect(self._on_filter_ui_changed)

        self._fa_adc_spin = QDoubleSpinBox()
        self._fa_adc_spin.setRange(1.0, 1000.0)
        self._fa_adc_spin.setDecimals(2)
        self._fa_adc_spin.setSingleStep(1.0)
        self._fa_adc_spin.setMinimumWidth(_spin_w)
        self._fa_adc_spin.setValue(
            float(self._opts.get("adcSamplingFreqHz", 8.0e6) or 8.0e6) / 1e6
        )
        self._fa_adc_spin.valueChanged.connect(self._on_filter_ui_changed)

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
        pgrid.addLayout(_param_cell("Window", self._win_spin,    "samp"), 0, 0)
        pgrid.addLayout(_param_cell("f₀",  self._fa_f0_spin,  "MHz"),  0, 1)
        pgrid.addLayout(_param_cell("BW",     self._fa_bw_spin,  "%"),    1, 0)
        pgrid.addLayout(_param_cell("ADC fs", self._fa_adc_spin, "MHz"),  1, 1)
        c3.addLayout(pgrid)

        # Dynamic range row — only visible for Log Compression
        self._dyn_spin = QDoubleSpinBox()
        self._dyn_spin.setRange(1.0, 100.0)
        self._dyn_spin.setDecimals(0)
        self._dyn_spin.setSingleStep(5.0)
        self._dyn_spin.setValue(40.0)
        self._dyn_spin.setMinimumWidth(_spin_w)
        self._dyn_spin.valueChanged.connect(self._schedule_recompute)
        self._dyn_row = QWidget()
        dyn_layout = QHBoxLayout(self._dyn_row)
        dyn_layout.setContentsMargins(0, 0, 0, 0)
        dyn_layout.setSpacing(3)
        dyn_lbl = QLabel("Dyn. range")
        dyn_lbl.setMinimumWidth(_lbl_w)
        dyn_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        dyn_layout.addWidget(dyn_lbl)
        dyn_layout.addWidget(self._dyn_spin)
        dyn_layout.addWidget(QLabel("dB"))
        dyn_layout.addStretch()
        self._dyn_row.setVisible(False)
        c3.addWidget(self._dyn_row)

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

        # "Features over time" toggle + indented sub-options
        self._show_features_cb = QCheckBox("Features over time")
        self._show_features_cb.setChecked(False)
        c4.addWidget(self._show_features_cb)

        # Sub-options — indented, disabled when features are hidden
        sub_w = QWidget()
        sub_layout = QVBoxLayout(sub_w)
        sub_layout.setContentsMargins(18, 0, 0, 0)
        sub_layout.setSpacing(2)
        self._plot_mode_bg = QButtonGroup(self)
        rb_mean = QRadioButton("Mean")
        rb_mean.setChecked(True)
        rb_all = QRadioButton("All windows")
        self._plot_mode_bg.addButton(rb_mean, 0)
        self._plot_mode_bg.addButton(rb_all, 1)
        sub_layout.addWidget(rb_mean)
        sub_layout.addWidget(rb_all)
        self._plot_mode_bg.buttonToggled.connect(
            lambda _, checked: self._refresh_feature_plots() if checked else None
        )
        sub_w.setEnabled(False)  # grayed out while features-over-time is off
        c4.addWidget(sub_w)

        self._show_features_cb.stateChanged.connect(
            lambda state: sub_w.setEnabled(bool(state))
        )

        c4.addStretch()
        cl.addLayout(c4)

        root.addWidget(ctrl_box)

        # ══════════════════════════════════════════════════════════════
        # Main visualization area
        # ══════════════════════════════════════════════════════════════
        if self._has_labels:
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

        else:
            self._feat_pane = QGroupBox("Features over time")
            self._feat_pane.setStyleSheet(_GB_BOLD)
            feat_layout = QVBoxLayout(self._feat_pane)
            feat_layout.setContentsMargins(4, 8, 4, 4)
            self._feat_gw = pg.GraphicsLayoutWidget()
            feat_layout.addWidget(self._feat_gw)
            self._feat_pane.setVisible(False)
            root.addWidget(self._feat_pane, stretch=1)
            self._show_features_cb.stateChanged.connect(
                lambda state: self._feat_pane.setVisible(bool(state))
            )

    # ------------------------------------------------------------------ #
    # Processing combo handler                                             #
    # ------------------------------------------------------------------ #

    @Slot(str)
    def _on_proc_combo_changed(self, text: str) -> None:
        self._dyn_row.setVisible(text == "Log Compression")
        self._schedule_recompute()

    # ------------------------------------------------------------------ #
    # Filter UI handler                                                    #
    # ------------------------------------------------------------------ #

    def _on_filter_ui_changed(self) -> None:
        self._opts["transmissionFrequencyHz"] = self._fa_f0_spin.value() * 1e6
        self._opts["bandwidthFraction"]       = self._fa_bw_spin.value() / 100.0
        self._opts["adcSamplingFreqHz"]       = self._fa_adc_spin.value() * 1e6
        self._opts["enableBandpass"]          = True
        self._schedule_recompute()

    # ------------------------------------------------------------------ #
    # Processing helpers                                                   #
    # ------------------------------------------------------------------ #

    def _build_filter(self) -> UltrasoundFilter | None:
        opts    = self._opts
        if not opts.get("enableBandpass", True):
            return None
        center  = float(opts.get("transmissionFrequencyHz", 2.25e6) or 2.25e6)
        bw_frac = float(opts.get("bandwidthFraction", 0.30) or 0.30)
        adc_fs  = float(opts.get("adcSamplingFreqHz",  8.0e6) or 8.0e6)
        if center <= 0.0 or adc_fs <= 0.0:
            return None
        half = center * bw_frac / 2.0
        low  = max(0.0, center - half)
        high = min(adc_fs / 2.0, center + half)
        if low >= high:
            return None
        return UltrasoundFilter(
            sampling_freq=adc_fs, low_cutoff=low, high_cutoff=high, enabled=True
        )

    def _apply_processing(self, raw: np.ndarray, step: str) -> np.ndarray:
        """
        Apply the selected processing chain.  `step` may be either the display
        name (e.g. "Hilbert Envelope") or the internal key ("env").
        """
        internal = _PROC_DISPLAY_TO_KEY.get(step, step)
        data = raw.astype(float)
        filt = self._build_filter()

        if internal == "raw":
            return data

        if filt is not None:
            data = filt.filter_data_postacq(data)

        if internal == "filtered":
            return data

        data = UltrasoundFilter.get_envelope_postacq(data)

        if internal == "env":
            return data

        dyn_range = self._dyn_spin.value() if hasattr(self, "_dyn_spin") else 40.0
        return UltrasoundFilter.apply_log_compression_postacq(data, dynamic_range=dyn_range)

    # ------------------------------------------------------------------ #
    # Feature computation                                                  #
    # ------------------------------------------------------------------ #

    @Slot()
    def _on_compute(self) -> None:
        channels = [ch for ch, cb in self._ch_cbs.items() if cb.isChecked()]
        features = [f  for f,  cb in self._feat_cbs.items() if cb.isChecked()]
        proc     = self._proc_combo.currentText()
        win_size = self._win_spin.value()

        if not channels or not features:
            return

        try:
            self._run_feature_extraction(channels, features, proc, win_size)
            self._last_channels = channels
            self._last_features = features
            self._refresh_feature_plots()
            if self._has_labels and hasattr(self, "_emb_bg"):
                self._on_compute_embeddings()
        except Exception:
            logging.exception("Feature computation failed")

    def _run_feature_extraction(
        self,
        channels: list[str],
        features: list[str],
        proc: str,
        win_size: int,
    ) -> None:
        df   = self._df
        excl = self._get_excluded_labels()

        n_ch_total = len([c for c in df.columns if c not in _NON_CHANNEL_COLUMNS])
        if n_ch_total == 0:
            n_ch_total = len(self._channel_names)

        proc_series: dict[str, pd.Series] = {}
        for ch in channels:
            if ch not in df.columns:
                continue
            raw_s = df[ch].dropna()
            if raw_s.empty:
                continue
            raw_mat   = np.vstack(raw_s.to_numpy())
            processed = self._apply_processing(raw_mat, proc)
            proc_series[ch] = pd.Series(list(processed), index=raw_s.index)

        if not proc_series:
            self._features_data = {}
            self._scan_labels_plot = []
            self._embed_matrix = None
            self._embed_labels = []
            return

        tmp = pd.DataFrame(proc_series, index=df.index).ffill()
        if self._has_labels and "Label_str" in df.columns:
            tmp["Label_str"] = df["Label_str"]

        scan_rows = tmp.iloc[list(range(n_ch_total - 1, len(tmp), n_ch_total))].copy()

        self._features_data = {}
        all_feat_mats: dict[str, dict[str, np.ndarray]] = {}
        common_n: int | None = None

        for ch in channels:
            if ch not in proc_series:
                continue
            ch_col = scan_rows[ch].dropna()
            if ch_col.empty:
                continue

            waveforms = np.vstack(
                [np.asarray(w, dtype=float).ravel() for w in ch_col.to_numpy()]
            )
            n_scans, n_depth = waveforms.shape

            start    = self.FIRST_DISCARD
            usable   = n_depth - start
            if usable < win_size:
                continue
            n_windows = usable // win_size
            windowed  = waveforms[:, start : start + n_windows * win_size].reshape(
                n_scans, n_windows, win_size
            )

            feat_mats: dict[str, np.ndarray] = {}
            for feat in features:
                if   feat == "mean": feat_mats[feat] = np.mean(windowed, axis=2)
                elif feat == "max":  feat_mats[feat] = np.max (windowed, axis=2)
                elif feat == "std":  feat_mats[feat] = np.std (windowed, axis=2)
                elif feat == "min":  feat_mats[feat] = np.min (windowed, axis=2)

            all_feat_mats[ch] = feat_mats

            t = (
                np.arange(n_scans, dtype=float) * self._period_ms
                if self._period_ms > 0
                else np.arange(n_scans, dtype=float)
            )
            self._features_data[ch] = {
                "t":         t,
                "feat_mats": {feat: feat_mats[feat] for feat in features},
            }
            common_n = n_scans if common_n is None else min(common_n, n_scans)

        if common_n is not None and self._has_labels and "Label_str" in scan_rows.columns:
            self._scan_labels_plot = scan_rows["Label_str"].iloc[:common_n].tolist()
        else:
            self._scan_labels_plot = []

        if common_n is not None and common_n > 0 and all_feat_mats:
            parts = [
                all_feat_mats[ch][feat][:common_n]
                for ch in channels if ch in all_feat_mats
                for feat in features
            ]
            embed_mat = np.hstack(parts)

            raw_embed_labels = (
                [str(l) for l in self._scan_labels_plot]
                if self._has_labels and self._scan_labels_plot
                else ["unknown"] * common_n
            )

            row_ok = np.isfinite(embed_mat).all(axis=1) & np.array(
                [str(l).strip().lower() not in excl for l in raw_embed_labels],
                dtype=bool,
            )
            self._embed_matrix = embed_mat[row_ok]
            self._embed_labels = [raw_embed_labels[i] for i, ok in enumerate(row_ok) if ok]
        else:
            self._embed_matrix = None
            self._embed_labels = []

    # ------------------------------------------------------------------ #
    # Feature plots                                                        #
    # ------------------------------------------------------------------ #

    def _refresh_feature_plots(self) -> None:
        channels = self._last_channels
        features = self._last_features
        excl     = self._get_excluded_labels()

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
        all_windows = self._plot_mode_bg.checkedId() == 1
        x_label     = "Time (ms)" if self._period_ms > 0 else "Scan index"
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

            t         = ch_data["t"]
            feat_mats = ch_data["feat_mats"]

            for feat in features:
                if feat not in feat_mats:
                    continue
                mat = feat_mats[feat]
                r, g, b = _FEATURE_PENS[feat]

                if all_windows:
                    n_windows = mat.shape[1]
                    alpha = max(40, min(200, int(220 / max(n_windows, 1))))
                    for w in range(n_windows):
                        p.plot(
                            t, mat[:, w],
                            pen=pg.mkPen((r, g, b, alpha), width=1),
                            name=feat if w == 0 else None,
                        )
                else:
                    p.plot(
                        t, np.mean(mat, axis=1),
                        pen=pg.mkPen((r, g, b), width=1.5),
                        name=feat,
                    )

        if show_labels:
            raw_labels = np.array(self._scan_labels_plot)
            t_ref_full = self._features_data[present[0]]["t"]
            n_full     = min(len(t_ref_full), len(raw_labels))
            raw_labels    = raw_labels[:n_full]
            t_ref_trimmed = t_ref_full[:n_full]

            valid_mask = np.array(
                [str(l).strip().lower() not in excl for l in raw_labels], dtype=bool
            )
            labels_arr = raw_labels[valid_mask]
            t_plot     = t_ref_trimmed[valid_mask]
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
                r, g, b = _LABEL_PALETTE[i % len(_LABEL_PALETTE)]
                p_lbl.plot(
                    t_plot[mask], c_plot[mask],
                    pen=None, symbol="s", symbolSize=5,
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
            X_2d, labels = self._run_embedding(method)
            if X_2d is not None:
                self._refresh_embedding_plot(X_2d, labels, method)
        except Exception:
            logging.exception("Embedding failed")

    def _run_embedding(
        self, method: str
    ) -> tuple[np.ndarray | None, list[str]]:
        try:
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            logging.warning("scikit-learn required (pip install scikit-learn).")
            return None, []

        mat = self._embed_matrix
        if mat is None:
            return None, []
        labels = list(self._embed_labels)

        row_ok = np.isfinite(mat).all(axis=1)
        mat    = mat[row_ok]
        labels = [labels[i] for i, ok in enumerate(row_ok) if ok]

        if len(mat) < 3:
            logging.warning("Not enough valid samples for embedding (need >= 3).")
            return None, []

        X = StandardScaler().fit_transform(mat)

        if method == "PCA":
            from sklearn.decomposition import PCA
            X_2d = PCA(n_components=2).fit_transform(X)
        elif method == "t-SNE":
            from sklearn.manifold import TSNE
            perp = min(30, len(mat) - 1)
            X_2d = TSNE(n_components=2, perplexity=perp, random_state=42).fit_transform(X)
        elif method == "UMAP":
            try:
                import umap as _umap
                nn   = min(15, len(mat) - 1)
                X_2d = _umap.UMAP(
                    n_components=2, n_neighbors=nn, random_state=42
                ).fit_transform(X)
            except ImportError:
                logging.warning("umap-learn not installed (pip install umap-learn).")
                return None, []
        else:
            return None, []

        return X_2d, labels

    def _refresh_embedding_plot(
        self, X_2d: np.ndarray, labels: list[str], method: str
    ) -> None:
        self._emb_gw.clear()
        p: pg.PlotItem = self._emb_gw.addPlot()
        p.setLabel("bottom", f"{method} dim 1")
        p.setLabel("left",   f"{method} dim 2")
        p.setTitle(f"{method}  —  coloured by label")
        p.showGrid(x=True, y=True, alpha=0.25)
        p.setAspectLocked(True)
        p.addLegend(labelTextSize="11pt")

        unique_labels = list(dict.fromkeys(labels))
        arr = np.array(labels)
        for i, lbl in enumerate(unique_labels):
            mask    = arr == lbl
            r, g, b = _LABEL_PALETTE[i % len(_LABEL_PALETTE)]
            p.addItem(
                pg.ScatterPlotItem(
                    x=X_2d[mask, 0],
                    y=X_2d[mask, 1],
                    size=8,
                    pen=pg.mkPen(None),
                    brush=pg.mkBrush(r, g, b, 180),
                    name=lbl,
                )
            )
