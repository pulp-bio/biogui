# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Class for mmWave radar range-time visualization.
"""

from __future__ import annotations

from collections import deque

import numpy as np
import pyqtgraph as pg

from .base_plot_mode import BasePlotMode

# Speed of light in air, m/s
_SPEED_OF_LIGHT = 299_792_458.0


class RadarPlotMode(BasePlotMode):
    """
    Plot mode for FMCW radar range-time visualization.

    Radar samples arrive as one flat stream in frame order. Each frame holds
    ``num_chirps x num_samples x num_rx`` ADC samples, which this mode reduces
    to a single range profile per frame and displays as a scrolling 2D image of
    range versus time -- the radar counterpart of the ultrasound M-mode view.

    A frame is reduced the same way the reference acquisition software does it:
    the per-chirp DC offset is removed, a Hann window is applied along the
    samples of each chirp, a range FFT is taken, and the resulting complex
    spectra are averaged over the chirps of the frame. The displayed value is
    the magnitude of that average, optionally in dB.

    Parameters
    ----------
    fs : float
        Sampling frequency of the flattened sample stream, i.e.
        ``frame_rate * samples_per_frame``.
    nCh : int
        Number of channels (must be 1: a radar frame is a flat sample stream).
    chSpacing : float
        Spacing between each channel (not used).
    renderLenMs : int
        Not used (the mode shows a fixed number of frames, RADAR_TIME_WINDOW).
    **config : dict
        Additional configuration options. ``extras`` is expected to carry the
        frame geometry:

        - num_chirps: chirps per frame
        - num_samples: ADC samples per chirp
        - num_rx: number of RX antennas
        - frame_rate: frames per second
        - start_freq_hz, end_freq_hz: chirp band, used for the range axis
        - rx_index: which RX antenna to display (default 0)

        and optionally:

        - radarColormap: colormap label, see COLORMAPS
        - radarLogScale: display magnitudes in dB (default True)
        - radarDynamicRange: dB span shown below the peak (default 40)

    Attributes
    ----------
    _incoming_buffer : deque
        Buffer accumulating incoming samples until a frame is complete.
    _radar_buffer : ndarray
        2D array for the display, shape (n_range_bins, RADAR_TIME_WINDOW).
    _pending_frames : int
        Number of complete frames waiting to be rendered.
    _frame_position : int
        Position within the frame currently being accumulated.
    _frame_count : int
        Total number of frames processed.
    _image_item : ImageItem
        PyQtGraph ImageItem displaying the range-time image.
    """

    RADAR_TIME_WINDOW = 250  # Number of frames displayed
    COLORMAPS = {
        "Viridis": "viridis",
        "Inferno": "inferno",
        "Grayscale": "CET-L2",
    }
    DEFAULT_COLORMAP = "Viridis"
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
            raise ValueError(
                "Radar mode expects a single-channel stream of flattened frames"
            )

        extras = config.get("extras", {})
        self._num_chirps = int(extras.get("num_chirps", 32))
        self._num_samples = int(extras.get("num_samples", 8))
        self._num_rx = int(extras.get("num_rx", 1))
        self._rx_index = int(extras.get("rx_index", 0))
        self._frame_rate = float(extras.get("frame_rate", 0.0))
        self._start_freq_hz = float(extras.get("start_freq_hz", 58e9))
        self._end_freq_hz = float(extras.get("end_freq_hz", 63.5e9))
        # Bin the phase waveform is taken from, marked on the image so the
        # heatmap can be used to judge whether that choice is the right one.
        self._range_bin = int(extras.get("range_bin", -1))

        if not 0 <= self._rx_index < self._num_rx:
            raise ValueError(
                f"rx_index {self._rx_index} outside the {self._num_rx} available "
                "RX antennas"
            )

        self._samples_per_frame = self._num_chirps * self._num_samples * self._num_rx

        # rfft of num_samples real samples yields num_samples // 2 + 1 bins; bin 0
        # is the residual DC term and carries no range information.
        self._n_range_bins = self._num_samples // 2 + 1

        # Display configuration
        colormap_label = config.get("radarColormap", self.DEFAULT_COLORMAP)
        self._colormap = self.COLORMAPS.get(
            colormap_label, self.COLORMAPS[self.DEFAULT_COLORMAP]
        )
        self._log_scale = bool(config.get("radarLogScale", True))
        self._dynamic_range = float(
            config.get("radarDynamicRange", self.DEFAULT_DYNAMIC_RANGE_DB)
        )

        # Data structures
        self._incoming_buffer: deque = deque()
        self._radar_buffer = np.zeros((self._n_range_bins, self.RADAR_TIME_WINDOW))
        self._pending_frames = 0
        self._frame_position = 0
        self._frame_count = 0

        self._window = np.hanning(self._num_samples)

        # Plot items
        self._image_item = None
        self._needs_rect_setup = True
        self._graph_widget = None

    def add_data(self, data: np.ndarray) -> None:
        """
        Buffer incoming samples and count complete frames.

        Parameters
        ----------
        data : ndarray
            Samples of shape (nSamp, 1), in frame order.
        """
        flat = np.asarray(data, dtype=np.float64).reshape(-1)

        self._incoming_buffer.extend(flat)
        self._frame_position += flat.size

        while self._frame_position >= self._samples_per_frame:
            self._pending_frames += 1
            self._frame_position -= self._samples_per_frame

        self._sample_count += data.shape[0]

    def has_new_data(self) -> bool:
        """Check if there are complete frames waiting to be rendered."""
        return self._pending_frames > 0

    def setup_plot(self, graph_widget) -> None:
        """Setup the range-time 2D image plot."""
        self._graph_widget = graph_widget
        graph_widget.clear()

        plot_item = graph_widget.getPlotItem()
        plot_item.showAxis("bottom")
        plot_item.showAxis("left")

        plot_item.getAxis("bottom").enableAutoSIPrefix(False)
        plot_item.getAxis("left").enableAutoSIPrefix(False)

        plot_item.setLabel("bottom", "Time", units="s")
        plot_item.setLabel("left", "Range", units="mm")

        self._image_item = pg.ImageItem()
        self._image_item.setAutoDownsample(True)
        graph_widget.addItem(self._image_item)

        self._image_item.setColorMap(pg.colormap.get(self._colormap))

        # Mark the bin the phase waveform comes from, so this plot answers
        # "is the selected bin where the energy actually is?".
        if 0 <= self._range_bin < self._n_range_bins:
            ranges_mm = self._calculate_range_axis()
            marker = pg.InfiniteLine(
                pos=float(ranges_mm[self._range_bin]),
                angle=0,
                movable=False,
                pen=pg.mkPen("r", width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
                label=f"phase bin {self._range_bin}",
                labelOpts={"position": 0.05, "color": "r"},
            )
            graph_widget.addItem(marker)

        self._update_image()
        self._needs_rect_setup = True

    def render(self) -> None:
        """Reduce every pending frame to a range profile and scroll it in."""
        if not self.has_new_data() or self._image_item is None:
            return

        frames_to_process = self._pending_frames

        profiles = np.empty((self._n_range_bins, frames_to_process))
        for idx in range(frames_to_process):
            frame = np.fromiter(
                (self._incoming_buffer.popleft() for _ in range(self._samples_per_frame)),
                dtype=np.float64,
                count=self._samples_per_frame,
            )
            profiles[:, idx] = self._range_profile(frame)

        # The buffer holds linear magnitudes. Conversion to dB happens at display
        # time against the whole displayed window, not against this batch: a
        # per-batch reference would rescale the colormap on every render, since
        # the number of frames per render varies with arrival timing.
        self._radar_buffer = np.roll(self._radar_buffer, -frames_to_process, axis=1)
        self._radar_buffer[:, -frames_to_process:] = profiles

        if self._needs_rect_setup:
            self._setup_image_rect()
            self._needs_rect_setup = False

        self._update_image()

        self._pending_frames -= frames_to_process
        self._frame_count += frames_to_process

    def get_elapsed_time(self) -> float:
        """Elapsed time derived from the number of frames rendered."""
        return self._frame_count * self._get_frame_period_s()

    def reinitialize(self, render_len_ms: int) -> None:
        """
        Reset the display buffer.

        The mode shows a fixed number of frames, so ``render_len_ms`` is unused.
        """
        self._radar_buffer = np.zeros((self._n_range_bins, self.RADAR_TIME_WINDOW))
        self._needs_rect_setup = True

        if self._graph_widget and self._image_item:
            self._update_image()

    def get_data_queue(self) -> deque:
        """Return the buffered samples as a queue, for mode switching."""
        return deque(self._incoming_buffer)

    def _range_profile(self, frame: np.ndarray) -> np.ndarray:
        """
        Reduce one radar frame to a magnitude range profile.

        Parameters
        ----------
        frame : ndarray
            Flat frame of ``num_chirps * num_samples * num_rx`` samples.

        Returns
        -------
        ndarray
            Magnitude per range bin, shape (n_range_bins,).
        """
        # Frame layout matches the firmware's FIFO order: chirp-major, then
        # samples, then RX antenna.
        cube = frame.reshape(self._num_chirps, self._num_samples, self._num_rx)
        chirps = cube[:, :, self._rx_index]

        # Remove the per-chirp DC offset, which otherwise dominates bin 0 and
        # leaks into the neighbouring range bins.
        chirps = chirps - chirps.mean(axis=1, keepdims=True)

        spectra = np.fft.rfft(chirps * self._window, axis=1)

        # Averaging the complex spectra (rather than the magnitudes) suppresses
        # noise that is incoherent between chirps, which is what makes the small
        # chest-wall displacement visible.
        return np.abs(spectra.mean(axis=0))

    def _update_image(self) -> None:
        """
        Push the buffer to the image, converting to dB if enabled.

        The dB reference is the strongest bin anywhere in the displayed window, so
        the colormap span is stable while the window scrolls and levels stay
        comparable between renders. Values are floored at the configured dynamic
        range and the levels are pinned, so the same colour always means the same
        level relative to the window peak.
        """
        if self._image_item is None:
            return

        if not self._log_scale:
            self._image_item.setImage(self._radar_buffer.T, autoLevels=True)
            return

        peak = max(float(self._radar_buffer.max()), np.finfo(np.float64).tiny)
        db = 20.0 * np.log10(
            np.maximum(self._radar_buffer, peak * 1e-12) / peak
        )
        np.maximum(db, -self._dynamic_range, out=db)

        self._image_item.setImage(
            db.T, autoLevels=False, levels=(-self._dynamic_range, 0.0)
        )

    def _setup_image_rect(self) -> None:
        """Scale the image to the range and time axes."""
        if self._image_item is None:
            return

        ranges_mm = self._calculate_range_axis()
        time_s = self.RADAR_TIME_WINDOW * self._get_frame_period_s()

        self._image_item.setRect(
            pg.QtCore.QRectF(0, ranges_mm[0], time_s, ranges_mm[-1] - ranges_mm[0])
        )

    def _calculate_range_axis(self) -> np.ndarray:
        """
        Nominal range of each FFT bin, in millimetres.

        For an FMCW chirp the bin spacing is the range resolution
        ``c / (2 * B)``, with ``B`` the swept bandwidth.
        """
        bandwidth_hz = abs(self._end_freq_hz - self._start_freq_hz)
        if bandwidth_hz <= 0:
            return np.arange(self._n_range_bins, dtype=np.float64)

        bin_spacing_mm = _SPEED_OF_LIGHT / (2.0 * bandwidth_hz) * 1e3
        return np.arange(self._n_range_bins) * bin_spacing_mm

    def _get_frame_period_s(self) -> float:
        """Time between two displayed frames."""
        if self._frame_rate > 0:
            return 1.0 / self._frame_rate
        if self.fs > 0:
            return self._samples_per_frame / self.fs
        return 0.0
