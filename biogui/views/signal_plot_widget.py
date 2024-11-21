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

from ..ui.signal_plots_widget_ui import Ui_SignalPlotsWidget


class SignalPlotWidget(QWidget, Ui_SignalPlotsWidget):
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
    chSpacing : int
        Spacing between each channel in the plot.
    renderLengthS : int
        Length of the window in the plot (in s).
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
    _chSpacing : int
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

    def __init__(
        self,
        sigName: str,
        fs: float,
        nCh: int,
        chSpacing: int,
        renderLengthS: int,
        parent: QWidget | None = None,
        **kwargs: dict,
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self._fs = fs
        self._nCh = nCh
        self._chSpacing = chSpacing

        # Set up queue
        renderLength = int(round(renderLengthS * fs))
        self._dataQueue = deque(maxlen=renderLength)

        # Fill queue
        if "dataQueue" in kwargs:
            self._dataQueue.extend(kwargs["dataQueue"])
        else:
            for _ in range(renderLength):  # type: ignore
                self._dataQueue.append(np.zeros(self._nCh))

        # Configure timers
        self._plotTimer = QTimer(self)
        self._plotTimer.setInterval(50)  # 20 FPS
        self._plotTimer.timeout.connect(self._refreshPlot)
        self._spsTimer = QTimer(self)
        self._spsTimer.setInterval(1000)
        self._spsTimer.timeout.connect(self._refreshSamplingRate)
        self._timeTracker = 0
        self._spsTracker = 0

        # Initialize plots
        self._plots = []
        self._initializePlots(sigName)

    @property
    def dataQueue(self) -> deque:
        """deque: Property representing the queue with the values to plot."""
        return self._dataQueue

    def _initializePlots(self, sigName: str) -> None:
        """Render the initial plot."""
        # Reset graph
        self.graphWidget.clear()
        self.graphWidget.setTitle(sigName)
        self.graphWidget.getPlotItem().hideAxis("left")  # type: ignore
        self.graphWidget.getPlotItem().hideAxis("bottom")  # type: ignore
        self.graphWidget.getPlotItem().setMouseEnabled(False, False)  # type: ignore
        if sigName == "force":
            self.graphWidget.setYRange(0, 2.5)

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
                    ys[i] + self._chSpacing * (self._nCh - i), pen=pen
                )
            )

    def startTimers(self) -> None:
        """Start the timers for plot refresh."""
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
        if self._dataQueue:
            ys = np.asarray(self._dataQueue).T
            for i in range(self._nCh):
                self._plots[i].setData(
                    ys[i] + self._chSpacing * (self._nCh - i),
                    skipFiniteCheck=True,
                )

            self.timeLabel.setText(f"{QLocale().toString(self._timeTracker / self._fs, 'f', 2)} s")  # type: ignore

    def _refreshSamplingRate(self) -> None:
        """Refresh the sampling rate."""
        self.spsLabel.setText(f"{self._spsTracker} sps")
        self._spsTracker = 0
