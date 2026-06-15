# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Post-acquisition feature extraction and embedding visualization.

Computes per-window statistical features (mean, max, std, min) over processed
ultrasound waveforms and shows them as linked time-series plots, one panel per
channel.  A togglable label track at the bottom mirrors the trigger labels from
the Visualization tab.  When the session was labelled, an Embedding section
(in the bottom half of a resizable splitter) allows 2-D projection via PCA,
t-SNE, or UMAP.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
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

_FEATURE_PENS: dict[str, pg.QPen] = {
    "mean": pg.mkPen((220, 60,  60),  width=1.5),
    "max":  pg.mkPen((60,  200, 60),  width=1.5),
    "std":  pg.mkPen((60,  130, 230), width=1.5),
    "min":  pg.mkPen((230, 210, 50),  width=1.5),
}

# Matplotlib "tab10" palette (RGB)
_LABEL_PALETTE = [
    (31,  119, 180), (255, 127, 14),  (44,  160, 44),  (214, 39,  40),
    (148, 103, 189), (140, 86,  75),  (227, 119, 194), (127, 127, 127),
    (188, 189, 34),  (23,  190, 207),
]

# Labels silently excluded from feature plots and embeddings by default
_EXCLUDED_LABELS = {"init", "nan", ""}


class FeatureAnalysisWidget(QWidget):
    """
    Feature extraction and embedding visualization tab for post-acquisition data.

    Parameters
    ----------
    dataframe : pd.DataFrame
        Session dataframe produced by ``_build_runtime_dataframe``.
        Each ``tx_N`` column holds per-acquisition waveform arrays.
    channel_names : list[str]
        Enabled channel column names (e.g. ``["tx_0", "tx_1"]``).
    num_samples : int
        Depth samples per acquisition waveform.
    meas_period_ms : float
        Time between consecutive full-round scans in ms (= meas_period_ms_per_channel
        from PostRunPlotWindow).  Used for the x-axis time label.  Pass 0 to
        fall back to scan-index numbering.
    plot_options : dict or None
        Filter configuration (``transmissionFrequencyHz``, ``adcSamplingFreqHz``,
        ``bandwidthFraction``, ``enableBandpass``).
    parent : QWidget or None
    """

    ALL_FEATURES = ["mean", "max", "std", "min"]
    FIRST_DISCARD = 10  # leading depth samples to skip before windowing

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
        self._df = dataframe
        self._channel_names = channel_names
        self._num_samples = num_samples
        self._period_ms = meas_period_ms
        self._opts = plot_options or {}
        self._has_labels = "Label_str" in dataframe.columns

        # Computed state (populated on demand)
        self._features_data: dict = {}   # {ch: {"t": ndarray, "features": {feat: ndarray}}}
        self._scan_labels_plot: list[str] = []   # labels aligned to scan time axis
        self._embed_matrix: np.ndarray | None = None
        self._embed_labels: list[str] = []

        # Remember last-used selection so the label toggle can re-draw without recompute
        self._last_channels: list[str] = []
        self._last_features: list[str] = []

        self._setup_ui()

    # ------------------------------------------------------------------ #
    # UI construction                                                      #
    # ------------------------------------------------------------------ #

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        # ── Feature Extraction controls (always at top) ──────────────
        ctrl_box = QGroupBox("Feature Extraction")
        cl = QVBoxLayout(ctrl_box)
        cl.setSpacing(4)

        # Channel checkboxes
        ch_row = QHBoxLayout()
        ch_row.addWidget(QLabel("Channels:"))
        self._ch_cbs: dict[str, QCheckBox] = {}
        for ch in self._channel_names:
            cb = QCheckBox(ch)
            cb.setChecked(True)
            self._ch_cbs[ch] = cb
            ch_row.addWidget(cb)
        ch_row.addStretch()
        cl.addLayout(ch_row)

        # Feature checkboxes + optional label toggle
        feat_row = QHBoxLayout()
        feat_row.addWidget(QLabel("Features:"))
        self._feat_cbs: dict[str, QCheckBox] = {}
        for feat in self.ALL_FEATURES:
            cb = QCheckBox(feat)
            cb.setChecked(True)
            self._feat_cbs[feat] = cb
            feat_row.addWidget(cb)
        if self._has_labels:
            feat_row.addSpacing(16)
            self._show_labels_cb = QCheckBox("Show labels")
            self._show_labels_cb.setChecked(True)
            self._show_labels_cb.stateChanged.connect(self._on_labels_toggle)
            feat_row.addWidget(self._show_labels_cb)
        feat_row.addSpacing(16)
        self._show_features_cb = QCheckBox("Features over time")
        self._show_features_cb.setChecked(True)
        feat_row.addWidget(self._show_features_cb)
        feat_row.addStretch()
        cl.addLayout(feat_row)

        # Processing + window size + compute button
        opt_row = QHBoxLayout()
        opt_row.addWidget(QLabel("Processing:"))
        self._proc_combo = QComboBox()
        self._proc_combo.addItems(["env", "filtered", "log", "raw"])
        opt_row.addWidget(self._proc_combo)
        opt_row.addSpacing(12)
        opt_row.addWidget(QLabel("Window:"))
        self._win_spin = QSpinBox()
        self._win_spin.setRange(5, 200)
        self._win_spin.setValue(25)
        self._win_spin.setSuffix(" samp")
        opt_row.addWidget(self._win_spin)
        opt_row.addStretch()
        self._compute_btn = QPushButton("Compute & Plot")
        self._compute_btn.clicked.connect(self._on_compute)
        opt_row.addWidget(self._compute_btn)
        cl.addLayout(opt_row)

        root.addWidget(ctrl_box)

        # ── Vertical splitter: feature plots (top) / embeddings (bot) ─
        if self._has_labels:
            splitter = QSplitter(Qt.Orientation.Horizontal)
            root.addWidget(splitter, stretch=1)

            # Left pane — feature time-series plots
            feat_pane = QWidget()
            feat_layout = QVBoxLayout(feat_pane)
            feat_layout.setContentsMargins(0, 0, 0, 0)
            feat_title = QLabel("Features over time")
            feat_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            _fnt = feat_title.font(); _fnt.setBold(True); feat_title.setFont(_fnt)
            feat_layout.addWidget(feat_title)
            self._feat_gw = pg.GraphicsLayoutWidget()
            feat_layout.addWidget(self._feat_gw)
            splitter.addWidget(feat_pane)

            # Right pane — embedding controls + square scatter
            emb_box = QGroupBox("Embedding Visualization")
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
            emb_ctrl.addStretch()
            emb_btn = QPushButton("Compute Embeddings")
            emb_btn.clicked.connect(self._on_compute_embeddings)
            emb_ctrl.addWidget(emb_btn)
            el.addLayout(emb_ctrl)

            self._emb_gw = pg.GraphicsLayoutWidget()
            el.addWidget(self._emb_gw)

            splitter.addWidget(emb_box)
            splitter.setSizes([600, 400])  # initial 60 / 40 left / right split
            self._show_features_cb.stateChanged.connect(
                lambda state: self._feat_gw.setVisible(bool(state))
            )

        else:
            # No labels → only feature plots, no splitter needed
            feat_title = QLabel("Features over time")
            feat_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            _fnt = feat_title.font(); _fnt.setBold(True); feat_title.setFont(_fnt)
            root.addWidget(feat_title)
            self._feat_gw = pg.GraphicsLayoutWidget()
            root.addWidget(self._feat_gw, stretch=1)
            self._show_features_cb.stateChanged.connect(
                lambda state: self._feat_gw.setVisible(bool(state))
            )

    # ------------------------------------------------------------------ #
    # Processing helpers                                                   #
    # ------------------------------------------------------------------ #

    def _build_filter(self) -> UltrasoundFilter | None:
        opts = self._opts
        if not opts.get("enableBandpass", True):
            return None
        center = float(opts.get("transmissionFrequencyHz", 0.0) or 0.0)
        bw_frac = float(opts.get("bandwidthFraction", 0.45) or 0.45)
        adc_fs  = float(opts.get("adcSamplingFreqHz",  0.0) or 0.0)
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
        """Apply the selected chain to a (n_frames, n_depth) matrix."""
        data = raw.astype(float)
        filt = self._build_filter()
        if step == "raw":
            return data
        if filt is not None:
            data = filt.filter_data_postacq(data)
        if step == "filtered":
            return data
        data = UltrasoundFilter.get_envelope_postacq(data)
        if step == "env":
            return data
        return UltrasoundFilter.apply_log_compression_postacq(data)

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
        except Exception:
            logging.exception("Feature computation failed")

    def _run_feature_extraction(
        self,
        channels: list[str],
        features: list[str],
        proc: str,
        win_size: int,
    ) -> None:
        df = self._df

        # Round-robin cadence = total number of physical channels
        n_ch_total = len([c for c in df.columns if c not in _NON_CHANNEL_COLUMNS])
        if n_ch_total == 0:
            n_ch_total = len(self._channel_names)

        # ── 1. Process each channel ──────────────────────────────────
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

        # ── 2. Forward-fill; sample one row per full round-robin scan ─
        tmp = pd.DataFrame(proc_series, index=df.index)
        tmp = tmp.ffill()
        if self._has_labels and "Label_str" in df.columns:
            tmp["Label_str"] = df["Label_str"]

        scan_rows = tmp.iloc[list(range(n_ch_total - 1, len(tmp), n_ch_total))].copy()

        # ── 3. Vectorised windowed feature extraction ─────────────────
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
            )  # (n_scans, n_depth)
            n_scans, n_depth = waveforms.shape

            start   = self.FIRST_DISCARD
            usable  = n_depth - start
            if usable < win_size:
                continue
            n_windows = usable // win_size
            windowed  = waveforms[:, start : start + n_windows * win_size].reshape(
                n_scans, n_windows, win_size
            )  # (n_scans, n_windows, win_size)

            feat_mats: dict[str, np.ndarray] = {}
            for feat in features:
                if   feat == "mean": feat_mats[feat] = np.mean(windowed, axis=2)
                elif feat == "max":  feat_mats[feat] = np.max (windowed, axis=2)
                elif feat == "std":  feat_mats[feat] = np.std (windowed, axis=2)
                elif feat == "min":  feat_mats[feat] = np.min (windowed, axis=2)

            all_feat_mats[ch] = feat_mats

            # Time axis: scan_index × period_ms  (or just index if no period)
            t = (
                np.arange(n_scans, dtype=float) * self._period_ms
                if self._period_ms > 0
                else np.arange(n_scans, dtype=float)
            )

            self._features_data[ch] = {
                "t":        t,
                "features": {feat: np.mean(feat_mats[feat], axis=1) for feat in features},
            }

            common_n = n_scans if common_n is None else min(common_n, n_scans)

        # ── 4. Label track aligned to scan time axis ──────────────────
        if common_n is not None and self._has_labels and "Label_str" in scan_rows.columns:
            self._scan_labels_plot = (
                scan_rows["Label_str"].iloc[:common_n].tolist()
            )
        else:
            self._scan_labels_plot = []

        # ── 5. Embedding matrix ───────────────────────────────────────
        if common_n is not None and common_n > 0 and all_feat_mats:
            parts = [
                all_feat_mats[ch][feat][:common_n]
                for ch in channels if ch in all_feat_mats
                for feat in features
            ]
            embed_mat = np.hstack(parts)

            if self._has_labels and self._scan_labels_plot:
                self._embed_labels = [str(l) for l in self._scan_labels_plot]
            else:
                self._embed_labels = ["unknown"] * common_n

            row_ok = np.isfinite(embed_mat).all(axis=1) & np.array(
                [str(l).strip().lower() not in _EXCLUDED_LABELS for l in self._embed_labels],
                dtype=bool,
            )
            self._embed_matrix = embed_mat[row_ok]
            self._embed_labels = [self._embed_labels[i] for i, ok in enumerate(row_ok) if ok]
        else:
            self._embed_matrix = None
            self._embed_labels = []

    # ------------------------------------------------------------------ #
    # Feature plots                                                        #
    # ------------------------------------------------------------------ #

    @Slot()
    def _on_labels_toggle(self) -> None:
        if self._last_channels:
            self._refresh_feature_plots()

    def _refresh_feature_plots(self) -> None:
        channels = self._last_channels
        features = self._last_features

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

        x_label = "Time (ms)" if self._period_ms > 0 else "Scan index"
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

            # Shared x-axis: only the bottom-most plot shows tick labels
            is_bottom_ch = (row_idx == n_ch - 1) and not show_labels
            if is_bottom_ch:
                p.setLabel("bottom", x_label)
            else:
                p.hideAxis("bottom")

            t = ch_data["t"]
            for feat in features:
                y = ch_data["features"][feat]
                p.plot(t, y, pen=_FEATURE_PENS.get(feat, pg.mkPen("w", width=1.5)), name=feat)

        # ── Label track ──────────────────────────────────────────────
        if show_labels:
            raw_labels = np.array(self._scan_labels_plot)
            t_ref_full = self._features_data[present[0]]["t"]
            n_full = min(len(t_ref_full), len(raw_labels))
            raw_labels = raw_labels[:n_full]
            t_ref_trimmed = t_ref_full[:n_full]

            # Drop excluded labels ("init", "", "nan") from the track
            valid_mask = np.array(
                [str(l).strip().lower() not in _EXCLUDED_LABELS for l in raw_labels],
                dtype=bool,
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

            ticks = [(float(i), str(lbl)) for i, lbl in enumerate(unique_labels)]
            p_lbl.getAxis("left").setTicks([ticks])

            if first_vb is not None:
                p_lbl.vb.setXLink(first_vb)

            for i, lbl in enumerate(unique_labels):
                mask = codes == i
                r, g, b = _LABEL_PALETTE[i % len(_LABEL_PALETTE)]
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
            logging.warning(
                "FeatureAnalysisWidget: run 'Compute & Plot' first."
            )
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

        mat    = self._embed_matrix
        labels = list(self._embed_labels)

        row_ok = np.isfinite(mat).all(axis=1)
        mat    = mat[row_ok]
        labels = [labels[i] for i, ok in enumerate(row_ok) if ok]

        if len(mat) < 3:
            logging.warning("Not enough valid samples for embedding (need ≥ 3).")
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
        p.setAspectLocked(True)   # equal x/y scale → square scatter
        p.addLegend()

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
