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

import datetime
import logging
import os
from collections import deque

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QFileDialog, QMainWindow, QRadioButton, QMessageBox
from scipy import signal

from emg_armband_gui._streaming import StreamingController, streamControllerFactory
from ._file_controller import FileController
from ._gesture_window import GeturesWindow
from ._svm_controller import SVMController
from ._svm_train_window import SVMWindow
from ._tcp_controller import TcpServerController
from ._ui.ui_main_window import Ui_MainWindow
from ._utils import loadValidateJSON, loadValidateTrainData, serialPorts


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window showing the real-time plot.

    Parameters
    ----------
    streamControllerType : str
        String representing StreamingController type.
    sampFreq : int
        Sampling frequency.
    renderLength : int
        Memory of the internal queues.

    Attributes
    ----------
    _streamControllerType : str
        String representing StreamingController type.
    _streamController : StreamingController or None
        Actual StreamingController instance.
    _sampFreq : int
        Sampling frequency.
    _xQueue : deque
        Queue for X values.
    _yQueue : deque
        Queue for Y values.
    _bufCount : int
        Counter for the plot buffer.
    _plotSpacing : int
        Spacing between each channel in the plot.
    _plotBuffer : int
        Size of the buffer for plotting samples.
    _serialPort : str
        Serial port.
    _nCh : int
        Number of channels.
    _plots : list of PlotItems
        List containing a PlotItem for each channel.
    _sos : ndarray
        Filter SOS coefficients.
    _zi : list of ndarrays
        Initial state for the filter (one per channel).
    _config : dict
        Dictionary representing the experiment configuration.
    _gestWin : GesturesWindow
        Window for gesture visualization.
    """

    def __init__(self, streamControllerType: str, sampFreq: int, renderLength: int) -> None:
        super(MainWindow, self).__init__()

        self._streamControllerType = streamControllerType
        self._streamController: StreamingController | None = None
        self._sampFreq = sampFreq
        self._xQueue = deque(maxlen=renderLength)
        self._yQueue = deque(maxlen=renderLength)
        self._bufCount = 0
        self._plotSpacing = 1000
        self._plotBuffer = 200

        self.setupUi(self)

        # Serial ports
        self._rescanSerialPorts()
        self._serialPort = self.serialPortsComboBox.currentText()
        self.serialPortsComboBox.currentTextChanged.connect(self._serialPortChange)
        self.rescanSerialPortsButton.clicked.connect(self._rescanSerialPorts)

        # Number of channels
        chButtons = filter(
            lambda elem: isinstance(elem, QRadioButton),
            self.channelsGroupBox.children(),
        )
        for chButton in chButtons:
            chButton.clicked.connect(self._updateChannels)
            if chButton.isChecked():
                self._nCh = int(chButton.text())  # set initial number of channels

        # Plot
        self._plots = []
        self._initializePlot()

        # Experiments
        self._gestWin: GeturesWindow | None = None
        self._config: dict | None = None
        self.browseJSONButton.clicked.connect(self._browseJson)

        # Streaming
        self.startStreamingButton.setEnabled(self._serialPort != "" or self._streamControllerType == "Dummy")
        self.stopStreamingButton.setEnabled(False)
        self.startStreamingButton.clicked.connect(self._startStreaming)
        self.stopStreamingButton.clicked.connect(self._stopStreaming)

        # Training SVM
        self._SVMWin: SVMWindow | None = None
        self._trainData: np.ndarray | None = None
        self.startTrainButton.clicked.connect(self._showSVM)
        self.browseTrainButton.clicked.connect(self._browseTrainData)

        # Filtering
        self._sos = signal.butter(N=4, Wn=20, fs=4000, btype="high", output="sos")
        self._zi = [signal.sosfilt_zi(self._sos) for _ in range(self._nCh)]

    def _rescanSerialPorts(self) -> None:
        """Rescan the serial ports to update the combo box."""
        self.serialPortsComboBox.clear()
        self.serialPortsComboBox.addItems(serialPorts())

    def _serialPortChange(self) -> None:
        """Detect if the serial port has changed."""
        self._serialPort = self.serialPortsComboBox.currentText()
        self.startStreamingButton.setEnabled(self._serialPort != "")

    def _initializePlot(self) -> None:
        """Render the initial plot."""
        # Reset graph
        self.graphWidget.clear()
        self.graphWidget.setYRange(0, self._plotSpacing * (self._nCh - 1))
        self.graphWidget.getPlotItem().hideAxis("bottom")
        self.graphWidget.getPlotItem().hideAxis("left")
        # Initialize queues
        for i in range(-self._xQueue.maxlen, 0):
            self._xQueue.append(i / self._sampFreq)
            self._yQueue.append(np.zeros(self._nCh))
        # Get colormap
        cm = pg.colormap.get("CET-C1")
        cm.setMappingMode("diverging")
        lut = cm.getLookupTable(nPts=self._nCh, mode="qcolor")
        colors = [lut[i] for i in range(self._nCh)]
        # Plot placeholder data
        y = np.asarray(self._yQueue).T
        for i in range(self._nCh):
            pen = pg.mkPen(color=colors[i])
            self._plots.append(
                self.graphWidget.plot(self._xQueue, y[i] + self._plotSpacing * i, pen=pen)
            )

    def _browseJson(self) -> None:
        """Browse to select the JSON file with the experiment configuration."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load JSON configuration",
            filter="*.json",
        )
        displayText = ""
        if filePath:
            self._config = loadValidateJSON(filePath)
            displayText = "JSON config invalid!" if self._config is None else filePath
        self.JSONLabel.setText(displayText)

    def _updateChannels(self) -> None:
        """Update the number of channels depending on user selection."""
        chButton = next(
            filter(
                lambda elem: isinstance(elem, QRadioButton) and elem.isChecked(),
                self.channelsGroupBox.children(),
            )
        )
        self._nCh = int(chButton.text())
        self._plots = []
        self._initializePlot()  # redraw plot
        self._zi = [
            signal.lfilter_zi(self._b, self._a) for _ in range(self._nCh)
        ]  # re-initialize filter

    def _startStreaming(self) -> None:
        """Start streaming."""
        # Attempt to create streaming controller
        self._streamController = streamControllerFactory(self._streamControllerType, self._serialPort, self._nCh)
        self._streamController.connectDataReady(self.grabData)
        self._streamController.connectSerialError(self._alertSerialError)

        # Handle UI elements
        self.serialPortsGroupBox.setEnabled(False)
        self.channelsGroupBox.setEnabled(False)
        self.acquisitionGroupBox.setEnabled(False)
        self.startStreamingButton.setEnabled(False)
        self.modelGroupBox.setEnabled(False)
        self.stopStreamingButton.setEnabled(True)

        # Configure acquisition
        if self.acquisitionGroupBox.isChecked() and self._config is not None:
            # Output file
            expDir = os.path.join(os.path.dirname(self.JSONLabel.text()), "data")
            os.makedirs(expDir, exist_ok=True)
            outFileName = self.experimentTextField.text()
            if outFileName == "":
                outFileName = (
                    f"acq_{datetime.datetime.now()}".replace(" ", "_")
                    .replace(":", "-")
                    .replace(".", "-")
                )
            outFileName = f"{outFileName}.bin"
            outFilePath = os.path.join(expDir, outFileName)

            # Create gesture window and file controller
            self._gestWin = GeturesWindow(**self._config)
            self._gestWin.show()
            self._gestWin.trigger_sig.connect(self._streamController.updateTrigger)
            self._fileController = FileController(outFilePath, self._streamController)
            self._gestWin.stop_sig.connect(self._fileController.stopFileWriter)

        self._streamController.startStreaming()

    def _stopStreaming(self) -> None:
        """Stop streaming."""
        self._streamController.stopStreaming()

        if self._gestWin is not None:
            self._gestWin.close()
        # Handle UI elements
        self.serialPortsGroupBox.setEnabled(True)
        self.channelsGroupBox.setEnabled(True)
        self.acquisitionGroupBox.setEnabled(True)
        self.modelGroupBox.setEnabled(True)
        self.startStreamingButton.setEnabled(True)
        self.stopStreamingButton.setEnabled(False)

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

    def _showSVM(self):
        if self._trainData is not None:
            # Output file
            expDir = os.path.join(os.path.dirname(self.trainLabel.text()), "models")
            os.makedirs(expDir, exist_ok=True)
            outFileName = self.trainingTextField.text()
            if outFileName == "":
                outFileName = (
                    f"acq_{datetime.datetime.now()}".replace(" ", "_")
                    .replace(":", "-")
                    .replace(".", "-")
                )
            outFileName = f"{outFileName}.pkl"
            outFilePath = os.path.join(expDir, outFileName)

            # Create gesture window and file controller
            self._SVMWin = SVMWindow(self._trainData, outFilePath)
            self._SVMWin.show()
            self._SVMWin.testButton.clicked.connect(self._startStreaming)
            self._SVMWin.testButton.clicked.connect(self._SVMTestStart)

    def _SVMTestStart(self):
        self._svmController = SVMController(self._SVMWin._clf, self._streamControllerCls)
        self._SVMWin.close()
        self._tcpController = TcpServerController(
            "192.168.1.105", 3333, 3334, self._svmController
        )

    def _browseTrainData(self) -> None:
        """Browse to select the training data file."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load the training data",
            filter="*.bin",
        )
        displayText = ""
        if filePath:
            self._trainData = loadValidateTrainData(filePath)
            displayText = (
                "Train data not valid!" if self._trainData is None else filePath
            )
        self.trainLabel.setText(displayText)

    @Slot(bytes)
    def grabData(self, data: bytes):
        """This method is called automatically when the associated signal is received,
        it grabs data from the signal and plots it.

        Parameters
        ----------
        data : bytes
            Data to plot.
        """
        data = np.frombuffer(bytearray(data), dtype="float32").reshape(
            -1, self._nCh + 1
        )

        for i in range(self._nCh):
            data[:, i], self._zi[i] = signal.sosfilt(
                self._sos, data[:, i], axis=0, zi=self._zi[i]
            )

        for samples in data:
            self._xQueue.append(self._xQueue[-1] + 1 / self._sampFreq)
            self._yQueue.append(samples[: self._nCh])

            if self._bufCount == self._plotBuffer:
                xs = list(self._xQueue)
                ys = np.asarray(list(self._yQueue)).T
                for i in range(self._nCh):
                    self._plots[i].setData(
                        xs, ys[i] + self._plotSpacing * i, skipFiniteCheck=True
                    )
                self._bufCount = 0
            self._bufCount += 1

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._streamController is not None:
            self._streamController.stopStreaming()
        if self._gestWin is not None:
            self._gestWin.close()
        event.accept()
