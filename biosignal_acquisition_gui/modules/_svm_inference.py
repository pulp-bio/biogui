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

import logging
from collections import deque

import numpy as np
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QWidget
from sklearn.svm import SVC
from skops.io import get_untrusted_types, load

from .._ui.ui_svm_inference_config import Ui_SVMInferenceConfig
from ..main_window import MainWindow
from ._ml_utils import majorityVoting, rootMeanSquared, waveformLength
from ._tcp_server import TCPServerController


class _SVMWorker(QObject):
    """Worker that performs inference on the data it receives via a Qt signal.

    Parameters
    ----------
    sampFreq : int
        Sampling frequency.

    Attributes
    ----------
    _sampFreq : int
        Sampling frequency.
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

    def __init__(self, sampFreq: int) -> None:
        super().__init__()

        self._sampFreq = sampFreq
        self._bufferCount = 0
        self._queue = deque()

        self._feature = "Waveform length"
        self._windowSize = int(200 * sampFreq / 1000)
        self._model = None

    @property
    def model(self) -> SVC:
        """SVC: Property representing the SVM model."""
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
        self._windowSize = int(windowSizeMs * self._sampFreq / 1000)

    @Slot(np.ndarray)
    def predict(self, data: np.ndarray) -> None:
        """This method is called automatically when the associated signal is received,
        and it performs the inference on the received data.

        Parameters
        ----------
        data : ndarray
            Data to perform inference on.
        """
        for samples in data:
            self._queue.append(samples)
        self._bufferCount += data.shape[0]

        if self._bufferCount >= 2 * self._windowSize:
            dataTmp = np.asarray(self._queue)
            nSamp, nCh = dataTmp.shape

            # Feature extraction
            featureDict = {"Waveform length": waveformLength, "RMS": rootMeanSquared}
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

    Attributes
    ----------
    model : SVC or None
        SVC model.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setupUi(self)

        self.model = None
        self.browseModelButton.clicked.connect(self._browseModel)

    def _browseModel(self) -> None:
        """Browse to select the SKOPS file with the trained SVM model."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load SVM model",
            filter="*.skops",
        )
        displayText = ""
        if filePath:
            unknownTypes = get_untrusted_types(file=filePath)
            self.model = load(filePath, trusted=unknownTypes)
            displayText = "SKOPS file invalid!" if self.model is None else filePath
        self.svmLabel.setText(displayText)


class SVMInferenceController(QObject):
    """Controller for SVM inference.

    Attributes
    ----------
    _svmWorker : _SVMWorker
        Worker for performing SVM inference.
    _svmThread : QThread
        The QThread associated to the SVM worker.

    Class attributes
    ----------------
    _dataReadySig : Signal
        Qt signal emitted when data is received.
    """

    _dataReadySig = Signal(np.ndarray)

    def __init__(self) -> None:
        super().__init__()

        self.confWidget = _SVMInferenceConfigWidget()

        # Create worker and thread
        self._svmWorker = _SVMWorker(4000)
        self._svmThread = QThread()
        self._svmWorker.moveToThread(self._svmThread)

        self._tcpServerController = None

    @property
    def tcpServerController(self) -> TCPServerController:
        """TCPServerController: Property representing the controller for TCP connections."""
        return self._tcpServerController

    @tcpServerController.setter
    def tcpServerController(self, tcpServerController: TCPServerController) -> None:
        self._tcpServerController = tcpServerController
        self._tcpServerController.signalConnect(self._svmWorker.inferenceSig)

    def subscribe(self, mainWin: MainWindow) -> None:
        """Subscribe to instance of MainWindow.

        Parameters
        ----------
        mainWin : MainWindow
            Instance of MainWindow.
        """
        mainWin.addConfWidget(self.confWidget)
        mainWin.startStreamingSig.connect(self._startInference)
        mainWin.stopStreamingSig.connect(self._stopInference)
        mainWin.closeSig.connect(self._stopInference)
        mainWin.dataReadyFltSig.connect(lambda d: self._dataReadySig.emit(d))

    def _startInference(self) -> None:
        """Start the inference."""
        if (
            self.confWidget.svmGroupBox.isChecked()
            and self.confWidget.model is not None
        ):
            logging.info("SVMInferenceController: inference started.")
            self.confWidget.svmGroupBox.setEnabled(False)

            # Handle TCP connection
            if self._tcpServerController is not None:
                self._tcpServerController.startTransmission()

            feature = self.confWidget.featureComboBox.currentText()
            windowSizeMs = self.confWidget.winTextField.text()
            windowSizeMs = (
                int(windowSizeMs) if windowSizeMs.isdigit() else 100
            )  # force default value

            self._svmWorker.feature = feature
            self._svmWorker.windowSize = windowSizeMs
            self._svmWorker.model = self.confWidget.model
            self._dataReadySig.connect(self._svmWorker.predict)
            self._svmThread.start()

    def _stopInference(self) -> None:
        """Stop the inference."""
        if self._svmThread.isRunning():
            self._dataReadySig.disconnect(self._svmWorker.predict)
            self._svmThread.quit()
            self._svmThread.wait()

            # Handle TCP connection
            if self._tcpServerController is not None:
                self._tcpServerController.stopTransmission()

            logging.info("SVMInferenceController: inference stopped.")
            self.confWidget.svmGroupBox.setEnabled(True)
