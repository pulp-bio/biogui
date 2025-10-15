from __future__ import annotations

from collections import deque

import numpy as np
import pyqtgraph as pg

from .base_plot_mode import BasePlotMode


class AModePlotMode(BasePlotMode):
    """
    Plot mode for A-Mode ultrasound visualization.

    Displays the latest complete scan as amplitude vs. depth.

    Parameters
    ----------
    fs : float
        Sampling frequency.
    nCh : int
        Number of channels.
    chSpacing : float
        Spacing between each channel in the plot.
    renderLenMs : int
        Length of the window in the plot (in ms).
    **config : dict
        Additional configuration options, including:
        - signal_type: Dict with ultrasound configuration
        - dataQueue: Optional pre-existing data queue
        - minRange: Optional minimum Y range
        - maxRange: Optional maximum Y range

    Attributes
    ----------
    _data_queue : deque
        Ring buffer for storing data.
    _plots : list
        List of PlotDataItem references.
    _num_samples : int
        Number of samples per scan.
    _adc_start_delay : float
        ADC start delay in seconds.
    _adc_sampling_freq : float
        ADC sampling frequency.
    _meas_period_us : float
        Measurement period in microseconds.
    _scan_count : int
        Number of complete scans processed.
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

        # Initialize data queue
        render_len_samples = self._num_samples
        self._data_queue = deque(maxlen=render_len_samples)

        # Pre-fill with existing data or zeros
        if "dataQueue" in config:
            self._data_queue.extend(config["dataQueue"])
        else:
            for _ in range(render_len_samples):
                self._data_queue.append(np.zeros(nCh))

        self._plots = []
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
        """Setup A-Mode plot with depth axis."""
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
        cm.setMappingMode("diverging")  # type: ignore
        lut = cm.getLookupTable(nPts=self.n_ch, mode="qcolor")  # type: ignore

        # Create placeholder plots
        depth_axis = self._calculate_distance_axis()
        latest_samples = self._get_latest_scan_data()

        for i in range(self.n_ch):
            pen = pg.mkPen(color=lut[i], width=1)  # type: ignore
            a_mode_data = latest_samples[:, i]
            vertical_offset = self.ch_spacing * (self.n_ch - i - 1)

            plot_item_obj = graph_widget.plot(
                depth_axis,
                a_mode_data + vertical_offset,
                pen=pen,
            )
            self._plots.append(plot_item_obj)

    def render(self) -> None:
        """Update the A-Mode plots."""
        if not self._plots or not self.has_new_data():
            return

        latest_samples = self._get_latest_scan_data()
        distance_axis = self._calculate_distance_axis()

        for i in range(self.n_ch):
            a_mode_data = latest_samples[:, i]
            vertical_offset = self.ch_spacing * (self.n_ch - i - 1)

            self._plots[i].setData(
                distance_axis,
                a_mode_data + vertical_offset,
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
        render_len_samples = int(round(render_len_ms / 1000 * self.fs))
        new_queue = deque(maxlen=render_len_samples)

        # Pre-fill with zeros
        for _ in range(render_len_samples):
            new_queue.append(np.zeros(self.n_ch))

        # Copy existing data
        new_queue.extend(self._data_queue)
        self._data_queue = new_queue

        # Re-setup plot
        if self._graph_widget:
            self._plots = []
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
