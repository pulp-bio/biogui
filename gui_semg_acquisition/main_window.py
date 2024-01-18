"""This module contains the main window of the app.


Copyright 2023 Mattia Orlandi, Pierangelo Maria Rapa

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

import logging
from collections import deque

import numpy as np
import pyqtgraph as pg
import serial.tools.list_ports
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QMessageBox, QWidget

from ._streaming import StreamingController
from ._ui.ui_main_window import Ui_MainWindow


def serialPorts():
    """Lists serial port names

    Returns
    -------
    list of str
        A list of the serial ports available on the system.
    """
    return [info[0] for info in serial.tools.list_ports.comports()]


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window showing the real-time plot.

    Parameters
    ----------
    sampFreq : int
        Sampling frequency.
    renderLength : int
        Memory of the internal queues.

    Attributes
    ----------
    _streamController : StreamingController or None
        StreamingController instance.
    _sampFreq : int
        Sampling frequency.
    _xQueue : deque
        Queue for X values.
    _yQueue : deque
        Queue for Y values.
    _bufferCount : int
        Counter for the plot buffer.
    _bufferSize : int
        Size of the buffer for plotting samples.
    _plotSpacing : int
        Spacing between each channel in the plot.
    _serialPort : str
        Serial port.
    _plots : list of PlotItems
        List containing a PlotItem for each channel.

    Class attributes
    ----------------
    startStreamingSig : Signal
        Qt signal emitted when streaming starts.
    stopStreamingSig : Signal
        Qt signal emitted when streaming stops.
    closeSig : Signal
        Qt signal emitted when the application is closed.
    dataReadySig : Signal
        Qt signal emitted when new data is available.
    dataReadyFltSig : Signal
        Qt signal emitted when new filtered data is available.
    """

    startStreamingSig = Signal()
    stopStreamingSig = Signal()
    closeSig = Signal()
    dataReadySig = Signal(np.ndarray)
    dataReadyFltSig = Signal(np.ndarray)

    def __init__(
        self, sampFreq: int, renderLength: int
    ) -> None:
        super().__init__()

        self._streamController: StreamingController | None = None
        self._sampFreq = sampFreq
        self._xQueue = deque(maxlen=renderLength)
        self._yQueue = deque(maxlen=renderLength)
        self._bufferCount = 0
        self._bufferSize = 200
        self._plotSpacing = 1000

        self.setupUi(self)

        # Serial port and number of channels
        self._rescanSerialPorts()
        self._serialPort = self.serialPortsComboBox.currentText()
        self.serialPortsComboBox.currentTextChanged.connect(self._serialPortChange)
        self.rescanSerialPortsButton.clicked.connect(self._rescanSerialPorts)

        # Plot
        self._plots = []
        self._initializePlot()

        # Streaming
        self.startStreamingButton.setEnabled(self._serialPort != "")
        self.stopStreamingButton.setEnabled(False)
        self.startStreamingButton.clicked.connect(self._startStreaming)
        self.stopStreamingButton.clicked.connect(self._stopStreaming)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._streamController is not None:
            self._streamController.stopStreaming()
        self.closeSig.emit()
        event.accept()

    def addWidget(self, widget: QWidget) -> None:
        """Add widget to the GUI.

        Parameters
        ----------
        widget : QWidget
            Widget to add.
        """
        self.moduleContainer.layout().addWidget(widget)

    def _initializePlot(self) -> None:
        """Render the initial plot."""
        # Reset graph
        self.PPG_SX.clear()
        self.PPG_DX.clear()
        self.EDA_SX.clear()
        self.EDA_DX.clear()
        self.FORCE_SX.clear()
        self.FORCE_DX.clear()
        self.PPG_SX.setTitle("PPG LEFT", color="b", size="10pt")
        self.PPG_DX.setTitle("PPG RIGHT", color="b", size="10pt")
        self.EDA_SX.setTitle("EDA LEFT", color="b", size="10pt")
        self.EDA_DX.setTitle("EDA RIGHT", color="b", size="10pt")
        self.FORCE_SX.setTitle("FORCE LEFT", color="b", size="10pt")
        self.FORCE_DX.setTitle("FORCE RIGHT", color="b", size="10pt")
        #self.PPG_SX.getPlotItem().hideAxis("bottom")
        #self.PPG_SX.getPlotItem().hideAxis("left")
        # Initialize queues
        for i in range(-self._xQueue.maxlen, 0):
            self._xQueue.append(i / self._sampFreq)
            self._yQueue.append(np.zeros(6))
        # Plot placeholder data
        ys = np.asarray(self._yQueue).T
        
        self._plots.append(
            self.PPG_SX.plot(self._xQueue, ys[1])
        )
        self._plots.append(
            self.PPG_DX.plot(self._xQueue, ys[0])
        )
        self._plots.append(
            self.EDA_SX.plot(self._xQueue, ys[3])
        )
        self._plots.append(
            self.EDA_DX.plot(self._xQueue, ys[2])
        )
        self._plots.append(
            self.FORCE_SX.plot(self._xQueue, ys[4])
        )
        self._plots.append(
            self.FORCE_DX.plot(self._xQueue, ys[5])
        )

    def _rescanSerialPorts(self) -> None:
        """Rescan the serial ports to update the combo box."""
        self.serialPortsComboBox.clear()
        self.serialPortsComboBox.addItems(serialPorts())

    def _serialPortChange(self) -> None:
        """Detect if the serial port has changed."""
        self._serialPort = self.serialPortsComboBox.currentText()
        self.startStreamingButton.setEnabled(self._serialPort != "")

    def _alertSerialError(self) -> None:
        """Alert message displayed when serial communication fails."""
        self._alert = QMessageBox.critical(
            self,
            "Serial communication failed",
            "Could not communicate with the device: try changing the serial port.",
            buttons=QMessageBox.Retry,
            defaultButton=QMessageBox.Retry,
        )
        self._stopStreaming()

    @Slot(np.ndarray)
    def _plotData(self, data: np.ndarray):
        """This method is called automatically when the associated signal is received,
        it grabs data from the signal and plots it.

        Parameters
        ----------
        data : ndarray
            Data to plot.
        """
        for samples in data:
            self._xQueue.append(self._xQueue[-1] + 1 / self._sampFreq)
            self._yQueue.append(samples)
        self._bufferCount += data.shape[0]

        if self._bufferCount >= self._bufferSize:
            ys = np.asarray(self._yQueue).T
            for i in range(6):
                self._plots[i].setData(
                    self._xQueue, ys[i], skipFiniteCheck=True
                )
            self._bufferCount = 0

    def _startStreaming(self) -> None:
        """Start streaming."""
        logging.info("MainWindow: streaming started.")

        # Attempt to create streaming controller
        self._streamController = StreamingController(self._serialPort, self._sampFreq)
        self._streamController.dataReadyFltSig.connect(self._plotData)
        self._streamController.serialErrorSig.connect(self._alertSerialError)
        self._streamController.dataReadySig.connect(lambda d: self.dataReadySig.emit(d))
        self._streamController.dataReadyFltSig.connect(
            lambda d: self.dataReadyFltSig.emit(d)
        )

        # Handle UI elements
        self.startStreamingButton.setEnabled(False)
        self.stopStreamingButton.setEnabled(True)
        self.streamConfGroupBox.setEnabled(False)

        self.startStreamingSig.emit()
        self._streamController.startStreaming()

    def _stopStreaming(self) -> None:
        """Stop streaming."""
        self._streamController.stopStreaming()
        self.stopStreamingSig.emit()

        # Handle UI elements
        self.streamConfGroupBox.setEnabled(True)
        self.startStreamingButton.setEnabled(True)
        self.stopStreamingButton.setEnabled(False)

        logging.info("MainWindow: streaming stopped.")
