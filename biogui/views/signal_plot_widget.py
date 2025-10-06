"""
Class implementing the real-time plot.


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
from PySide6.QtCore import QLocale, QTimer, Slot
from PySide6.QtWidgets import QWidget

from ..ui.signal_plot_widget_ui import Ui_SignalPlotWidget


class SignalPlotWidget(QWidget, Ui_SignalPlotWidget):
    """
    Widget showing the real-time plot of a signal.

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
        Optional keyword arguments for pre-filling, namely:
        - "xQueue": the queue for the X values;
        - "yQueue": the queue for the Y values.

    Attributes
    ----------
    _fs : float
        Sampling frequency.
    _nCh : int
        Number of channels.
    _chSpacing : float
        Spacing between each channel in the plot.
    _plotTimer : QTimer
        Timer for plot refreshing.
    _spsTimer : QTimer
        Timer for sampling rate refreshing.
    _timeTracker : int
        Tracker for the time passed.
    _spsTracker : int
        Tracker for the actual sampling rate.
    _plots : list of PlotItem
        List containing the references to the PlotItem objects.
    """

    # Constants
    SCAN_LENGTH = 400  # TODO: Get from interface config
    MMODE_TIME_WINDOW = 400  # Show more history
    PLOT_UPDATE_RATE = 50  # ms (20 FPS)
    SPS_UPDATE_RATE = 1000  # ms
    SPEED_OF_SOUND = 1540  # m/s in tissue

    def __init__(
        self,
        sigName: str,
        fs: float,
        nCh: int,
        chSpacing: float,
        renderLenMs: int,
        parent: QWidget | None = None,
        **kwargs: dict[str, float],
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self._fs = fs
        self._nCh = nCh
        self._chSpacing = chSpacing

        # read ultrasound mode if available
        self._ultrasoundMode = kwargs.get("ultrasoundMode", False)

        # Initialize mode-specific data structures
        self._initializeModeSpecificData()

        # Set up data queue
        renderLen = int(round(renderLenMs / 1000 * fs))
        self._dataQueue = self._createDataQueue(renderLen, kwargs)

        # Configure UI and timers
        self._setupTimers()
        self._setupGraphWidget(sigName, kwargs)
        self._renderPlots()

    def _initializeModeSpecificData(self) -> None:
        """Initialize data structures based on ultrasound mode."""
        self._plots = []
        self._lastRenderedScan = -1

        if self._ultrasoundMode == "M-Mode":
            self._mModeBuffer = np.zeros((self.SCAN_LENGTH, self.MMODE_TIME_WINDOW))

    def _createDataQueue(self, renderLen: int, kwargs: dict) -> deque:
        """Create and initialize the data queue."""
        dataQueue = deque(maxlen=renderLen)

        if "dataQueue" in kwargs:
            dataQueue.extend(kwargs["dataQueue"])
        else:
            # Fill with zeros
            for _ in range(renderLen):
                dataQueue.append(np.zeros(self._nCh))

        return dataQueue

    def _setupTimers(self) -> None:
        """Configure plot and sampling rate timers."""
        self._plotTimer = QTimer(self)
        self._plotTimer.setInterval(self.PLOT_UPDATE_RATE)
        self._plotTimer.timeout.connect(self._refreshPlot)

        self._spsTimer = QTimer(self)
        self._spsTimer.setInterval(self.SPS_UPDATE_RATE)
        self._spsTimer.timeout.connect(self._refreshSamplingRate)

        self._timeTracker = 0
        self._spsTracker = 0

    def _setupGraphWidget(self, sigName: str, kwargs: dict) -> None:
        """Configure the graph widget."""
        self.graphWidget.setTitle(sigName)
        self.graphWidget.getPlotItem().setMouseEnabled(False, False)
        self.graphWidget.getPlotItem().hideAxis("bottom")

        if "minRange" in kwargs and "maxRange" in kwargs:
            self.graphWidget.setYRange(kwargs["minRange"], kwargs["maxRange"])

    @property
    def dataQueue(self) -> deque:
        """deque: Property representing the queue with the values to plot."""
        return self._dataQueue

    def _renderPlots(self) -> None:
        """Render the initial plot."""
        self.graphWidget.clear()

        if self._ultrasoundMode == "A-Mode":
            self._setupAModeAxes()
            self._setupLinePlots()
        elif self._ultrasoundMode == "M-Mode":
            self._setupMModeAxes()
            self._setupImagePlot()
        else:
            # Time-Series (default)
            # self.graphWidget.getPlotItem().hideAxis("bottom")
            self._setupLinePlots()

    def _setupAModeAxes(self) -> None:
        """Configure axes for A-Mode display."""
        plot_item = self.graphWidget.getPlotItem()
        plot_item.showAxis("bottom")

        axis_item = plot_item.getAxis("bottom")
        axis_item.enableAutoSIPrefix(False)

        plot_item.setLabel("bottom", "Distance", "mm")

    def _setupMModeAxes(self) -> None:
        """Configure axes for M-Mode display."""
        plot_item = self.graphWidget.getPlotItem()
        plot_item.showAxis("bottom")
        plot_item.setLabel("bottom", "Time", "s")
        plot_item.setLabel("left", "Distance", "mm")

    def _setupLinePlots(self) -> None:
        """Setup line plots for A-Mode and Time-Series."""
        # Get colormap
        cm = pg.colormap.get("CET-C1")
        cm.setMappingMode("diverging")  # type: ignore
        lut = cm.getLookupTable(nPts=self._nCh, mode="qcolor")  # type: ignore

        # Plot placeholder data
        ys = np.asarray(self._dataQueue).T
        for i in range(self._nCh):
            pen = pg.mkPen(color=lut[i], width=1)  # type: ignore
            self._plots.append(
                self.graphWidget.plot(
                    ys[i] + self._chSpacing * (self._nCh - i - 1), pen=pen
                )
            )

    def _setupImagePlot(self) -> None:
        """Setup 2D image plot for M-Mode with enhanced quality."""
        self._imageItem = pg.ImageItem()
        self.graphWidget.addItem(self._imageItem)

        colormap = pg.colormap.get("viridis")
        self._imageItem.setColorMap(colormap)

        # self._imageItem.setLookupTable(None)
        self._imageItem.setImage(self._mModeBuffer.T, autoLevels=True)

        # Calculate scaling - but defer setRect to first data update
        # to avoid the TypeError
        self._needsRectSetup = True  # Flag for first update


    def _getLatestScanData(self) -> np.ndarray:
        """Extract the latest complete scan from the data queue."""
        return np.asarray(self._dataQueue)[-self.SCAN_LENGTH :]

    def _calculateDistanceAxis(self) -> np.ndarray:
        """Calculate distance axis for ultrasound display."""
        sample_distance_mm = (self.SPEED_OF_SOUND * 1000) / (2 * self._fs * 1000)
        return np.arange(self.SCAN_LENGTH) * sample_distance_mm

    @Slot(int)
    def reInitPlot(self, renderLenMs) -> None:
        """Re-initialize the plot when the render length changes."""

        # Fill new queue
        renderLen = int(round(renderLenMs / 1000 * self._fs))
        newDataQueue = deque(maxlen=renderLen)
        for _ in range(renderLen):
            newDataQueue.append(np.zeros(self._nCh))
        newDataQueue.extend(self._dataQueue)
        self._dataQueue = newDataQueue

        # Re-render plots
        self._plots = []
        self._renderPlots()

    def startTimers(self) -> None:
        """Start the timers for plot refresh."""
        self._timeTracker = 0
        self._spsTracker = 0

        self._plotTimer.start()
        self._spsTimer.start()

    def stopTimers(self) -> None:
        """Start the timers for plot refresh."""
        self._plotTimer.stop()
        self._spsTimer.stop()

    @Slot(np.ndarray)
    def addData(self, data: np.ndarray) -> None:
        """
        Add the given data to the internal queues.

        Parameters
        ----------
        data : ndarray
            Data to plot.
        """
        self._timeTracker += data.shape[0]
        self._spsTracker += data.shape[0]

        for samples in data:
            self._dataQueue.append(samples)

    def _refreshPlot(self) -> None:
        """Plot the given data."""
        if not self._dataQueue:
            return

        if self._ultrasoundMode == "A-Mode":
            self._refreshAModePlot()
        elif self._ultrasoundMode == "M-Mode":
            self._refreshMModePlot()
        else:
            self._refreshTimeSeriesPlot()

    def _refreshAModePlot(self) -> None:
        """Plot data as A-Mode."""
        latest_samples = self._getLatestScanData()
        distance_axis = self._calculateDistanceAxis()

        for i in range(self._nCh):
            a_mode_data = latest_samples[:, i]
            vertical_offset = self._chSpacing * (self._nCh - i - 1)

            self._plots[i].setData(
                distance_axis,
                a_mode_data + vertical_offset,
                skipFiniteCheck=True,
            )

        scan_count = self._timeTracker // self.SCAN_LENGTH
        self.timeLabel.setText(f"A-Mode Scan: {scan_count}")

    def _refreshMModePlot(self) -> None:
        """Plot data as M-Mode with enhanced quality."""
        # Extract latest A-line
        latest_samples = self._getLatestScanData()
        a_line_data = (
            latest_samples[:, 0] if self._nCh == 1 else np.mean(latest_samples, axis=1)
        )

        # Update M-Mode buffer (scroll left, add new data on right)
        self._mModeBuffer = np.roll(self._mModeBuffer, -1, axis=1)
        self._mModeBuffer[:, -1] = a_line_data

        # Setup rect on first update (when image has proper dimensions)
        if hasattr(self, "_needsRectSetup") and self._needsRectSetup:
            depth_mm = (
                (self.SPEED_OF_SOUND * 1000) / (2 * self._fs * 1000) * self.SCAN_LENGTH
            )
            time_s = self.MMODE_TIME_WINDOW * (self.SCAN_LENGTH / self._fs)
            self._imageItem.setRect(pg.QtCore.QRectF(0, 0, time_s, depth_mm))
            self._needsRectSetup = False

        # Update image with better contrast settings
        data_min, data_max = a_line_data.min(), a_line_data.max()
        level_range = data_max - data_min

        self._imageItem.setImage(
            self._mModeBuffer.T,
            autoLevels=False,
            levels=[data_min - 0.1 * level_range, data_max + 0.1 * level_range],
        )

        scan_count = self._timeTracker // self.SCAN_LENGTH
        self.timeLabel.setText(f"M-Mode: {scan_count} scans")

    def _refreshTimeSeriesPlot(self) -> None:
        """Plot data as time series."""
        ys = np.asarray(self._dataQueue).T
        for i in range(self._nCh):
            self._plots[i].setData(
                ys[i] + self._chSpacing * (self._nCh - i - 1),
                skipFiniteCheck=True,
            )

        self.timeLabel.setText(
            f"{QLocale().toString(self._timeTracker / self._fs, 'f', 2)} s"
        )

    def _refreshSamplingRate(self) -> None:
        """Refresh the sampling rate."""
        self.spsLabel.setText(f"{self._spsTracker} sps")
        self._spsTracker = 0
