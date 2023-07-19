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
import os
from collections import deque

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QFileDialog, QMainWindow, QRadioButton
from scipy import signal

from ._acquisition._abc_acq_controller import AcquisitionController
from ._acquisition._dummy_acq_controller import DummyAcquisitionController
from ._acquisition._esb_acq_controller import ESBAcquisitionController
from ._file_controller import FileController
from ._gesture_window import GeturesWindow
from ._svm_controller import SVMController
from ._ui.ui_main_window import Ui_MainWindow
from ._utils import load_validate_json, load_validate_train_data, serial_ports
from ._svm_train_window import SVMWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window showing the real time plot.

    Parameters
    ----------
    fs : int
        Sampling frequency.
    wl : int
        Memory of the internal deques.
    dummy : bool, default=False
        Whether to use dummy signals.

    Attributes
    ----------
    _x : deque
        Deque for X values.
    _y : deque
        Deque for Y values.
    _nCh : int
        Number of channels.
    _fs : int
        Sampling frequency.
    _serialPort : str
        Serial port.
    _config : dit
        Dictionary representing the experiment configuration.
    _bufCount : int
        Counter for the plot buffer.
    _dummy : bool
        Whether to use dummy signals.
    _plotSpacing : int
        Spacing between each channel in the plot.
    _plotBuffer : int
        Size of the buffer for plotting samples.
    _plots : list of PlotItems
        List containing a PlotItem for each channel.
    _gestWin : GeturesWindow
        Window for gesture visualization.
    _acqController : AcquisitionController
        Controller for the acquisition.
    _b : ndarray
        Numerator polynomials for the filter.
    _a : ndarray
        Denominator polynomials for the filter.
    _zi : list of ndarrays
        Initial state for the filter (one per channel).
    """

    def __init__(self, fs: int, wl: int, dummy: bool = False):
        super(MainWindow, self).__init__()

        self._fs = fs
        self._x = deque(maxlen=wl)
        self._y = deque(maxlen=wl)
        self._bufCount = 0
        self._dummy = dummy
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

        # Acquisition
        self._acqController: AcquisitionController = None
        self.startAcquisitionButton.setEnabled(self._serialPort != "" or self._dummy)
        self.stopAcquisitionButton.setEnabled(False)
        self.startAcquisitionButton.clicked.connect(self._startAcquisition)
        self.stopAcquisitionButton.clicked.connect(self._stopAcquisition)

        # Training SVM
        self._SVMWin: SVMWindow | None = None
        self._trainData: np.ndarray | None = None 
        self.startTrainButton.clicked.connect(self._showSVM)
        self.browseTrainButton.clicked.connect(self._browseTrainData)

        # Filtering
        self._sos= signal.butter(
            N=4, Wn=20, fs=4000, btype="high", output='sos'
        )
        self._zi = [signal.sosfilt_zi(self._sos) for _ in range(self._nCh)]

        # TODO: temporarily disable 32 and 64 channels with real signals
        if not dummy:
            self.ch32RadioButton.setEnabled(False)
            self.ch64RadioButton.setEnabled(False)

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
            self._SVMWin.testButton.clicked.connect(self._startAcquisition)
            self._SVMWin.testButton.clicked.connect(self._SVMTestStart)

    def _SVMTestStart(self):
        self._svmController = SVMController(self._SVMWin._clf, self._acqController)
        self._svmController._SVMWorker.inferenceSig.connect(self.inference)
        self._SVMWin.close()



    def _rescanSerialPorts(self) -> None:
        """Rescan the serial ports to update the combo box."""
        self.serialPortsComboBox.clear()
        self.serialPortsComboBox.addItems(serial_ports())

    def _serialPortChange(self) -> None:
        """Detect if the serial port has changed."""
        self._serialPort = self.serialPortsComboBox.currentText()
        self.startAcquisitionButton.setEnabled(self._serialPort != "")

    def _initializePlot(self) -> None:
        """Render the initial plot."""
        # Reset graph
        self.graphWidget.clear()
        self.graphWidget.setYRange(0, self._plotSpacing * (self._nCh - 1))
        self.graphWidget.getPlotItem().hideAxis("bottom")
        self.graphWidget.getPlotItem().hideAxis("left")
        # Initialize deques
        for i in range(-self._x.maxlen, 0):
            self._x.append(i / self._fs)
            self._y.append(np.zeros(self._nCh))
        # Get colormap
        cm = pg.colormap.get("CET-C1")
        cm.setMappingMode("diverging")
        lut = cm.getLookupTable(nPts=self._nCh, mode="qcolor")
        colors = [lut[i] for i in range(self._nCh)]
        # Plot placeholder data
        y = np.asarray(self._y).T
        for i in range(self._nCh):
            pen = pg.mkPen(color=colors[i])
            self._plots.append(
                self.graphWidget.plot(self._x, y[i] + self._plotSpacing * i, pen=pen)
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
            self._config = load_validate_json(filePath)
            displayText = "JSON config invalid!" if self._config is None else filePath
        self.JSONLabel.setText(displayText)

    def _browseTrainData(self) -> None:
        """Browse to select the training data file."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load the training data",
            filter="*.bin",
        )
        displayText = ""
        if filePath:
            self._trainData = load_validate_train_data(filePath)
            displayText = "Train data not valid!" if self._trainData is None else filePath
        self.trainLabel.setText(displayText)

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

    def _startAcquisition(self) -> None:
        """Start the acquisition."""
        # Handle UI elements
        self.serialPortsGroupBox.setEnabled(False)
        self.channelsGroupBox.setEnabled(False)
        self.experimentGroupBox.setEnabled(False)
        self.startAcquisitionButton.setEnabled(False)
        self.trainingGroupBox.setEnabled(False)
        self.stopAcquisitionButton.setEnabled(True)

        self._acqController = (
            DummyAcquisitionController(self._nCh)
            if self._dummy
            else ESBAcquisitionController(self._serialPort, nCh=self._nCh)
        )
        self._acqController.connectDataReady(self.grabData)
        if self.experimentGroupBox.isChecked() and self._config is not None:
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
            self._gestWin.trigger_sig.connect(self._acqController.updateTrigger)
            self._fileController = FileController(outFilePath, self._acqController)
            self._gestWin.stop_sig.connect(self._fileController.stopFileWriter)

        self._acqController.startAcquisition()

    def _stopAcquisition(self) -> None:
        """Stop the acquisition."""
        self._acqController.stopAcquisition()

        if self._gestWin is not None:
            self._gestWin.close()
        # Handle UI elements
        self.serialPortsGroupBox.setEnabled(True)
        self.channelsGroupBox.setEnabled(True)
        self.experimentGroupBox.setEnabled(True)
        self.trainingGroupBox.setEnabled(True)
        self.startAcquisitionButton.setEnabled(True)
        self.stopAcquisitionButton.setEnabled(False)

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
            self._x.append(self._x[-1] + 1 / self._fs)
            self._y.append(samples[: self._nCh])

            if self._bufCount == self._plotBuffer:
                xs = list(self._x)
                ys = np.asarray(list(self._y)).T
                for i in range(self._nCh):
                    self._plots[i].setData(
                        xs, ys[i] + self._plotSpacing * i, skipFiniteCheck=True
                    )
                self._bufCount = 0
            self._bufCount += 1

    @Slot(int)
    def inference(self, label: int):
        self.trainLabel.setText(str(label))

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._acqController is not None:
            self._acqController.stopAcquisition()
        if self._gestWin is not None:
            self._gestWin.close()
        event.accept()
