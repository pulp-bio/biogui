"""
M-Mode plot mode implementation.

Copyright 2024 Mattia Orlandi, Pierangelo Maria Rapa

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


class MModePlotMode(BasePlotMode):
    """
    Plot mode for M-Mode ultrasound visualization.

    Displays depth vs. time as a 2D image, where each column represents
    one A-line scan over time.

    Parameters
    ----------
    fs : float
        Sampling frequency.
    nCh : int
        Number of channels (must be 1 for M-Mode).
    chSpacing : float
        Spacing between each channel (not used in M-Mode).
    renderLenMs : int
        Not used in M-Mode (uses MMODE_TIME_WINDOW instead).
    **config : dict
        Additional configuration options, including:
        - signal_type: Dict with ultrasound configuration

    Attributes
    ----------
    _incoming_buffer : deque
        Buffer for accumulating incoming samples.
    _mmode_buffer : ndarray
        2D array for M-Mode display [depth x time].
    _pending_scans : int
        Number of complete scans waiting to be plotted.
    _current_scan_position : int
        Position within the current scan being accumulated.
    _image_item : ImageItem
        PyQtGraph ImageItem for displaying the M-Mode image.
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
    """

    MMODE_TIME_WINDOW = 400  # Number of A-lines to display
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

        if nCh != 1:
            raise ValueError("M-Mode only supports single channel data")

        # Extract ultrasound configuration
        signal_type = config.get("signal_type", {})
        self._num_samples = signal_type["num_samples"]
        self._adc_start_delay = signal_type["adc_start_delay"]
        self._adc_sampling_freq = signal_type["adc_sampling_freq"]
        self._meas_period_us = signal_type.get("meas_period")

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
        """Setup M-Mode 2D image plot."""
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

        # Create image item
        self._image_item = pg.ImageItem()
        graph_widget.addItem(self._image_item)

        # Set colormap
        colormap = pg.colormap.get("viridis")
        self._image_item.setColorMap(colormap)

        # Display initial empty buffer
        self._image_item.setImage(self._mmode_buffer.T, autoLevels=True)

        self._needs_rect_setup = True

    def render(self) -> None:
        """
        Render ONE complete scan to the M-Mode buffer.

        This ensures each scan is only plotted once, preventing duplication
        when the refresh rate is faster than the data acquisition rate.
        """
        if self._pending_scans == 0 or self._image_item is None:
            return

        # Check if we have enough data in buffer
        if len(self._incoming_buffer) < self._num_samples:
            # This shouldn't happen if pending_scans > 0, but safety check
            self._pending_scans = 0
            return

        # Extract exactly ONE complete scan
        scan_data = np.array(
            [self._incoming_buffer.popleft() for _ in range(self._num_samples)]
        )

        # Update M-Mode buffer (scroll left, add new data on right)
        self._mmode_buffer = np.roll(self._mmode_buffer, -1, axis=1)
        self._mmode_buffer[:, -1] = scan_data[:, 0]

        # Setup rect on first update
        if self._needs_rect_setup:
            self._setup_image_rect()
            self._needs_rect_setup = False

        # Update image with contrast settings
        data_min, data_max = scan_data.min(), scan_data.max()
        level_range = data_max - data_min if data_max != data_min else 1.0

        self._image_item.setImage(
            self._mmode_buffer.T,
            autoLevels=False,
            levels=[data_min - 0.1 * level_range, data_max + 0.1 * level_range],
        )

        # Decrement pending scans and increment scan count
        self._pending_scans -= 1
        self._scan_count += 1

    def get_elapsed_time(self) -> float:
        """Calculate elapsed time based on scan count and measurement period."""
        if self._meas_period_us:
            return self._scan_count * self._meas_period_us / 1e6
        else:
            # Fallback to sample-based calculation
            return (self._scan_count * self._num_samples) / self.fs

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
        time_s = self.MMODE_TIME_WINDOW * (self._num_samples / self._adc_sampling_freq)

        # Set rect: (x, y, width, height) = (0, min_depth, time, depth_range)
        self._image_item.setRect(
            pg.QtCore.QRectF(0, min_depth_mm, time_s, depth_range_mm)
        )

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
        """
        Re-initialize (not applicable for M-Mode).

        M-Mode uses a fixed time window (MMODE_TIME_WINDOW).
        """
        # M-Mode doesn't use render_len_ms, it has a fixed time window
        # We can reset the buffer if needed
        self._mmode_buffer = np.zeros((self._num_samples, self.MMODE_TIME_WINDOW))
        self._needs_rect_setup = True

        if self._graph_widget and self._image_item:
            self._image_item.setImage(self._mmode_buffer.T, autoLevels=True)

    def get_data_queue(self) -> deque:
        """
        Get a data queue representation for mode switching.

        For M-Mode, we return the incoming buffer as a queue.

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
