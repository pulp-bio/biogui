"""
Class for A-mode ultrasound visualization.


Copyright 2025 Enzo Baraldi

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

from collections import deque

import numpy as np
import pyqtgraph as pg

from .base_plot_mode import BasePlotMode
from .ultrasound_filters import UltrasoundFilter


class AModePlotMode(BasePlotMode):
    """
    Plot mode for A-mode ultrasound visualization.

    Displays the latest complete scan as amplitude vs. depth.

    Parameters
    ----------
    fs : float
        Sampling frequency (measurement rate).
    nCh : int
        Number of channels.
    chSpacing : float
        Spacing between each channel in the plot.
    renderLenMs : int
        Length of the window in the plot (in ms) - not used for A-mode.
    **config : dict
        Additional configuration options, including:
        - signal_type: Dict with ultrasound configuration
        - dataQueue: Optional pre-existing data queue
        - minRange: Optional minimum Y range
        - maxRange: Optional maximum Y range
        - showRaw: Show raw RF data
        - showFiltered: Show filtered data
        - showEnvelope: Show envelope
        - enableBandpass: Enable bandpass filter
        - bandpassLow: Low cutoff frequency in Hz
        - bandpassHigh: High cutoff frequency in Hz

    Attributes
    ----------
    _data_queue : deque
        Ring buffer for storing data.
    _raw_plots : list
        List of PlotDataItem references for raw data.
    _filtered_plots : list
        List of PlotDataItem references for filtered data.
    _envelope_plots : list
        List of PlotDataItem references for envelope data.
    _num_samples : int
        Number of samples per scan.
    _adc_start_delay : float
        ADC start delay in seconds.
    _adc_sampling_freq : float
        ADC sampling frequency in Hz.
    _meas_period_us : float or None
        Measurement period in microseconds.
    _scan_count : int
        Number of complete scans processed.
    _graph_widget : PlotWidget or None
        Reference to the plot widget.
    _us_filter : UltrasoundFilter
        Ultrasound filter instance.
    _show_raw : bool
        Whether to show raw data.
    _show_filtered : bool
        Whether to show filtered data.
    _show_envelope : bool
        Whether to show envelope.
    """

    SPEED_OF_SOUND = 1540  # m/s in tissue

    def __init__(
        self,
        fs: float,
        nCh: int,
        chSpacing: float,
        renderLenMs: int,
        **config: dict,
    ) -> None:
        super().__init__(fs, nCh, chSpacing, **config)

        # Extract ultrasound configuration
        signal_type = config.get("signal_type", {})
        self._num_samples = signal_type["num_samples"]
        self._adc_start_delay = signal_type["adc_start_delay"]
        self._adc_sampling_freq = signal_type["adc_sampling_freq"]
        self._meas_period_us = signal_type.get("meas_period")

        # Ultrasound display configuration
        self._show_raw = config.get("showRaw", True)
        self._show_filtered = config.get("showFiltered", False)
        self._show_envelope = config.get("showEnvelope", False)

        # Initialize ultrasound filter
        enable_bandpass = config.get("enableBandpass", False)
        bandpass_low = config.get("bandpassLow", self._adc_sampling_freq / 2 * 0.1)
        bandpass_high = config.get("bandpassHigh", self._adc_sampling_freq / 2 * 0.9)

        self._us_filter = UltrasoundFilter(
            sampling_freq=self._adc_sampling_freq,
            low_cutoff=bandpass_low,
            high_cutoff=bandpass_high,
            enabled=enable_bandpass,
        )

        # Initialize data queue
        render_len_samples = self._num_samples
        self._data_queue = deque(maxlen=render_len_samples)

        # Pre-fill with existing data or zeros
        if "dataQueue" in config:
            self._data_queue.extend(config["dataQueue"])
        else:
            for _ in range(render_len_samples):
                self._data_queue.append(np.zeros(nCh))

        self._raw_plots = []
        self._filtered_plots = []
        self._envelope_plots = []
        self._scan_count = 0
        self._graph_widget = None

    def add_data(self, data: np.ndarray) -> None:
        """Add data to the queue."""
        self._data_queue.extend(data)
        self._sample_count += data.shape[0]

        # Track complete scans
        # assumes data arrives in complete scans
        self._scan_count += data.shape[0] // self._num_samples

    def has_new_data(self) -> bool:
        """Check if we have enough data for at least one complete scan."""
        return len(self._data_queue) >= self._num_samples

    def setup_plot(self, graph_widget) -> None:
        """Setup A-mode plot with depth axis and multiple display options."""
        self._graph_widget = graph_widget
        graph_widget.clear()

        plot_item = graph_widget.getPlotItem()
        plot_item.showAxis("bottom")
        plot_item.showAxis("left")

        # Disable auto SI prefix for consistent mm display
        bottom_axis = plot_item.getAxis("bottom")
        bottom_axis.enableAutoSIPrefix(False)

        left_axis = plot_item.getAxis("left")
        left_axis.enableAutoSIPrefix(False)

        plot_item.setLabel("bottom", "Depth", units="mm")
        plot_item.setLabel("left", "Amplitude", units="ADC code")

        # Set Y range if provided
        if "minRange" in self.config and "maxRange" in self.config:
            graph_widget.setYRange(self.config["minRange"], self.config["maxRange"])

        # Get colormap
        cm = pg.colormap.get("CET-C1")
        cm.setMappingMode("diverging")
        lut = cm.getLookupTable(nPts=self.n_ch, mode="qcolor")

        # Create plot dictionaries for different display modes
        self._raw_plots = []
        self._filtered_plots = []
        self._envelope_plots = []

        depth_axis = self._calculate_distance_axis()
        latest_samples = self._get_latest_scan_data()

        # Precompute filtered and envelope data
        filtered_data = (
            self._filter_data(latest_samples)
            if self._show_filtered or self._show_envelope
            else None
        )
        envelope_data = (
            self._get_envelope(filtered_data) if self._show_envelope else None
        )

        for i in range(self.n_ch):
            color = lut[i]
            vertical_offset = self.ch_spacing * (self.n_ch - i - 1)

            # Raw data plot (blue)
            if self._show_raw:
                pen = pg.mkPen(
                    color=color, width=1, style=pg.QtCore.Qt.PenStyle.SolidLine
                )
                raw_plot = graph_widget.plot(
                    depth_axis,
                    latest_samples[:, i] + vertical_offset,
                    pen=pen,
                    name=f"Raw Ch{i}",
                )
                raw_plot.setClipToView(True)
                self._raw_plots.append(raw_plot)
            else:
                self._raw_plots.append(None)

            # Filtered data plot (green)
            if self._show_filtered:
                pen = pg.mkPen(color="g", width=1, style=pg.QtCore.Qt.PenStyle.DashLine)
                filt_plot = graph_widget.plot(
                    depth_axis,
                    filtered_data[:, i] + vertical_offset,
                    pen=pen,
                    name=f"Filtered Ch{i}",
                )
                filt_plot.setClipToView(True)
                self._filtered_plots.append(filt_plot)
            else:
                self._filtered_plots.append(None)

            # Envelope plot (red)
            if self._show_envelope:
                pen = pg.mkPen(
                    color="r", width=2, style=pg.QtCore.Qt.PenStyle.SolidLine
                )
                env_plot = graph_widget.plot(
                    depth_axis,
                    envelope_data[:, i] + vertical_offset,
                    pen=pen,
                    name=f"Envelope Ch{i}",
                )
                env_plot.setClipToView(True)
                self._envelope_plots.append(env_plot)
            else:
                self._envelope_plots.append(None)

        # Add legend if multiple display modes are active
        if sum([self._show_raw, self._show_filtered, self._show_envelope]) > 1:
            plot_item.addLegend()

    def render(self) -> None:
        """Update the A-mode plots with all display modes."""
        if not self.has_new_data():
            return

        latest_samples = self._get_latest_scan_data()
        distance_axis = self._calculate_distance_axis()

        # Precompute filtered and envelope data if needed
        filtered_data = None
        envelope_data = None

        if self._show_filtered or self._show_envelope:
            filtered_data = self._filter_data(latest_samples)

        if self._show_envelope:
            envelope_data = self._get_envelope(filtered_data)

        for i in range(self.n_ch):
            vertical_offset = self.ch_spacing * (self.n_ch - i - 1)

            # Update raw data
            if self._raw_plots[i] is not None:
                self._raw_plots[i].setData(
                    distance_axis,
                    latest_samples[:, i] + vertical_offset,
                    skipFiniteCheck=True,
                )

            # Update filtered data
            if self._filtered_plots[i] is not None:
                self._filtered_plots[i].setData(
                    distance_axis,
                    filtered_data[:, i] + vertical_offset,
                    skipFiniteCheck=True,
                )

            # Update envelope
            if self._envelope_plots[i] is not None:
                self._envelope_plots[i].setData(
                    distance_axis,
                    envelope_data[:, i] + vertical_offset,
                    skipFiniteCheck=True,
                )

    def get_elapsed_time(self) -> float:
        """Calculate elapsed time based on scan count and measurement period."""
        if self._meas_period_us:
            return self._scan_count * self._meas_period_us / 1e6
        else:
            # Fallback to sample-based calculation
            return (self._scan_count * self._num_samples) / self.fs

    def _get_latest_scan_data(self) -> np.ndarray:
        """Extract the latest complete scan from the data queue."""
        if len(self._data_queue) < self._num_samples:
            # Not enough data, return zeros
            return np.zeros((self._num_samples, self.n_ch))

        return np.asarray(self._data_queue)[-self._num_samples :]

    def _calculate_distance_axis(self) -> np.ndarray:
        """Calculate distance axis for ultrasound display in millimeters."""
        # Calculate minimum depth based on ADC start delay
        min_depth = (self.SPEED_OF_SOUND * self._adc_start_delay) / 2  # in meters

        # Calculate maximum acquisition time
        max_time = self._num_samples / self._adc_sampling_freq  # in seconds

        # Calculate maximum depth
        max_depth = (self.SPEED_OF_SOUND * max_time) / 2 + min_depth  # in meters

        # Create linearly spaced depth array and convert to millimeters
        depths_m = np.linspace(min_depth, max_depth, self._num_samples)
        depths_mm = depths_m * 1e3  # Convert to millimeters

        return depths_mm

    def reinitialize(self, render_len_ms: int) -> None:
        """Re-initialize with new render length."""
        render_len_samples = self._num_samples
        new_queue = deque(maxlen=render_len_samples)

        # Pre-fill with zeros
        for _ in range(render_len_samples):
            new_queue.append(np.zeros(self.n_ch))

        # Copy existing data
        new_queue.extend(self._data_queue)
        self._data_queue = new_queue

        # Re-setup plot
        if self._graph_widget:
            self._raw_plots = []
            self._filtered_plots = []
            self._envelope_plots = []
            self.setup_plot(self._graph_widget)

    def get_data_queue(self) -> deque:
        """
        Get the data queue for mode switching.

        Returns
        -------
        deque
            The internal data queue.
        """
        return self._data_queue

    def _filter_data(self, data_in: np.ndarray) -> np.ndarray:
        """Apply bandpass filter to data using UltrasoundFilter."""
        return self._us_filter.filter_data(data_in)

    def _get_envelope(self, data_in: np.ndarray) -> np.ndarray:
        """Calculate envelope using UltrasoundFilter."""
        return UltrasoundFilter.get_envelope(data_in)
