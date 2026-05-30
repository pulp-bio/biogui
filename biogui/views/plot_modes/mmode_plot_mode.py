# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Class for M-mode ultrasound visualization.
"""

from __future__ import annotations

from collections import deque

import numpy as np
import pyqtgraph as pg

from .base_plot_mode import BasePlotMode
from .ultrasound_filters import UltrasoundFilter


class MModePlotMode(BasePlotMode):
    """
    Plot mode for M-mode ultrasound visualization.

    Displays depth vs. time as a 2D image, where each column represents
    one A-line scan over time.

    Parameters
    ----------
    fs : float
        Sampling frequency.
    nCh : int
        Number of channels (must be 1 for M-mode).
    chSpacing : float
        Spacing between each channel (not used in M-mode).
    renderLenMs : int
        Not used in M-mode (uses MMODE_TIME_WINDOW instead).
    **config : dict
        Additional configuration options, including:
        - extras: Dict with ultrasound configuration
        - showRaw: Show raw RF data (only one can be True for M-mode)
        - showFiltered: Show filtered data
        - showEnvelope: Show envelope
        - mmodeColormap: M-mode colormap label ("Grayscale" or "Viridis")
        - mmodeLogCompression: Apply log compression before display
        - mmodeDynamicRange: Dynamic range in dB for log compression
        - enableBandpass: Enable bandpass filter
        - bandpassLow: Low cutoff frequency in Hz
        - bandpassHigh: High cutoff frequency in Hz

    Attributes
    ----------
    _incoming_buffer : deque
        Buffer for accumulating incoming samples.
    _mmode_buffer : ndarray
        2D array for M-mode display [depth x time].
    _pending_scans : int
        Number of complete scans waiting to be plotted.
    _current_scan_position : int
        Position within the current scan being accumulated.
    _image_item : ImageItem
        PyQtGraph ImageItem for displaying the M-mode image.
    _num_samples : int
        Number of samples per scan.
    _adc_start_delay : float
        ADC start delay in seconds.
    _adc_sampling_freq : float
        ADC sampling frequency.
    _meas_period_us : float
        Measurement period in microseconds.
    _scan_count : int
        Total number of scans processed.
    _display_mode : str
        Display mode: "raw", "filtered", or "envelope".
    _us_filter : UltrasoundFilter
        Ultrasound filter instance.
    """

    MMODE_TIME_WINDOW = 250  # Number of A-lines to display
    SPEED_OF_SOUND = 1540  # m/s in tissue
    COLORMAPS = {
        "Grayscale": "CET-L2",
        "Viridis": "viridis",
    }
    DEFAULT_COLORMAP = "Grayscale"
    DEFAULT_DYNAMIC_RANGE_DB = 40.0

    def __init__(
        self,
        fs: float,
        nCh: int,
        chSpacing: float,
        renderLenMs: int,
        **config: dict,
    ) -> None:
        super().__init__(fs, nCh, chSpacing, **config)

        if nCh != 1:
            raise ValueError("M-Mode only supports single channel data")

        # Extract ultrasound configuration
        extras = config.get("extras", {})
        self._num_samples = extras["num_samples"]
        self._adc_start_delay = extras["adc_start_delay"]
        self._adc_sampling_freq = extras["adc_sampling_freq"]
        self._meas_period_us = extras.get("meas_period")

        # Initialize data structures
        self._incoming_buffer = deque()
        self._mmode_buffer = np.zeros((self._num_samples, self.MMODE_TIME_WINDOW))
        self._pending_scans = 0
        self._current_scan_position = 0  # Track position within current scan
        self._scan_count = 0

        # Plot items
        self._image_item = None
        self._needs_rect_setup = True
        self._graph_widget = None

        # M-Mode display configuration (only one mode at a time)
        self._show_raw = config.get("showRaw", True)
        self._show_filtered = config.get("showFiltered", False)
        self._show_envelope = config.get("showEnvelope", False)
        colormap_label = config.get("mmodeColormap", self.DEFAULT_COLORMAP)
        self._colormap = self.COLORMAPS.get(colormap_label, self.COLORMAPS[self.DEFAULT_COLORMAP])
        self._log_compression = config.get("mmodeLogCompression", False)
        self._dynamic_range = float(config.get("mmodeDynamicRange", self.DEFAULT_DYNAMIC_RANGE_DB))

        # Determine which mode to display (only one should be True for M-mode)
        if self._show_envelope:
            self._display_mode = "envelope"
        elif self._show_filtered:
            self._display_mode = "filtered"
        else:
            self._display_mode = "raw"

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

    def add_data(self, data: np.ndarray) -> None:
        """
        Add data to the buffer and track complete scans.

        This method ensures that each complete scan is only counted once
        by tracking the position within the current scan.
        """
        # Add samples to buffer one by one and track scan completion
        for sample in data:
            self._incoming_buffer.append(sample)
            self._current_scan_position += 1

            # Check if we completed a scan
            if self._current_scan_position >= self._num_samples:
                self._pending_scans += 1
                self._current_scan_position = 0

        self._sample_count += data.shape[0]

    def has_new_data(self) -> bool:
        """Check if there are complete scans waiting to be rendered."""
        return self._pending_scans > 0

    def setup_plot(self, graph_widget) -> None:
        """Setup M-mode 2D image plot."""
        self._graph_widget = graph_widget
        graph_widget.clear()

        plot_item = graph_widget.getPlotItem()
        plot_item.showAxis("bottom")
        plot_item.showAxis("left")

        # Disable auto SI prefix
        bottom_axis = plot_item.getAxis("bottom")
        bottom_axis.enableAutoSIPrefix(False)

        left_axis = plot_item.getAxis("left")
        left_axis.enableAutoSIPrefix(False)

        plot_item.setLabel("bottom", "Time", units="s")
        plot_item.setLabel("left", "Depth", units="mm")

        # Clinical convention
        plot_item.invertY(True)

        # Create image item
        self._image_item = pg.ImageItem()
        # Optimization: automatic downsampling for image
        self._image_item.setAutoDownsample(True)
        graph_widget.addItem(self._image_item)

        colormap = pg.colormap.get(self._colormap)
        self._image_item.setColorMap(colormap)

        # Display initial empty buffer
        self._update_image()

        self._needs_rect_setup = True

    def _update_image(self) -> None:
        if self._image_item is None:
            return
        if self._log_compression:
            self._image_item.setImage(self._mmode_buffer.T, autoLevels=False, levels=(0, 255))
        else:
            self._image_item.setImage(self._mmode_buffer.T, autoLevels=True)

    def render(self) -> None:
        """
        Render all pending scans to the M-mode buffer.

        This ensures we stay up-to-date even when data arrives faster
        than the display refresh rate.
        """
        if not self.has_new_data() or self._image_item is None:
            return

        scans_to_process = self._pending_scans

        # Extract all pending scans from the incoming buffer
        all_scans = []
        for _ in range(scans_to_process):
            # Extract one complete scan (num_samples samples)
            single_scan = []
            for _ in range(self._num_samples):
                single_scan.append(self._incoming_buffer.popleft())
            all_scans.append(single_scan)

        # Convert to numpy array: shape (scans_to_process, num_samples, 1)
        all_scans = np.array(all_scans)

        # Process scans based on display mode (filtered/envelope/raw)
        processed_scans = []
        for i in range(scans_to_process):
            scan = all_scans[i, :, :]  # Shape: (num_samples, 1)
            processed = self._process_scan_data(scan)
            processed_scans.append(processed[:, 0])  # Remove channel dimension

        processed_scans = np.array(processed_scans).T  # Shape: (num_samples, scans_to_process)
        if self._log_compression:
            compressed = np.zeros_like(processed_scans, dtype=np.float64)
            for col_idx in range(processed_scans.shape[1]):
                compressed[:, col_idx] = UltrasoundFilter.apply_log_compression(
                    processed_scans[:, col_idx],
                    self._dynamic_range,
                )
            processed_scans = compressed

        # Scroll the M-mode buffer to the left by scans_to_process columns
        self._mmode_buffer = np.roll(self._mmode_buffer, -scans_to_process, axis=1)

        # Add all new processed scans at the right side of the buffer
        self._mmode_buffer[:, -scans_to_process:] = processed_scans

        # Setup image rect on first update
        if self._needs_rect_setup:
            self._setup_image_rect()
            self._needs_rect_setup = False

        self._update_image()

        # Update counters
        self._pending_scans -= scans_to_process
        self._scan_count += scans_to_process

    def get_elapsed_time(self) -> float:
        """Calculate elapsed time based on scan count and measurement period."""
        return self._scan_count * self._get_scan_period_s()

    def _setup_image_rect(self) -> None:
        """Setup the image rectangle with proper depth and time scaling."""
        if self._image_item is None:
            return

        # Calculate depth range
        depths_mm = self._calculate_distance_axis()
        min_depth_mm = depths_mm[0]
        max_depth_mm = depths_mm[-1]
        depth_range_mm = max_depth_mm - min_depth_mm

        # Calculate time window
        time_s = self.MMODE_TIME_WINDOW * self._get_scan_period_s()

        # Set rect: (x, y, width, height) = (0, min_depth, time, depth_range)
        self._image_item.setRect(pg.QtCore.QRectF(0, min_depth_mm, time_s, depth_range_mm))

    def _calculate_distance_axis(self) -> np.ndarray:
        """Calculate distance axis for ultrasound display in millimeters."""
        sample_times_s = self._adc_start_delay + (
            np.arange(self._num_samples) / self._adc_sampling_freq
        )
        return (self.SPEED_OF_SOUND * sample_times_s / 2) * 1e3

    def _get_scan_period_s(self) -> float:
        """Return the effective time between two displayed A-lines."""
        if self.fs > 0:
            return self._num_samples / self.fs
        if self._meas_period_us:
            return self._meas_period_us / 1e6
        return 0.0

    def _process_scan_data(self, scan_data: np.ndarray) -> np.ndarray:
        """
        Process scan data based on display mode.

        Parameters
        ----------
        scan_data : ndarray
            Raw scan data (shape: [num_samples, 1])

        Returns
        -------
        ndarray
            Processed scan data based on display mode.
        """
        if self._display_mode == "raw":
            return scan_data
        elif self._display_mode == "filtered":
            return self._us_filter.filter_data(scan_data)
        elif self._display_mode == "envelope":
            filtered = self._us_filter.filter_data(scan_data)
            envelope = UltrasoundFilter.get_envelope(filtered)

            envelope = np.sqrt(envelope)

            return envelope

        else:
            return scan_data

    def reinitialize(self, render_len_ms: int) -> None:
        """
        Re-initialize (not applicable for M-mode).

        M-mode uses a fixed time window (MMODE_TIME_WINDOW).
        """
        # M-mode doesn't use render_len_ms, it has a fixed time window
        # We can reset the buffer if needed
        self._mmode_buffer = np.zeros((self._num_samples, self.MMODE_TIME_WINDOW))
        self._needs_rect_setup = True

        if self._graph_widget and self._image_item:
            self._update_image()

    def get_data_queue(self) -> deque:
        """
        Get a data queue representation for mode switching.

        For M-mode, we return the incoming buffer as a queue.

        Returns
        -------
        deque
            Queue containing the buffered data.
        """
        # Convert buffer to proper format (list of arrays)
        queue = deque()
        for sample in self._incoming_buffer:
            queue.append(sample)
        return queue
