# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Class implementing the real-time plot.


Copyright 2024 Mattia Orlandi, Pierangelo Maria Rapa
Copyright 2025 Enzo Baraldi (modifications)

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
from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QWidget

from ..ui.signal_plot_widget_ui import Ui_SignalPlotWidget
from .plot_modes import AModePlotMode, BasePlotMode, MModePlotMode, TimeSeriesPlotMode


class SignalPlotWidget(QWidget, Ui_SignalPlotWidget):
    """
    Widget showing the real-time plot of a signal.

    This widget delegates the actual plotting to mode-specific implementations
    (TimeSeriesPlotMode, AModePlotMode, MModePlotMode) to ensure clean separation
    of concerns and proper handling of different visualization types.

    Parameters
    ----------
    sigName : str
        Name of the signal to display.
    fs : float
        Sampling frequency.
    nCh : int
        Number of channels.
    chSpacing : float
        Spacing between each channel in the plot.
    renderLenMs : int
        Length of the window in the plot (in ms).
    parent : QWidget or None
        Parent widget.
    **kwargs : dict
        Optional keyword arguments, including:
        - signal_type: Dict with signal configuration
        - ultrasoundMode: "A-mode" or "M-mode" for ultrasound signals
        - dataQueue: Optional pre-existing data queue
        - minRange: Optional minimum Y range
        - maxRange: Optional maximum Y range

    Attributes
    ----------
    _plot_mode : BasePlotMode
        The current plot mode implementation.
    _plot_timer : QTimer
        Timer for plot refreshing.
    _sps_timer : QTimer
        Timer for sampling rate refreshing.
    """

    # Constants
    PLOT_UPDATE_RATE = 50  # ms (20 FPS)
    SPS_UPDATE_RATE = 1000  # ms

    def __init__(
        self,
        sigName: str,
        fs: float,
        nCh: int,
        chSpacing: float,
        renderLenMs: int,
        parent: QWidget | None = None,
        **kwargs: dict,
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        # WARNING: OpenGL seems to performs worse than software rendering for this application!
        # try:
        #     from PySide6.QtOpenGLWidgets import QOpenGLWidget

        #     gl_widget = QOpenGLWidget()
        #     self.graphWidget.setViewport(gl_widget)
        # except Exception:
        #     logging.error(
        #         "Failed to initialize OpenGL widget, falling back to software rendering"
        #     )
        #     pass  # Fallback to software rendering

        # Store parameters
        self._sig_name = sigName
        self._render_len_ms = renderLenMs
        self._signal_type = kwargs.get("signal_type", {})

        # Set appropriate label for sampling rate display
        if self._is_ultrasound():
            self.label1.setText("Pulse Repetition Frequency (PRF):")
        else:
            self.label1.setText("Sampling rate:")

        # Determine plot mode and create appropriate instance
        self._plot_mode = self._create_plot_mode(fs, nCh, chSpacing, renderLenMs, **kwargs)

        # Setup UI
        self._setup_graph_widget(sigName)

        # Setup plot
        self._plot_mode.setup_plot(self.graphWidget)

        # Setup timers
        self._setup_timers()

    def _create_plot_mode(
        self,
        fs: float,
        nCh: int,
        chSpacing: float,
        renderLenMs: int,
        **kwargs: dict,
    ) -> BasePlotMode:
        """
        Create the appropriate plot mode based on configuration.

        Parameters
        ----------
        fs : float
            Sampling frequency.
        nCh : int
            Number of channels.
        chSpacing : float
            Spacing between channels.
        renderLenMs : int
            Render window length in milliseconds.
        **kwargs : dict
            Additional configuration.

        Returns
        -------
        BasePlotMode
            The appropriate plot mode instance.
        """
        signal_type = kwargs.get("signal_type", {})

        # Check if this is an ultrasound signal
        if signal_type.get("type") == "ultrasound":
            ultrasound_mode = kwargs.get("ultrasoundMode", "A-Mode")

            if ultrasound_mode == "M-Mode":
                return MModePlotMode(fs, nCh, chSpacing, renderLenMs, **kwargs)
            elif ultrasound_mode == "A-Mode":
                return AModePlotMode(fs, nCh, chSpacing, renderLenMs, **kwargs)

        # Default: Time-Series mode
        return TimeSeriesPlotMode(fs, nCh, chSpacing, renderLenMs, **kwargs)

    def _setup_graph_widget(self, sig_name: str) -> None:
        """Configure the graph widget."""
        self.graphWidget.setTitle(sig_name)
        self.graphWidget.getPlotItem().setMouseEnabled(False, False)

    def _setup_timers(self) -> None:
        """Configure plot and sampling rate timers."""
        self._plot_timer = QTimer(self)
        self._plot_timer.setInterval(self.PLOT_UPDATE_RATE)
        self._plot_timer.timeout.connect(self._refresh_plot)

        self._sps_timer = QTimer(self)
        self._sps_timer.setInterval(self.SPS_UPDATE_RATE)
        self._sps_timer.timeout.connect(self._refresh_sampling_rate)

    def _is_ultrasound(self) -> bool:
        """
        Check if the current signal is an ultrasound signal.

        Returns
        -------
        bool
            True if ultrasound, False otherwise.
        """
        return self._signal_type.get("type") == "ultrasound"

    @property
    def dataQueue(self) -> deque:
        """
        Property representing the queue with the values to plot.

        This is used for backwards compatibility and mode switching.

        Returns
        -------
        deque
            The current data queue from the plot mode.
        """
        return self._plot_mode.get_data_queue()

    @property
    def bufferState(self) -> dict | None:
        """
        Property representing the buffer state for M-mode plots.
        This allows preserving M-mode buffer data when reconfiguring the plot.
        """
        if hasattr(self._plot_mode, "get_buffer_state"):
            return self._plot_mode.get_buffer_state()
        return None

    @Slot(int)
    def reInitPlot(self, renderLenMs: int) -> None:
        """
        Re-initialize the plot when the render length changes.

        Parameters
        ----------
        renderLenMs : int
            New render length in milliseconds.
        """
        self._render_len_ms = renderLenMs

        # Delegate to plot mode
        if hasattr(self._plot_mode, "reinitialize"):
            self._plot_mode.reinitialize(renderLenMs)

    def startTimers(self) -> None:
        """Start the timers for plot refresh."""
        self._plot_timer.start()
        self._sps_timer.start()

    def stopTimers(self) -> None:
        """Stop the timers for plot refresh."""
        self._plot_timer.stop()
        self._sps_timer.stop()

    @Slot(np.ndarray)
    def addData(self, data: np.ndarray) -> None:
        """
        Add the given data to the plot mode.

        Parameters
        ----------
        data : ndarray
            Data to plot (shape: [n_samples, n_channels]).
        """
        self._plot_mode.add_data(data)

    def _refresh_plot(self) -> None:
        """Refresh the plot if new data is available."""
        # skip rendering if plot is not displayed
        if not self.isVisible():
            return

        if self._plot_mode.has_new_data():
            self._plot_mode.render()

        # Update time label
        elapsed_time = self._plot_mode.get_elapsed_time()
        self.timeLabel.setText(f"{elapsed_time:.2f} s")

    def _refresh_sampling_rate(self) -> None:
        """Refresh the sampling rate display."""
        sample_count = self._plot_mode.sample_count

        if self._is_ultrasound():
            num_samples = self._signal_type.get("num_samples", 397)  # Default for wulpus

            if num_samples > 0:
                prf = sample_count / num_samples
                self.spsLabel.setText(f"{prf:.2f} Hz (PRF)")
            else:
                # Fallback if num_samples not available
                self.spsLabel.setText(f"{sample_count} sps")
        else:
            # For time-series signals: display SPS
            self.spsLabel.setText(f"{sample_count:.2f} sps")
