"""This module containes the controller for SVM inference.


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
import struct

import numpy as np
from PySide6.QtCore import QObject, QSize, QThread, Signal, Slot
from PySide6.QtGui import QMovie
from PySide6.QtWidgets import QFileDialog, QWidget
from scipy import signal
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from skops.io import dump

from emg_armband_gui._ui import resources_rc
from emg_armband_gui._ui.ui_svm_train_config import Ui_SVMTrainConfig
from emg_armband_gui.main_window import MainWindow
from emg_armband_gui.modules._ml_utils import rootMeanSquared, waveformLength


def _loadValidateTrainData(filePath: str) -> np.ndarray | None:
    """Load and validate a .bin file containg the training data.

    Parameters
    ----------
    filePath : str
        Path the the .bin file.

    Returns
    -------
    ndarray or None
        Training data with shape (nSamp, nCh + 1) or None if the file is not valid.
    """
    # Open file and check if it is reshapable
    with open(filePath, "rb") as f:
        nChAndTrigger = struct.unpack("<I", f.read(4))[0]
        bSig = bytes(f.read())
    data = np.frombuffer(bSig, dtype="float32")
    if data.size % nChAndTrigger != 0:
        return None

    return data.reshape(-1, nChAndTrigger)


class _SVMTrainWorker(QObject):
    """Worker that performs training of a SVM.

    Parameters
    ----------
    sampFreq : int
        Sampling frequency.

    Attributes
    ----------
    _sampFreq : int
        Sampling frequency.

    Class attributes
    ----------------
    trainStopSig : Signal
        Signal emitted when the training is finished.
    """

    trainStopSig = Signal(float)

    def __init__(self, sampFreq: int) -> None:
        super().__init__()

        self._sampFreq = sampFreq

        self._feature = "Waveform length"
        self._windowSize = int(200 * sampFreq / 1000)
        self._model = None
        self._trainData = None

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

    @property
    def model(self) -> SVC:
        """SVC: Property representing the SVM model."""
        return self._model

    @model.setter
    def model(self, model: SVC) -> None:
        self._model = model

    @property
    def trainData(self) -> np.ndarray:
        """ndarray: Property representing the training data as an array with shape (nSamp, nCh + 1)."""
        return self._trainData

    @trainData.setter
    def trainData(self, trainData: np.ndarray) -> None:
        self._trainData = trainData

    def train(self) -> None:
        """Train the model."""
        # Preprocessing
        logging.info("SVMTrainWorker: preprocessing...")
        sos = signal.butter(4, 20, "high", output="sos", fs=self._sampFreq)
        dataFlt = signal.sosfiltfilt(sos, self._trainData[:, :-1], axis=0)
        nSamp, nCh = dataFlt.shape
        labels = self._trainData[:, -1].astype("int32")

        # Feature extraction
        logging.info(
            f"SVMTrainWorker: feature extraction (feature: {self._feature}, window size: {self._windowSize})..."
        )
        featureDict = {"Waveform length": waveformLength, "RMS": rootMeanSquared}
        featureFun = featureDict[self._feature]
        dataFeat = np.zeros((nSamp - self._windowSize + 1, nCh))
        for i in range(nCh):
            dataFeat[:, i] = featureFun(dataFlt[:, i], self._windowSize)
        labels = labels[self._windowSize - 1 :]

        test_split = 0.5
        seed = 42
        for label in np.unique(labels):
            if label == 0:  # rest
                xTrainRest, xTestRest, yTrainRest, yTestRest = train_test_split(
                    dataFeat[labels == label],
                    labels[labels == label],
                    test_size=test_split,
                    random_state=seed,
                )
            else:
                xTrainContr, xTestContr, yTrainContr, yTestContr = train_test_split(
                    dataFeat[labels == label],
                    labels[labels == label],
                    test_size=test_split,
                    random_state=seed,
                )
                xTrain = np.concatenate((xTrainRest, xTrainContr))
                xTest = np.concatenate((xTestRest, xTestContr))
                yTrain = np.append(yTrainRest, yTrainContr)
                yTest = np.append(yTestRest, yTestContr)

        # Training
        logging.info(
            f"SVMTrainWorker: training... (training set size: {xTrain.shape}, test set size: {xTest.shape})"
        )
        self._model.fit(xTrain, yTrain)
        yPred = self._model.predict(xTest)

        logging.info(f"SVMTrainWorker: training ended.")

        self.trainStopSig.emit(accuracy_score(yTest, yPred))


class _SVMTrainConfigWidget(QWidget, Ui_SVMTrainConfig):
    """Widget providing configuration options for the SVM training.

    Attributes
    ----------
    trainData : ndarray or None
        Array with shape (nSamp, nCh + 1) with the training data.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setupUi(self)

        self.trainData = None
        self.browseTrainDataButton.clicked.connect(self._browseTrainData)
        self.startTrainButton.setEnabled(False)

        gifSize = 64
        self.mov = QMovie(":/images/waiting.gif")
        size = QSize(gifSize, gifSize)
        self.mov.setScaledSize(size)
        self.progressLabel.setFixedHeight(gifSize)
        self.progressLabel.setMovie(self.mov)

    def _browseTrainData(self) -> None:
        """Browse to select the binary file with the training data."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load training data configuration",
            filter="*.bin",
        )
        displayText = ""
        if filePath:
            self.trainData = _loadValidateTrainData(filePath)
            displayText = "Binary file invalid!" if self.trainData is None else filePath
        self.trainDataLabel.setText(displayText)

        self.startTrainButton.setEnabled(self.trainData is not None)


class SVMTrainController(QObject):
    """Controller for SVM inference.

    Parameters
    ----------
    sampFreq : int
        Sampling frequency.

    Attributes
    ----------
    confWidget : _SVMTrainConfigWidget
        Instance of _SVMTrainConfigWidget.
    _svmTrainWorker : _SVMTrainWorker or None
        Instance of _SVMTrainWorker
    _svmTrainThread : QThread
        QThread associated to the SVM train worker.
    """

    def __init__(self, sampFreq: int) -> None:
        super().__init__()

        self.confWidget = _SVMTrainConfigWidget()
        self.confWidget.startTrainButton.clicked.connect(self._startTraining)

        self._svmTrainWorker = _SVMTrainWorker(sampFreq)
        self._svmTrainThread = QThread()
        self._svmTrainWorker.moveToThread(self._svmTrainThread)
        self._svmTrainThread.started.connect(self._svmTrainWorker.train)
        self._svmTrainWorker.trainStopSig.connect(self._stopTraining)

    def subscribe(self, mainWin: MainWindow) -> None:
        """Subscribe to instance of MainWindow.

        Parameters
        ----------
        mainWin : MainWindow
            Instance of MainWindow.
        """
        mainWin.addWidget(self.confWidget)

    def _startTraining(self) -> None:
        """Start the SVM training."""

        feature = self.confWidget.featureComboBox.currentText()
        windowSizeMs = self.confWidget.winTextField.text()
        windowSizeMs = (
            int(windowSizeMs) if windowSizeMs.isdigit() else 100
        )  # force default value
        kernel = self.confWidget.kernelComboBox.currentText()
        C = self.confWidget.cTextField.text()
        C = float(C) if C.replace(".", "", 1).isdigit() else 1.0  # force default value

        self.confWidget.progressLabel.show()
        self.confWidget.mov.start()
        self.confWidget.setEnabled(False)

        self._svmTrainWorker.feature = feature
        self._svmTrainWorker.windowSize = windowSizeMs
        self._svmTrainWorker.model = SVC(C=C, kernel=kernel)
        self._svmTrainWorker.trainData = self.confWidget.trainData
        self._svmTrainThread.start()

    @Slot(float)
    def _stopTraining(self, acc: float) -> None:
        """This method is called automatically when the associated signal is received,
        and it stops the SVM training.

        Parameters
        ----------
        acc : float
            Accuracy on the test set.
        """
        self._svmTrainThread.quit()
        self._svmTrainThread.wait()

        self.confWidget.setEnabled(True)
        self.confWidget.mov.stop()
        self.confWidget.progressLabel.hide()

        self.confWidget.accLabel.setText(f"{acc:.2%}")

        # Output file
        expDir = os.path.join(
            os.path.dirname(self.confWidget.trainDataLabel.text()), "..", "models"
        )
        os.makedirs(expDir, exist_ok=True)
        outFileName = self.confWidget.outModelTextField.text()
        if outFileName == "":
            outFileName = (
                f"svm_{datetime.datetime.now()}".replace(" ", "_")
                .replace(":", "-")
                .replace(".", "-")
            )
        outFileName = f"{outFileName}.skops"
        outFilePath = os.path.join(expDir, outFileName)
        dump(self._svmTrainWorker.model, outFilePath)
