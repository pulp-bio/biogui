# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Qt-based post-run time-series visualization window.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from biogui.controllers.signal_filters import TimeSeriesFilter

from .bio_file_utils import group_channels_by_signal

ProcessingMode = Literal["raw", "filtered"]

_FILTER_TYPES = ["highpass", "lowpass", "bandpass", "bandstop"]


class TimeSeriesPlotWindow(QWidget):
    """
    Non-blocking post-run time-series viewer.

    Opens alongside the main BioGUI window. Provides:
    - One stacked, X-linked line plot per channel, plus optional trigger overlay rows
    - Per-channel visibility toggles
    - Processing mode: Raw / Filtered (Butterworth, matching the live TimeSeriesFilter)
    - Editable filter parameters (type, cutoff frequency/ies, order)

    Parameters
    ----------
    file_path : Path
        Source .bio file — used for the window title.
    channels : dict[str, dict]
        Per-channel data, keyed by flattened channel name. Each entry has "data"
        (1D ndarray), "fs", "sigName" and "chIdx".
    trigger : ndarray or None
        Numeric trigger codes, one per recorded packet (not one per sample).
    trigger_str : ndarray or None
        Trigger label strings, aligned index-for-index with `trigger`.
    trigger_t : ndarray or None
        Relative time (seconds, since recording start) for each trigger entry.
    plot_options : dict or None
        Initial filter configuration: "signalFilters" (dict of sigName ->
        {filtType, freqs, filtOrder}), used to seed the default filter params.
    parent : QWidget or None
    """

    _CHANNEL_COLORS = ["c", "m", "y", "g", "r", "b", "w", "orange"]

    def __init__(
        self,
        file_path: Path,
        channels: dict[str, dict],
        trigger: np.ndarray | None,
        trigger_str: np.ndarray | None,
        trigger_t: np.ndarray | None,
        plot_options: dict | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Post-run — {file_path.name}")
        self.setAttribute(Qt.WA_DeleteOnClose)  # type: ignore
        self.resize(1400, 900)

        self._file_path = file_path
        self._channels = channels
        self._channel_names = list(channels.keys())
        self._trigger = trigger
        self._trigger_str = trigger_str
        self._trigger_t = trigger_t
        self._signal_groups = group_channels_by_signal(channels)

        # ── initial filter config from plot_options ──────────────────
        opts = plot_options or {}
        signal_filters_cfg: dict = opts.get("signalFilters") or {}
        default_cfg: dict = next(iter(signal_filters_cfg.values()), {}) or {}
        self._filt_type: str = default_cfg.get("filtType", "bandpass")
        self._freqs: list[float] = [float(f) for f in default_cfg.get("freqs", [20.0, 450.0])]
        self._filt_order: int = int(default_cfg.get("filtOrder", 4))
        self._proc_mode: ProcessingMode = "filtered" if signal_filters_cfg else "raw"

        # Debounce timer for spinbox valueChanged -> avoids reprocessing on every step
        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(300)
        self._filter_timer.timeout.connect(self._on_filter_params_changed)

        self._processed: dict[str, np.ndarray] = self._compute_all()

        self._all_plots: list[pg.PlotItem] = []
        self._plot_items: dict[str, pg.PlotItem] = {}
        self._plot_lines: dict[str, pg.PlotDataItem] = {}

        self._vis_container = QWidget()
        self._setup_ui()
        self._build_view()

        # ── Feature Analysis tab ─────────────────────────────────────
        from .time_series_feature_analysis_widget import TimeSeriesFeatureAnalysisWidget

        feature_widget = TimeSeriesFeatureAnalysisWidget(
            channels=self._channels,
            trigger_str=self._trigger_str,
            trigger_t=self._trigger_t,
            plot_options=plot_options,
            parent=self,
        )

        outer_tabs = QTabWidget()
        outer_tabs.addTab(self._vis_container, "Visualization")
        outer_tabs.addTab(feature_widget, "Feature Analysis")

        top = QVBoxLayout(self)
        top.setContentsMargins(0, 0, 0, 0)
        top.addWidget(outer_tabs)

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def _build_filter_for_signal(self, sig_name: str) -> TimeSeriesFilter | None:
        if self._proc_mode != "filtered":
            return None
        if self._filt_type in ("bandpass", "bandstop") and (
            len(self._freqs) < 2 or self._freqs[1] <= self._freqs[0]
        ):
            return None
        if any(f >= self._signal_groups[sig_name]["fs"] / 2 for f in self._freqs):
            return None

        group = self._signal_groups[sig_name]
        n_ch = group["data"].shape[1]
        filt = TimeSeriesFilter(group["fs"], n_ch)
        filt.configure(
            {
                "filtType": self._filt_type,
                "freqs": self._freqs,
                "filtOrder": self._filt_order,
            }
        )
        return filt

    def _compute_all(self) -> dict[str, np.ndarray]:
        """Return {chName: 1D processed array}."""
        processed: dict[str, np.ndarray] = {}
        for sig_name, group in self._signal_groups.items():
            data = np.asarray(group["data"], dtype=float)
            try:
                filt = self._build_filter_for_signal(sig_name)
                if filt is not None:
                    data = filt.process(data)
            except Exception:
                logging.exception("Time-series filtering failed for '%s'; showing raw.", sig_name)
            for i, ch_name in enumerate(group["chNames"]):
                processed[ch_name] = data[:, i]
        return processed

    def _reprocess_and_refresh(self) -> None:
        self._processed = self._compute_all()
        for ch_name, line in self._plot_lines.items():
            fs = self._channels[ch_name]["fs"]
            t = np.arange(len(self._processed[ch_name])) / fs
            line.setData(t, self._processed[ch_name], skipFiniteCheck=True)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self._vis_container)
        root.setSpacing(4)
        root.setContentsMargins(6, 6, 6, 6)

        # ── Row 1: channel toggles ────────────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(6)
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

        # ── Row 2: processing mode + filter params ───────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.addWidget(QLabel("Processing:"))

        self._proc_raw_btn = QPushButton("Raw")
        self._proc_filt_btn = QPushButton("Filtered")
        for btn in (self._proc_raw_btn, self._proc_filt_btn):
            btn.setCheckable(True)
        proc_group = QButtonGroup(self)
        proc_group.addButton(self._proc_raw_btn)
        proc_group.addButton(self._proc_filt_btn)
        (self._proc_filt_btn if self._proc_mode == "filtered" else self._proc_raw_btn).setChecked(
            True
        )
        proc_group.buttonClicked.connect(self._on_proc_mode_changed)
        row2.addWidget(self._proc_raw_btn)
        row2.addWidget(self._proc_filt_btn)

        row2.addSpacing(16)

        row2.addWidget(QLabel("Type:"))
        self._filt_type_combo = QComboBox()
        self._filt_type_combo.addItems(_FILTER_TYPES)
        self._filt_type_combo.setCurrentText(self._filt_type)
        self._filt_type_combo.currentTextChanged.connect(self._on_filt_type_changed)
        row2.addWidget(self._filt_type_combo)

        row2.addWidget(QLabel("Freq 1:"))
        self._freq1_spin = QDoubleSpinBox()
        self._freq1_spin.setRange(0.01, 100000.0)
        self._freq1_spin.setDecimals(2)
        self._freq1_spin.setSuffix(" Hz")
        self._freq1_spin.setMinimumWidth(110)
        self._freq1_spin.setValue(self._freqs[0] if self._freqs else 20.0)
        self._freq1_spin.valueChanged.connect(self._filter_timer.start)
        row2.addWidget(self._freq1_spin)

        row2.addWidget(QLabel("Freq 2:"))
        self._freq2_spin = QDoubleSpinBox()
        self._freq2_spin.setRange(0.01, 100000.0)
        self._freq2_spin.setDecimals(2)
        self._freq2_spin.setSuffix(" Hz")
        self._freq2_spin.setMinimumWidth(110)
        self._freq2_spin.setValue(self._freqs[1] if len(self._freqs) > 1 else 450.0)
        self._freq2_spin.valueChanged.connect(self._filter_timer.start)
        row2.addWidget(self._freq2_spin)
        self._freq2_spin.setEnabled(self._filt_type in ("bandpass", "bandstop"))

        row2.addWidget(QLabel("Order:"))
        self._order_spin = QSpinBox()
        self._order_spin.setRange(1, 10)
        self._order_spin.setValue(self._filt_order)
        self._order_spin.valueChanged.connect(self._filter_timer.start)
        row2.addWidget(self._order_spin)

        row2.addStretch()
        root.addLayout(row2)

        # ── plot area ──────────────────────────────────────────────
        self._graphics_widget = pg.GraphicsLayoutWidget()
        root.addWidget(self._graphics_widget, 1)

    def _build_view(self) -> None:
        first_vb: pg.ViewBox | None = None
        row = 0

        for ch_name in self._channel_names:
            fs = self._channels[ch_name]["fs"]
            data = self._processed[ch_name]
            t = np.arange(len(data)) / fs
            color = self._CHANNEL_COLORS[row % len(self._CHANNEL_COLORS)]

            p: pg.PlotItem = self._graphics_widget.addPlot(row=row, col=0)
            p.setLabel("left", ch_name)
            p.getAxis("left").setWidth(64)
            p.getAxis("left").enableAutoSIPrefix(False)
            p.getAxis("bottom").enableAutoSIPrefix(False)
            p.showGrid(x=True, y=True, alpha=0.25)

            if first_vb is None:
                first_vb = p.vb
            else:
                p.vb.setXLink(first_vb)

            line = p.plot(t, data, pen=pg.mkPen(color, width=1))
            line.setClipToView(True)
            line.setDownsampling(auto=True, method="peak")

            self._plot_items[ch_name] = p
            self._plot_lines[ch_name] = line
            self._all_plots.append(p)
            row += 1

        # ── trigger / trigger_str overlay rows ────────────────────────
        if self._trigger_t is not None:
            if self._trigger is not None:
                p = self._graphics_widget.addPlot(row=row, col=0)
                p.setLabel("left", "Trigger")
                p.getAxis("left").setWidth(64)
                p.getAxis("left").enableAutoSIPrefix(False)
                p.showGrid(x=True, y=True, alpha=0.25)
                if first_vb:
                    p.vb.setXLink(first_vb)
                p.plot(
                    self._trigger_t, self._trigger.astype(float), pen=pg.mkPen("y", width=1)
                )
                self._all_plots.append(p)
                row += 1

            if self._trigger_str is not None:
                codes, labels = pd.factorize(pd.Series(self._trigger_str), sort=True)
                p = self._graphics_widget.addPlot(row=row, col=0)
                p.setLabel("left", "Trigger str")
                p.getAxis("left").setWidth(64)
                p.getAxis("left").setTicks([list(enumerate(str(lb) for lb in labels))])
                if first_vb:
                    p.vb.setXLink(first_vb)
                p.plot(self._trigger_t, codes.astype(float), pen=pg.mkPen("orange", width=1))
                self._all_plots.append(p)
                row += 1

        # Shared time axis: only the bottom-most plot shows tick labels
        for _p in self._all_plots[:-1]:
            _p.hideAxis("bottom")
        if self._all_plots:
            self._all_plots[-1].setLabel("bottom", "Time (s)")
            self._all_plots[-1].getAxis("bottom").enableAutoSIPrefix(False)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _reset_view(self) -> None:
        for p in self._all_plots:
            p.autoRange()

    def _on_channel_toggled(self, channel_name: str, visible: bool) -> None:
        if channel_name in self._plot_items:
            self._plot_items[channel_name].setVisible(visible)

    def _on_proc_mode_changed(self, button: QPushButton) -> None:
        self._proc_mode = "filtered" if button is self._proc_filt_btn else "raw"
        self._reprocess_and_refresh()

    def _on_filt_type_changed(self, filt_type: str) -> None:
        self._freq2_spin.setEnabled(filt_type in ("bandpass", "bandstop"))
        self._filter_timer.start()

    def _on_filter_params_changed(self) -> None:
        self._filt_type = self._filt_type_combo.currentText()
        self._filt_order = self._order_spin.value()
        if self._filt_type in ("bandpass", "bandstop"):
            self._freqs = [self._freq1_spin.value(), self._freq2_spin.value()]
        else:
            self._freqs = [self._freq1_spin.value()]
        self._reprocess_and_refresh()
