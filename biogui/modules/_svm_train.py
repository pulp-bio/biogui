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

import datetime
import logging
import os
import struct

import numpy as np
from PySide6.QtCore import QLocale, QObject, QSize, QThread, Signal, Slot
from PySide6.QtGui import QDoubleValidator, QIntValidator, QMovie
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget
from scipy import signal
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from skops.io import dump

from ..main_window import MainWindow
from ..ui.ui_svm_train_config import Ui_SVMTrainConfig
from ._ml_utils import rootMeanSquared, waveformLength


def _loadValidateTrainData(filePath: str) -> np.ndarray | None:
    """Load and validate a .bin file containing the training data.

    Parameters
    ----------
    filePath : str
        Path to the .bin file.

    Returns
    -------
    ndarray or None
        Training data with shape (nSamp, nCh + 1) or None if the file is not valid.
    """
    # Open file and check if it is resizable
    with open(filePath, "rb") as f:
        nChAndTrigger = struct.unpack("<I", f.read(4))[0]
        bSig = bytes(f.read())
    data = np.frombuffer(bSig, dtype="float32")
    if data.size % nChAndTrigger != 0:
        return None

    return data.reshape(-1, nChAndTrigger)


class _SVMTrainWorker(QObject):
    """Worker that trains an SVM.

    Class attributes
    ----------------
    trainStopSig : Signal
        Qt signal emitted when the training is finished.
    """

    trainStopSig = Signal(float)

    def __init__(self) -> None:
        super().__init__()

        self._fs = 0.0
        self._feature = ""
        self._windowSize = 0
        self._model = None
        self._trainData = None

    @property
    def fs(self) -> float:
        """float: Property representing the sampling frequency."""
        return self._fs

    @fs.setter
    def fs(self, fs: float) -> None:
        self._fs = fs

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
    def model(self) -> SVC | None:
        """SVC or None: Property representing the SVM model."""
        return self._model

    @model.setter
    def model(self, model: SVC) -> None:
        self._model = model

    @property
    def trainData(self) -> np.ndarray | None:
        """ndarray or None: Property representing the training data as an array with shape (nSamp, nCh + 1)."""
        return self._trainData

    @trainData.setter
    def trainData(self, trainData: np.ndarray) -> None:
        self._trainData = trainData

    def train(self) -> None:
        """Train the model."""
        # Preprocessing
        logging.info("SVMTrainWorker: preprocessing...")
        sos = signal.butter(4, (20, 500), "bandpass", output="sos", fs=self._fs)
        dataFlt = signal.sosfiltfilt(sos, self._trainData[:, :-1], axis=0)
        labels = self._trainData[:, -1].astype("int32")
        nSamp, nCh = dataFlt.shape

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
        xTrain = np.zeros(shape=(0, nCh))
        yTrain = np.zeros(shape=(0,), dtype="int32")
        xTest = np.zeros(shape=(0, nCh))
        yTest = np.zeros(shape=(0,), dtype="int32")
        for label in np.unique(labels):
            xTrainTmp, xTestTmp, yTrainTmp, yTestTmp = train_test_split(
                dataFeat[labels == label],
                labels[labels == label],
                test_size=test_split,
                random_state=seed,
            )
            xTrain = np.concatenate((xTrain, xTrainTmp))
            yTrain = np.append(yTrain, yTrainTmp)
            xTest = np.concatenate((xTest, xTestTmp))
            yTest = np.append(yTest, yTestTmp)

        # Training
        logging.info(
            f"SVMTrainWorker: training... (training set size: {xTrain.shape}, test set size: {xTest.shape})"
        )
        self._model.fit(xTrain[::10], yTrain[::10])
        yPred = self._model.predict(xTest)

        logging.info("SVMTrainWorker: training ended.")

        self.trainStopSig.emit(accuracy_score(yTest, yPred))


class _SVMTrainConfigWidget(QWidget, Ui_SVMTrainConfig):
    """Widget providing configuration options for the SVM training."""

    def __init__(self) -> None:
        super().__init__()

        self.setupUi(self)

        self._fs = None
        self._trainData = None
        self._trainDataPath = ""

        self.browseTrainDataButton.clicked.connect(self._browseTrainData)
        self.startTrainButton.setEnabled(False)

        gifSize = 64
        self.mov = QMovie(":/images/waiting")
        size = QSize(gifSize, gifSize)
        self.mov.setScaledSize(size)
        self.progressLabel.setFixedHeight(gifSize)
        self.progressLabel.setMovie(self.mov)

        # Validation rules
        minWinSizeMs, maxWinSizeMs = 1, 5000
        minFreq, maxFreq = 0.001, 20_000.0
        minC, maxC = 0.0, 1000.0

        self.winSizeTextField.setToolTip(
            f"Integer between {minWinSizeMs} and {maxWinSizeMs}"
        )
        winSizeValidator = QIntValidator(bottom=minWinSizeMs, top=maxWinSizeMs)
        self.winSizeTextField.setValidator(winSizeValidator)

        self.fsTextField.setToolTip(f"Float between {minFreq:.3f} and {maxFreq:.3f}")
        fsValidator = QDoubleValidator(bottom=minFreq, top=maxFreq, decimals=3)
        fsValidator.setNotation(QDoubleValidator.StandardNotation)  # type: ignore
        self.fsTextField.setValidator(fsValidator)

        self.cTextField.setToolTip(f"Float between {minC:.3f} and {maxC:.3f}")
        cValidator = QDoubleValidator(bottom=minC, top=maxC, decimals=3)
        cValidator.setNotation(QDoubleValidator.StandardNotation)  # type: ignore
        self.cTextField.setValidator(cValidator)

    @property
    def fs(self) -> float | None:
        """float or None: Property representing the sampling frequency."""
        return self._fs

    @property
    def trainData(self) -> np.ndarray | None:
        """ndarray or None: Property representing the training data."""
        return self._trainData

    @property
    def trainDataPath(self) -> str:
        """str: Property representing the path to training data."""
        return self._trainDataPath

    def isValid(self) -> bool:
        """Check if the configuration is valid.

        Returns
        -------
        bool
            Whether the configuration is valid.
        """
        return (
            self.winSizeTextField.hasAcceptableInput()
            and self.fsTextField.hasAcceptableInput()
            and self.cTextField.hasAcceptableInput()
        )

    def _browseTrainData(self) -> None:
        """Browse to select the binary file with the training data."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load training data configuration",
            filter="*.bin",
        )
        if filePath:
            trainData = _loadValidateTrainData(filePath)
            if trainData is None:
                QMessageBox.critical(
                    self,
                    "Invalid data",
                    "The provided file does not contain valid data.",
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                return

            self._trainData = trainData
            self._trainDataPath = filePath

            displayText = (
                filePath
                if len(filePath) <= 24
                else filePath[:8] + "..." + filePath[-16:]
            )
            self.trainDataPathLabel.setText(displayText)
            self.trainDataPathLabel.setToolTip(filePath)

        self.startTrainButton.setEnabled(self._trainData is not None)


class SVMTrainController(QObject):
    """Controller for SVM inference.

    Attributes
    ----------
    _confWidget : _SVMTrainConfigWidget
        Instance of _SVMTrainConfigWidget.
    _svmTrainWorker : _SVMTrainWorker or None
        Instance of _SVMTrainWorker
    _svmTrainThread : QThread
        The QThread associated to the SVM train worker.
    """

    def __init__(self) -> None:
        super().__init__()

        self._confWidget = _SVMTrainConfigWidget()
        self._confWidget.startTrainButton.clicked.connect(self._startTraining)

        self._svmTrainWorker = _SVMTrainWorker()
        self._svmTrainThread = QThread()
        self._svmTrainWorker.moveToThread(self._svmTrainThread)
        self._svmTrainThread.started.connect(self._svmTrainWorker.train)  # type: ignore
        self._svmTrainWorker.trainStopSig.connect(self._stopTraining)

    def subscribe(self, mainWin: MainWindow) -> None:
        """Subscribe to instance of MainWindow.

        Parameters
        ----------
        mainWin : MainWindow
            Instance of MainWindow.
        """
        mainWin.addConfWidget(self._confWidget)

    def _startTraining(self) -> None:
        """Start the SVM training."""
        lo = QLocale()

        if not self._confWidget.isValid():
            QMessageBox.critical(
                self._confWidget,
                "Invalid configuration",
                "The provided configuration is invalid.",
                buttons=QMessageBox.Retry,  # type: ignore
                defaultButton=QMessageBox.Retry,  # type: ignore
            )
            return

        feature = self._confWidget.featureComboBox.currentText()
        windowSizeMs = lo.toInt(self._confWidget.winSizeTextField.text())[0]
        fs = lo.toDouble(self._confWidget.fsTextField.text())[0]
        kernel = self._confWidget.kernelComboBox.currentText()
        c = lo.toDouble(self._confWidget.cTextField.text())[0]

        self._confWidget.progressLabel.show()
        self._confWidget.mov.start()
        self._confWidget.setEnabled(False)

        self._svmTrainWorker.fs = fs
        self._svmTrainWorker.feature = feature
        self._svmTrainWorker.windowSize = windowSizeMs
        self._svmTrainWorker.model = SVC(C=c, kernel=kernel)
        self._svmTrainWorker.trainData = self._confWidget.trainData
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

        self._confWidget.setEnabled(True)
        self._confWidget.mov.stop()
        self._confWidget.progressLabel.hide()

        self._confWidget.accLabel.setText(f"{acc:.2%}")

        # Output file
        expDir = os.path.join(
            os.path.dirname(self._confWidget.trainDataPath), "..", "models"
        )
        os.makedirs(expDir, exist_ok=True)
        outFileName = self._confWidget.outModelTextField.text()
        if outFileName == "":
            outFileName = (
                f"svm_{datetime.datetime.now()}".replace(" ", "_")
                .replace(":", "-")
                .replace(".", "-")
            )
        outFileName = f"{outFileName}.skops"
        outFilePath = os.path.join(expDir, outFileName)
        dump(self._svmTrainWorker.model, outFilePath)
