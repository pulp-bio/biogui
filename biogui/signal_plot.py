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

from collections import deque

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QWidget

from .ui.ui_signal_plots_widget import Ui_SignalPlotsWidget


class SignalPlotWidget(QWidget, Ui_SignalPlotsWidget):
    """
    Widget showing the real-time plot of a signal.

    Parameters
    ----------
    sigName : str
        Name of the signal to display.
    nCh : int
        Number of channels.
    fs : float
        Sampling frequency.
    renderLengthS : int
        Length of the window in the plot (in s).
    chSpacing : int
        Spacing between each channel in the plot.
    parent : QWidget or None
        Parent widget.

    Attributes
    ----------
    _nCh : int
        Number of channels.
    _fs : float
        Sampling frequency.
    _chSpacing : int
        Spacing between each channel in the plot.
    _xQueue : deque
        Queue for X values.
    _yQueue : deque
        Queue for Y values.
    _timer : QTimer
        Timer for plot refreshing.
    _plots : list of PlotItem
        List containing the references to the PlotItem objects.
    """

    def __init__(
        self,
        sigName: str,
        nCh: int,
        fs: float,
        renderLengthS: int,
        chSpacing: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        renderLength = int(round(renderLengthS * fs))
        self._xQueue = deque(maxlen=renderLength)
        self._yQueue = deque(maxlen=renderLength)
        self._nCh = nCh
        self._fs = fs
        self._chSpacing = chSpacing
        self._timer = QTimer(self)
        self._timer.setInterval(20)  # 50 FPS
        self._timer.timeout.connect(self._refreshPlot)
        self._timer.start()

        # Initialize plots
        self._plots = []
        self._initializePlots(sigName)

    def _initializePlots(self, sigName: str) -> None:
        """Render the initial plot."""
        # Reset graph
        self.graphWidget.clear()
        self.graphWidget.setTitle(sigName)
        self.graphWidget.setLabel("bottom", "Time (s)")
        self.graphWidget.getPlotItem().hideAxis("left")  # type: ignore
        self.graphWidget.getPlotItem().setMouseEnabled(False, False)

        # Initialize queues
        for i in range(-self._xQueue.maxlen, 0):  # type: ignore
            self._xQueue.append(i / self._fs)
            self._yQueue.append(np.zeros(self._nCh))

        # Get colormap
        cm = pg.colormap.get("CET-C1")  # type: ignore
        cm.setMappingMode("diverging")  # type: ignore
        lut = cm.getLookupTable(nPts=self._nCh, mode="qcolor")  # type: ignore

        # Plot placeholder data
        ys = np.asarray(self._yQueue).T
        for i in range(self._nCh):
            pen = pg.mkPen(color=lut[i], width=1)
            self._plots.append(
                self.graphWidget.plot(
                    self._xQueue, ys[i] + self._chSpacing * i, pen=pen
                )
            )

    @Slot(np.ndarray)
    def addData(self, data: np.ndarray) -> None:
        """
        Add the given data to the internal queues.

        Parameters
        ----------
        data : ndarray
            Data to plot.
        """
        for samples in data:
            self._xQueue.append(self._xQueue[-1] + 1 / self._fs)
            self._yQueue.append(samples)

    def _refreshPlot(self) -> None:
        """Plot the given data."""

        ys = np.asarray(self._yQueue).T
        for i in range(self._nCh):
            self._plots[i].setData(
                self._xQueue,
                ys[i] + self._chSpacing * (self._nCh - i),
                skipFiniteCheck=True,
            )
