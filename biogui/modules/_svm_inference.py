"""This module contains the controller for SVM inference.


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

import json
import logging
import socket
import struct
from collections import deque

import numpy as np
from PySide6.QtCore import QLocale, QObject, QThread, Signal, Slot
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget
from sklearn.svm import SVC
from skops.io import get_untrusted_types, load

from ..main_window import DataPacket, MainWindow
from ..ui.ui_svm_inference_config import Ui_SVMInferenceConfig
from ._ml_utils import majorityVoting, rootMeanSquared, waveformLength


class _TCPServerWorker(QObject):
    """Worker that creates a TCP socket to control the virtual hand in Simulink.

    Parameters
    ----------
    port : str
        Server port.
    gestureMap : dict of {int : list of int}
        Mapping between gesture label and joint angles.

    Attributes
    ----------
    _port : str
        Server port.
    _sock : socket or None
        TCP socket.
    _conn : socket or None
        Connection to the virtual hand.
    _gestureMap : dict of {int : list of int}
        Mapping between gesture label and joint angles.
    """

    def __init__(self, port: int, gestureMap: dict[int, list[int]]) -> None:
        super(_TCPServerWorker, self).__init__()

        self._port = port
        self._gestureMap = gestureMap

        self._sock = None
        self._conn = None
        self._forceExit = False

    @property
    def forceExit(self) -> bool:
        """bool: Property for forcing exit from socket accept."""
        return self._forceExit

    @forceExit.setter
    def forceExit(self, forceExit: bool) -> None:
        self._forceExit = forceExit

    def openConnection(self) -> None:
        """Open the connection for the Simulink TCP client."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.settimeout(1.0)
        self._sock.bind(("", self._port))
        self._sock.listen(1)
        logging.info(f"TCPServerWorker: waiting for connection on port {self._port}.")

        # Non-blocking accept
        while True:
            try:
                if self._forceExit:
                    break
                self._conn, _ = self._sock.accept()
                logging.info(
                    f"TCPServerWorker: connection on port {self._port} from {self._conn}."
                )
                break
            except socket.timeout:
                pass

    def closeConnection(self) -> None:
        """Close the connection."""
        if self._conn is not None:
            self._conn.shutdown(socket.SHUT_RDWR)
            self._conn.close()
        self._sock.shutdown(socket.SHUT_RDWR)
        self._sock.close()

    @Slot(int)
    def sendMovements(self, data: int) -> None:
        """This method is called automatically when the associated signal is received, and
        it sends the new hand position using the TCP socket.

        Parameters
        ----------
        data : int
            Gesture label.
        """
        if self._conn is not None:
            mov = self._gestureMap[data]
            self._conn.sendall(struct.pack(f"{len(mov)}i", *mov))


class _TCPServerController(QObject):
    """Controller for the TCP servers.

    Parameters
    ----------
    port1 : str
        port for the first socket connected to the virtual hand
    port2 : str
        port for the second socket connected to the target hand
    gestureMap : dict of {int : list of int}
        Mapping between gesture label and joint angles.

    Attributes
    ----------
    _tcpServerWorker1 : _TCPServerWorker
        Instance of _TCPServerWorker.
    _tcpServerThread1 : QThread
        The QThread associated to the TCP server worker.
    _tcpServerWorker2 : _TCPServerWorker
        Instance of _TCPServerWorker.
    _tcpServerThread2 : QThread
        The QThread associated to the TCP server worker.
    """

    def __init__(
        self, port1: int, port2: int, gestureMap: dict[int, list[int]]
    ) -> None:
        super(_TCPServerController, self).__init__()

        # Create worker and thread for first connection
        self._tcpServerWorker1 = _TCPServerWorker(port1, gestureMap)
        self._tcpServerThread1 = QThread()
        self._tcpServerWorker1.moveToThread(self._tcpServerThread1)
        self._tcpServerThread1.started.connect(self._tcpServerWorker1.openConnection)
        self._tcpServerThread1.finished.connect(self._tcpServerWorker1.closeConnection)
        # Create worker and thread for second connection
        self._tcpServerWorker2 = _TCPServerWorker(port2, gestureMap)
        self._tcpServerThread2 = QThread()
        self._tcpServerWorker2.moveToThread(self._tcpServerThread2)
        self._tcpServerThread2.started.connect(self._tcpServerWorker2.openConnection)
        self._tcpServerThread2.finished.connect(self._tcpServerWorker2.closeConnection)

    def signalConnect(self, sig: Signal) -> None:
        """Connect a given signal to the TCPServerWorker send method.

        Parameters
        ----------
        sig : Signal
            Qt signal to connect to the TCPServerWorker send method.
        """
        sig.connect(self._tcpServerWorker1.sendMovements)
        sig.connect(self._tcpServerWorker2.sendMovements)

    def startTransmission(self) -> None:
        """Start the transmission to TCP clients."""
        self._tcpServerThread1.start()
        self._tcpServerThread2.start()

    def stopTransmission(self) -> None:
        """Stop the transmission to TCP clients."""
        self._tcpServerWorker1.forceExit = True
        self._tcpServerWorker2.forceExit = True
        self._tcpServerThread1.quit()
        self._tcpServerThread2.quit()
        self._tcpServerThread1.wait()
        self._tcpServerThread2.wait()


class _SVMWorker(QObject):
    """Worker that performs inference on the data it receives via a Qt Signal.

    Attributes
    ----------
    _bufferCount : int
        Counter for the inference buffer.
    _queue : deque
        Buffer for performing inference.

    Class attributes
    ----------------
    inferenceSig : Signal
        Qt signal emitted when inference is performed.
    """

    inferenceSig = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        self._fs = 0.0
        self._feature = ""
        self._windowSize = 0
        self._bufferCount = 0
        self._model = None

        self._queue = deque()
        self._targetSigName = ""

    @property
    def fs(self) -> float:
        """float: Property representing the sampling frequency."""
        return self._fs

    @fs.setter
    def fs(self, fs: float) -> None:
        self._fs = fs

    @property
    def model(self) -> SVC | None:
        """SVC or None: Property representing the SVM model."""
        return self._model

    @model.setter
    def model(self, model: SVC) -> None:
        self._model = model

    @property
    def feature(self) -> str:
        """str: Property representing the feature to be computed."""
        return self._feature

    @feature.setter
    def feature(self, feature: str) -> None:
        self._feature = feature

    @property
    def windowSize(self) -> int:
        """int: Property representing the window size for feature computation.

        The setter accepts the size in milliseconds and automatically converts it to samples.
        """
        return self._windowSize

    @windowSize.setter
    def windowSize(self, windowSizeMs: int) -> None:
        self._windowSize = int(windowSizeMs * self._fs / 1000)

    @property
    def targetSigName(self) -> str:
        """str: Property representing the target signal name."""
        return self._targetSigName

    @targetSigName.setter
    def targetSigName(self, targetSigName: str) -> None:
        self._targetSigName = targetSigName

    @Slot(DataPacket)
    def predict(self, dataPacket: DataPacket) -> None:
        """This method is called automatically when the associated signal is received,
        and it performs the inference on the received data.

        Parameters
        ----------
        dataPacket : DataPacket
            Data to perform inference on.
        """
        if dataPacket.id == self._targetSigName:
            for samples in dataPacket.data:
                self._queue.append(samples)
            self._bufferCount += dataPacket.data.shape[0]

            if self._bufferCount >= 2 * self._windowSize:
                dataTmp = np.asarray(self._queue)
                nSamp, nCh = dataTmp.shape

                # Feature extraction
                featureDict = {
                    "Waveform length": waveformLength,
                    "RMS": rootMeanSquared,
                }
                featureFun = featureDict[self._feature]
                dataFeat = np.zeros((nSamp - self._windowSize + 1, nCh))
                for i in range(nCh):
                    dataFeat[:, i] = featureFun(dataTmp[:, i], self._windowSize)

                # Inference
                labels = self._model.predict(dataFeat)
                label = majorityVoting(labels, self._windowSize).astype("int32").item()

                self.inferenceSig.emit(label)
                logging.info(f"SVMWorker: predicted label {label}.")

                self._bufferCount = 0
                self._queue.clear()


class _SVMInferenceConfigWidget(QWidget, Ui_SVMInferenceConfig):
    """Widget providing configuration options for the SVM inference.

    Parameters
    ----------
    mainWin : MainWindow
        Reference to MainWindow object.

    Attributes
    ----------
    _mainWin : MainWindow
        Reference to MainWindow object.
    _sigInfo : list of tuples of (str, float)
        Signal information.
    """

    def __init__(self, mainWin: MainWindow) -> None:
        super().__init__(mainWin)

        self.setupUi(self)

        self._mainWin = mainWin
        self._model = None
        self._fs = 0.0
        self._gestureMapping = {}

        self.rescanSignalsButton.clicked.connect(self._rescanSignals)
        self.signalComboBox.currentIndexChanged.connect(self._onSignalChange)
        self.browseModelButton.clicked.connect(self._browseModel)
        self.browseJSONButton.clicked.connect(self._browseMapping)

        # Validation rules
        minWinSizeMs, maxWinSizeMs = 1, 5000

        self.winSizeTextField.setToolTip(
            f"Integer between {minWinSizeMs} and {maxWinSizeMs}"
        )
        winSizeValidator = QIntValidator(bottom=minWinSizeMs, top=maxWinSizeMs)
        self.winSizeTextField.setValidator(winSizeValidator)

    @property
    def model(self) -> SVC | None:
        """SVC or None: Property representing the SVM model."""
        return self._model

    @property
    def gestureMap(self) -> dict:
        """dict: Dictionary with gesture mapping."""
        return self._gestureMapping

    @property
    def fs(self) -> float:
        """float: Property representing the sampling frequency."""
        return self._fs

    def isValid(self) -> bool:
        """Check if the configuration is valid.

        Returns
        -------
        bool
            Whether the configuration is valid.
        """
        return self.winSizeTextField.hasAcceptableInput() and self._model is not None

    def _browseModel(self) -> None:
        """Browse to select the SKOPS file with the trained SVM model."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load SVM model",
            filter="*.skops",
        )
        if filePath:
            unknownTypes = get_untrusted_types(file=filePath)
            model = load(filePath, trusted=unknownTypes)
            if model is None:
                QMessageBox.critical(
                    self,
                    "Invalid configuration",
                    "The provided SKOPS file is invalid.",
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                return

            self._model = model

            displayText = (
                filePath
                if len(filePath) <= 24
                else filePath[:8] + "..." + filePath[-16:]
            )
            self.svmModelPathLabel.setText(displayText)
            self.svmModelPathLabel.setToolTip(filePath)

    def _browseMapping(self) -> None:
        """Browse to select the JSON file with the gesture mapping."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load gesture mapping JSON",
            filter="*.json",
        )
        if filePath:
            with open(filePath) as f:
                gestureMapping = json.load(f)
                gestureMapping = {i: k for i, k in enumerate(gestureMapping.values())}

            self._gestureMapping = gestureMapping

            displayText = (
                filePath
                if len(filePath) <= 16
                else filePath[:6] + "..." + filePath[-10:]
            )
            self.mappingJSONPathLabel.setText(displayText)
            self.mappingJSONPathLabel.setToolTip(filePath)

    def _onSignalChange(self) -> None:
        """Detect if signal has changed."""
        sigNameList, fsList = list(zip(*self._sigInfo))
        self._fs = fsList[sigNameList.index(self.signalComboBox.currentText())]

    def _rescanSignals(self) -> None:
        """Re-scan the available signals."""
        self._sigInfo = self._mainWin.getSigInfo()
        self.signalComboBox.addItems(list(zip(*self._sigInfo))[0])


class SVMInferenceController(QObject):
    """Controller for SVM inference.

    Parameters
    ----------
    mainWin : MainWindow
        Reference to MainWindow object.

    Attributes
    ----------
    _svmWorker : _SVMWorker
        Worker for performing SVM inference.
    _svmThread : QThread
        The QThread associated to the SVM worker.

    Class attributes
    ----------------
    _dataReadySig : Signal
        Qt Signal emitted when data is received.
    """

    _dataReadySig = Signal(DataPacket)

    def __init__(self, mainWin: MainWindow) -> None:
        super().__init__()

        self._confWidget = _SVMInferenceConfigWidget(mainWin)

        # Create worker and thread
        self._svmWorker = _SVMWorker()
        self._svmThread = QThread()
        self._svmWorker.moveToThread(self._svmThread)

        self._svmWorker.inferenceSig.connect(
            lambda label: self._confWidget.svmPredLabel.setText(str(label))
        )

        self._tcpServerController = None

        # Make connections with MainWindow
        mainWin.addConfWidget(self._confWidget)
        mainWin.startStreamingSig.connect(self._startInference)
        mainWin.stopStreamingSig.connect(self._stopInference)
        mainWin.closeSig.connect(self._stopInference)
        mainWin.dataReadyRawSig.connect(lambda d: self._dataReadySig.emit(d))

    def _startInference(self) -> None:
        """Start the inference."""
        lo = QLocale()

        if self._confWidget.svmGroupBox.isChecked() and self._confWidget.isValid():
            logging.info("SVMInferenceController: inference started.")
            # self._confWidget.svmGroupBox.setEnabled(False)

            # Handle UBHand connection
            if (
                self._confWidget.ubHandGroupBox.isChecked()
                and len(self._confWidget.gestureMap) > 0
            ):
                self._tcpServerController = _TCPServerController(
                    port1=3334, port2=3335, gestureMap=self._confWidget.gestureMap
                )
                self._tcpServerController.signalConnect(self._svmWorker.inferenceSig)
                self._tcpServerController.startTransmission()

            feature = self._confWidget.featureComboBox.currentText()
            windowSizeMs = lo.toInt(self._confWidget.winSizeTextField.text())[0]

            self._svmWorker.fs = self._confWidget.fs
            self._svmWorker.feature = feature
            self._svmWorker.windowSize = windowSizeMs
            self._svmWorker.model = self._confWidget.model
            self._svmWorker.targetSigName = (
                self._confWidget.signalComboBox.currentText()
            )
            self._dataReadySig.connect(self._svmWorker.predict)
            self._svmThread.start()

    def _stopInference(self) -> None:
        """Stop the inference."""
        if self._svmThread.isRunning():
            self._dataReadySig.disconnect(self._svmWorker.predict)
            self._svmThread.quit()
            self._svmThread.wait()

            # Handle UBHand connection
            if self._tcpServerController is not None:
                self._tcpServerController.stopTransmission()

            logging.info("SVMInferenceController: inference stopped.")
            # self._confWidget.svmGroupBox.setEnabled(True)
