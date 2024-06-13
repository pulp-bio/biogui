# """Class for the real-time chart.


# Copyright 2024 Mattia Orlandi, Pierangelo Maria Rapa

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# """

from collections import deque

import numpy as np
from PySide6.QtCore import QObject, QTimer, Slot
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsScene, QWidget

from .ui.ui_signal_plots_widget import Ui_SignalPlotsWidget


class SignalPlotWidget(QWidget, Ui_SignalPlotsWidget):
    """Real-time chart of a signal.

    Parameters
    ----------
    sigName : str
        Name of the signal to display.
    nCh : int
        Number of channels.
    fs : float
        Sampling frequency.
    renderLengthS : int
        Length of the window in the chart (in s).
    chSpacing : int
        Spacing between each channel in the plot.

    Attributes
    ----------
    _dataQueue : deque
        Queue containing the data samples.
    _series : list of QLineSeries
        List of QLineSeries objects (one per channel).
    _nCh : int
        Number of channels.
    _fs : float
        Sampling frequency.
    _renderLength : int
        Length of the plot window.
    _chSpacing : int
        Spacing between each channel in the plot.
    """

    def __init__(
        self,
        sigName: str,
        nCh: int,
        fs: float,
        renderLengthS: int,
        chSpacing: int,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self.sigNameLabel.setText(sigName)

        self._nCh = nCh
        self._fs = fs
        self._renderLength = int(round(renderLengthS * fs))
        self._chSpacing = chSpacing
        self._dataQueue = deque(maxlen=self._renderLength)
        self._timer = QTimer(self)
        self._timer.setInterval(17)  # ~60 FPS
        self._timer.timeout.connect(self._refreshPlot)
        self._timer.start()

        # Create OpenGL-accelerated scene
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        self.view.setViewport(QOpenGLWidget())
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setBackgroundBrush(QColor("black"))

        self.pen = QPen(QColor("blue"))
        self.pen.setWidth(2)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._configScene()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._configScene()

    @Slot(np.ndarray)
    def addData(self, data: np.ndarray) -> None:
        """Plot the given data.

        Parameters
        ----------
        data : ndarray
            Data to plot.
        """
        for samples in data:
            self._dataQueue.append(samples)

    def _configScene(self) -> None:
        """Configure the scene (called the first time the plot is shown and everytime it is resized)."""
        self.scene.setSceneRect(
            0,
            -self.view.viewport().height(),
            self.view.viewport().width(),
            self.view.viewport().height(),
        )

    def _refreshPlot(self) -> None:
        """Refresh the scene."""
        if len(self._dataQueue) != 0:

            self.scene.clear()
            for i in range(1, len(self._dataQueue)):
                x1 = i - 1
                y1 = (
                    100 - self._dataQueue[i - 1][0] * 100
                )  # Scale y for better visibility
                x2 = i
                y2 = 100 - self._dataQueue[i][0] * 100  # Scale y for better visibility
                line = QGraphicsLineItem(x1, y1, x2, y2)
                line.setPen(self.pen)
                self.scene.addItem(line)
