# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Qt-based post-run ultrasound visualization window.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from biogui.views.plot_modes.ultrasound_filters import UltrasoundFilter

ProcessingMode = Literal["raw", "filtered", "envelope", "log"]


class PostRunPlotWindow(QWidget):
    """
    Non-blocking post-run ultrasound viewer.

    Opens alongside the main BioGUI window. Provides:
    - M-mode (ImageItem per channel) and A-mode (one plot per channel + frame slider)
    - Per-channel visibility toggles
    - Processing mode: Raw / Filtered / Envelope / Log compression
    - Editable bandpass filter parameters (center frequency, bandwidth)
    - Editable log dynamic range

    Parameters
    ----------
    file_path : Path
        Source .bio file — used for the window title.
    raw_matrices : dict[str, np.ndarray]
        Unprocessed data per channel, shaped (n_frames, n_depth_samples).
    depth_start_mm : float
        Shallowest depth in mm.
    depth_stop_mm : float
        Deepest depth in mm.
    meas_period_ms_per_channel : float
        Time between consecutive frames of a single channel (ms).
    meas_period_ms_global : float
        Time between any two successive acquisitions (ms).
    dataframe : pd.DataFrame
        Full session dataframe — used for trigger and IMU overlay rows.
    plot_options : dict or None
        Initial filter configuration (transmissionFrequencyHz, adcSamplingFreqHz,
        bandwidthFraction, enableBandpass).
    parent : QWidget or None
    """

    _COLORMAP = "CET-L2"
    _CHANNEL_COLORS = ["c", "m", "y", "g", "r", "b", "w"]

    def __init__(
        self,
        file_path: Path,
        raw_matrices: dict[str, np.ndarray],
        depth_start_mm: float,
        depth_stop_mm: float,
        meas_period_ms_per_channel: float,
        meas_period_ms_global: float,
        dataframe: pd.DataFrame,
        plot_options: dict | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Post-run — {file_path.name}")
        self.setAttribute(Qt.WA_DeleteOnClose)  # type: ignore
        self.resize(1400, 900)

        self._raw = raw_matrices
        self._depth_start = depth_start_mm
        self._depth_stop = depth_stop_mm
        self._period_per_ch = meas_period_ms_per_channel
        self._period_global = meas_period_ms_global
        self._dataframe = dataframe
        self._channel_names = list(raw_matrices.keys())

        # ── initial filter config from plot_options ──────────────────
        opts = plot_options or {}
        self._enable_bandpass: bool = bool(opts.get("enableBandpass", True))
        self._center_freq_hz: float = float(opts.get("transmissionFrequencyHz", 0.0) or 0.0)
        self._bandwidth_fraction: float = float(opts.get("bandwidthFraction", 0.45) or 0.45)
        self._adc_fs: float = float(opts.get("adcSamplingFreqHz", 0.0) or 0.0)
        self._dynamic_range: float = 40.0
        self._proc_mode: ProcessingMode = "envelope"

        # ── physical dimensions ──────────────────────────────────────
        if raw_matrices:
            first = next(iter(raw_matrices.values()))
            self._n_frames, self._n_depth = first.shape
        else:
            self._n_frames, self._n_depth = 0, 0

        self._depth_axis = (
            np.linspace(depth_start_mm, depth_stop_mm, self._n_depth)
            if self._n_depth > 0
            else np.array([])
        )

        # Initial processing (envelope by default)
        self._processed: dict[str, np.ndarray] = self._compute_all()

        # Populated during view construction — used by _reset_view
        self._all_mmode_plots: list[pg.PlotItem] = []
        self._all_amode_plots: list[pg.PlotItem] = []

        self._setup_ui()
        self._build_mmode_view()
        self._build_amode_view()
        self._stacked.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def _build_current_filter(self) -> UltrasoundFilter | None:
        """Build a bandpass filter from the current UI settings, or None."""
        if not self._enable_bandpass or self._center_freq_hz <= 0.0 or self._adc_fs <= 0.0:
            return None
        half = self._center_freq_hz * self._bandwidth_fraction / 2.0
        low = max(0.0, self._center_freq_hz - half)
        high = min(self._adc_fs / 2.0, self._center_freq_hz + half)
        if low >= high:
            return None
        return UltrasoundFilter(
            sampling_freq=self._adc_fs,
            low_cutoff=low,
            high_cutoff=high,
            enabled=True,
        )

    def _process_single(self, raw: np.ndarray) -> np.ndarray:
        """
        Process one (n_frames, n_depth) matrix with the current mode and filter.

        Returns (n_frames, n_depth).
        """
        data = np.asarray(raw, dtype=float)

        if self._proc_mode == "raw":
            return data

        filt = self._build_current_filter()
        if filt is not None:
            data = filt.filter_data_postacq(data)

        if self._proc_mode == "filtered":
            return data

        # envelope / log
        data = UltrasoundFilter.get_envelope_postacq(data)
        if self._proc_mode == "log":
            data = UltrasoundFilter.apply_log_compression_postacq(
                data, dynamic_range=self._dynamic_range
            )
        return data

    def _compute_all(self) -> dict[str, np.ndarray]:
        """Return {ch: (n_depth, n_frames)} for every channel."""
        return {ch: self._process_single(raw).T for ch, raw in self._raw.items()}

    def _reprocess_and_refresh(self) -> None:
        """Recompute all channels and push new data into every visible item."""
        self._processed = self._compute_all()
        is_log = self._proc_mode == "log"

        # M-mode
        for ch_name, img in self._mmode_image_items.items():
            mat = self._processed[ch_name]  # (n_depth, n_frames)
            if is_log:
                img.setImage(mat.T, autoLevels=False, levels=(0, 255))
            else:
                img.setImage(mat.T, autoLevels=True)

        # A-mode at current frame
        if hasattr(self, "_frame_slider"):
            frame = self._frame_slider.value()
            for ch_name, line in self._amode_lines.items():
                mat = self._processed[ch_name]
                col = min(frame, mat.shape[1] - 1)
                line.setData(self._depth_axis, mat[:, col])

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(4)
        root.setContentsMargins(6, 6, 6, 6)

        # ── Row 1: view mode + channel toggles ───────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        row1.addWidget(QLabel("View:"))
        self._mmode_btn = QPushButton("M-mode")
        self._mmode_btn.setCheckable(True)
        self._mmode_btn.setChecked(True)
        self._amode_btn = QPushButton("A-mode")
        self._amode_btn.setCheckable(True)
        view_group = QButtonGroup(self)
        view_group.addButton(self._mmode_btn)
        view_group.addButton(self._amode_btn)
        view_group.buttonClicked.connect(self._on_view_mode_changed)
        row1.addWidget(self._mmode_btn)
        row1.addWidget(self._amode_btn)
        row1.addSpacing(16)

        row1.addWidget(QLabel("Channels:"))
        self._channel_checkboxes: dict[str, QCheckBox] = {}
        for name in self._channel_names:
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.stateChanged.connect(lambda state, n=name: self._on_channel_toggled(n, bool(state)))
            row1.addWidget(cb)
            self._channel_checkboxes[name] = cb

        row1.addStretch()
        reset_btn = QPushButton("Reset View")
        reset_btn.setToolTip("Restore zoom / pan to fit all data  (also: right-click → View All)")
        reset_btn.clicked.connect(self._reset_view)
        row1.addWidget(reset_btn)
        root.addLayout(row1)

        # ── Row 2: processing mode ────────────────────────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.addWidget(QLabel("Processing:"))

        self._proc_raw_btn = QPushButton("Raw")
        self._proc_filt_btn = QPushButton("Filtered")
        self._proc_env_btn = QPushButton("Envelope")
        self._proc_log_btn = QPushButton("Log")
        self._proc_env_btn.setChecked(True)
        proc_group = QButtonGroup(self)
        for btn in (
            self._proc_raw_btn,
            self._proc_filt_btn,
            self._proc_env_btn,
            self._proc_log_btn,
        ):
            btn.setCheckable(True)
            proc_group.addButton(btn)
            row2.addWidget(btn)
        proc_group.buttonClicked.connect(self._on_proc_mode_changed)

        row2.addSpacing(16)

        # Bandpass toggle
        self._bp_cb = QCheckBox("Bandpass")
        self._bp_cb.setChecked(self._enable_bandpass)
        self._bp_cb.stateChanged.connect(self._on_filter_params_changed)
        row2.addWidget(self._bp_cb)

        # Center frequency
        row2.addWidget(QLabel("f₀:"))
        self._center_spin = QDoubleSpinBox()
        self._center_spin.setRange(0.0, 100.0)
        self._center_spin.setDecimals(2)
        self._center_spin.setSuffix(" MHz")
        self._center_spin.setSingleStep(0.5)
        self._center_spin.setMinimumWidth(110)
        self._center_spin.setValue(self._center_freq_hz / 1e6)
        self._center_spin.editingFinished.connect(self._on_filter_params_changed)
        row2.addWidget(self._center_spin)

        # Bandwidth
        row2.addWidget(QLabel("BW:"))
        self._bw_spin = QDoubleSpinBox()
        self._bw_spin.setRange(1.0, 100.0)
        self._bw_spin.setDecimals(0)
        self._bw_spin.setSuffix(" %")
        self._bw_spin.setSingleStep(5.0)
        self._bw_spin.setMinimumWidth(90)
        self._bw_spin.setValue(self._bandwidth_fraction * 100.0)
        self._bw_spin.editingFinished.connect(self._on_filter_params_changed)
        row2.addWidget(self._bw_spin)

        row2.addSpacing(16)

        # Log dynamic range (enabled only in Log mode)
        self._log_label = QLabel("Dyn. range:")
        self._log_spin = QDoubleSpinBox()
        self._log_spin.setRange(1.0, 100.0)
        self._log_spin.setDecimals(0)
        self._log_spin.setSuffix(" dB")
        self._log_spin.setSingleStep(5.0)
        self._log_spin.setMinimumWidth(90)
        self._log_spin.setValue(self._dynamic_range)
        self._log_spin.editingFinished.connect(self._on_filter_params_changed)
        self._log_label.setEnabled(False)
        self._log_spin.setEnabled(False)
        row2.addWidget(self._log_label)
        row2.addWidget(self._log_spin)

        row2.addStretch()
        root.addLayout(row2)

        # ── stacked view ─────────────────────────────────────────────
        self._stacked = QStackedWidget()
        root.addWidget(self._stacked)

    def _build_mmode_view(self) -> None:
        self._mmode_widget = pg.GraphicsLayoutWidget()
        self._mmode_image_items: dict[str, pg.ImageItem] = {}
        self._mmode_plot_items: dict[str, pg.PlotItem] = {}

        colormap = pg.colormap.get(self._COLORMAP)
        row = 0
        first_vb = None
        last_plot: pg.PlotItem | None = None

        for ch_name in self._channel_names:
            mat = self._processed[ch_name]  # (n_depth, n_frames)
            t_span = mat.shape[1] * self._period_per_ch
            depth_span = self._depth_stop - self._depth_start

            p: pg.PlotItem = self._mmode_widget.addPlot(row=row, col=0)
            p.setLabel("left", ch_name)
            p.getAxis("left").setWidth(64)
            p.getAxis("left").enableAutoSIPrefix(False)
            p.getAxis("bottom").enableAutoSIPrefix(False)
            p.invertY(True)
            p.showGrid(x=True, y=True, alpha=0.25)

            if first_vb is None:
                first_vb = p.vb
            else:
                p.vb.setXLink(first_vb)

            img = pg.ImageItem()
            img.setColorMap(colormap)
            img.setImage(mat.T, autoLevels=True)  # (n_frames, n_depth)
            img.setRect(pg.QtCore.QRectF(0.0, self._depth_start, t_span, depth_span))
            p.addItem(img)

            self._mmode_image_items[ch_name] = img
            self._mmode_plot_items[ch_name] = p
            self._all_mmode_plots.append(p)
            last_plot = p
            row += 1

        # ── trigger / IMU overlay rows ────────────────────────────────
        n_global = len(self._dataframe)
        t_global = np.arange(n_global, dtype=float) * self._period_global

        if "Label" in self._dataframe.columns:
            p = self._mmode_widget.addPlot(row=row, col=0)
            p.setLabel("left", "Trigger")
            p.getAxis("left").setWidth(64)
            p.getAxis("left").enableAutoSIPrefix(False)
            p.showGrid(x=True, y=True, alpha=0.25)
            if first_vb:
                p.vb.setXLink(first_vb)
            p.plot(
                t_global, self._dataframe["Label"].to_numpy(dtype=float), pen=pg.mkPen("y", width=1)
            )
            self._all_mmode_plots.append(p)
            last_plot = p
            row += 1

        if "Label_str" in self._dataframe.columns:
            codes, labels = pd.factorize(self._dataframe["Label_str"], sort=True)
            p = self._mmode_widget.addPlot(row=row, col=0)
            p.setLabel("left", "Trigger str")
            p.getAxis("left").setWidth(64)
            p.getAxis("left").setTicks([list(enumerate(str(lb) for lb in labels))])
            if first_vb:
                p.vb.setXLink(first_vb)
            p.plot(t_global, codes.astype(float), pen=pg.mkPen("orange", width=1))
            self._all_mmode_plots.append(p)
            last_plot = p
            row += 1

        imu_cols = [c for c in ("imu_x", "imu_y", "imu_z") if c in self._dataframe.columns]
        if imu_cols:
            p = self._mmode_widget.addPlot(row=row, col=0)
            p.setLabel("left", "IMU")
            p.getAxis("left").setWidth(64)
            p.getAxis("left").enableAutoSIPrefix(False)
            p.showGrid(x=True, y=True, alpha=0.25)
            p.addLegend()
            if first_vb:
                p.vb.setXLink(first_vb)
            for col, color in zip(("imu_x", "imu_y", "imu_z"), ("r", "g", "b")):
                if col in self._dataframe.columns:
                    p.plot(
                        t_global,
                        self._dataframe[col].to_numpy(dtype=float),
                        pen=pg.mkPen(color, width=1),
                        name=col,
                    )
            self._all_mmode_plots.append(p)
            last_plot = p

        if last_plot is not None:
            last_plot.setLabel("bottom", "Time (ms)")
            last_plot.getAxis("bottom").enableAutoSIPrefix(False)

        self._stacked.addWidget(self._mmode_widget)

    def _build_amode_view(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._amode_graphics = pg.GraphicsLayoutWidget()
        self._amode_plot_items_per_ch: dict[str, pg.PlotItem] = {}
        self._amode_lines: dict[str, pg.PlotDataItem] = {}

        first_vb = None
        n_ch = len(self._channel_names)
        for i, ch_name in enumerate(self._channel_names):
            mat = self._processed[ch_name]  # (n_depth, n_frames)
            color = self._CHANNEL_COLORS[i % len(self._CHANNEL_COLORS)]

            p: pg.PlotItem = self._amode_graphics.addPlot(row=i, col=0)
            p.setLabel("left", ch_name)
            p.getAxis("left").setWidth(64)
            p.getAxis("left").enableAutoSIPrefix(False)
            p.getAxis("bottom").enableAutoSIPrefix(False)
            p.showGrid(x=True, y=True, alpha=0.25)
            p.setXRange(self._depth_start, self._depth_stop, padding=0.01)

            if first_vb is None:
                first_vb = p.vb
            else:
                p.vb.setXLink(first_vb)

            if i == n_ch - 1:
                p.setLabel("bottom", "Depth (mm)")

            initial = mat[:, 0] if mat.shape[1] > 0 else np.zeros(self._n_depth)
            line = p.plot(self._depth_axis, initial, pen=pg.mkPen(color, width=1.5))

            self._amode_plot_items_per_ch[ch_name] = p
            self._amode_lines[ch_name] = line
            self._all_amode_plots.append(p)

        layout.addWidget(self._amode_graphics)

        # ── frame slider ─────────────────────────────────────────────
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("Frame:"))
        self._frame_slider = QSlider(Qt.Horizontal)  # type: ignore
        self._frame_slider.setRange(0, max(0, self._n_frames - 1))
        self._frame_slider.setValue(0)
        self._frame_label = QLabel(f"0 / {max(0, self._n_frames - 1)}")
        self._frame_slider.valueChanged.connect(self._on_frame_changed)
        slider_row.addWidget(self._frame_slider, stretch=1)
        slider_row.addWidget(self._frame_label)
        layout.addLayout(slider_row)

        self._stacked.addWidget(container)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _reset_view(self) -> None:
        """Restore all plots in the active view to fit their full data range."""
        plots = (
            self._all_mmode_plots if self._stacked.currentIndex() == 0 else self._all_amode_plots
        )
        for p in plots:
            p.autoRange()

    def _on_view_mode_changed(self, button: QPushButton) -> None:
        self._stacked.setCurrentIndex(0 if button is self._mmode_btn else 1)

    def _on_channel_toggled(self, channel_name: str, visible: bool) -> None:
        if channel_name in self._mmode_plot_items:
            self._mmode_plot_items[channel_name].setVisible(visible)
        if channel_name in self._amode_plot_items_per_ch:
            self._amode_plot_items_per_ch[channel_name].setVisible(visible)

    def _on_proc_mode_changed(self, button: QPushButton) -> None:
        mode_map: dict[QPushButton, ProcessingMode] = {
            self._proc_raw_btn: "raw",
            self._proc_filt_btn: "filtered",
            self._proc_env_btn: "envelope",
            self._proc_log_btn: "log",
        }
        self._proc_mode = mode_map.get(button, "envelope")
        is_log = self._proc_mode == "log"
        self._log_label.setEnabled(is_log)
        self._log_spin.setEnabled(is_log)
        self._reprocess_and_refresh()

    def _on_filter_params_changed(self) -> None:
        self._enable_bandpass = self._bp_cb.isChecked()
        self._center_freq_hz = self._center_spin.value() * 1e6
        self._bandwidth_fraction = self._bw_spin.value() / 100.0
        self._dynamic_range = self._log_spin.value()
        self._reprocess_and_refresh()

    def _on_frame_changed(self, frame: int) -> None:
        self._frame_label.setText(f"{frame} / {max(0, self._n_frames - 1)}")
        for ch_name, line in self._amode_lines.items():
            if not self._channel_checkboxes[ch_name].isChecked():
                continue
            mat = self._processed[ch_name]
            col = min(frame, mat.shape[1] - 1)
            line.setData(self._depth_axis, mat[:, col])
