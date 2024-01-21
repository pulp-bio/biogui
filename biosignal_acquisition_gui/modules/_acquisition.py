"""This module contains the acquisition controller and widgets.


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
import json
import logging
import os
import struct

import numpy as np
from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QCloseEvent, QPixmap
from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QWidget

from ..main_window import DataPacket, MainWindow
from ..ui.ui_acquisition_config import Ui_AcquisitionConfig


def _loadValidateJSON(filePath: str) -> dict | None:
    """Load and validate a JSON file representing the experiment configuration.

    Parameters
    ----------
    filePath : str
        Path to the JSON file.

    Returns
    -------
    dict or None
        Dictionary corresponding to the configuration, or None if it's not valid.
    """
    with open(filePath) as f:
        config = json.load(f)
    # Check keys
    providedKeys = set(config.keys())
    validKeys = {"gestures", "nReps", "durationMs", "imageFolder"}
    if providedKeys != validKeys:
        return None
    # Check paths
    if not os.path.isdir(config["imageFolder"]):
        return None
    for imagePath in config["gestures"].values():
        imagePath = os.path.join(config["imageFolder"], imagePath)
        if not (
            os.path.isfile(imagePath)
            and (imagePath.endswith(".png") or imagePath.endswith(".jpg"))
        ):
            return None

    return config


class _FileWriterWorker(QObject):
    """Worker that writes into a file the data it receives via a Qt signal.

    Attributes
    ----------
    _f : BinaryIO or None
        File object.
    _firstWrite : bool
        Whether it's the first time the worker receives data.
    """

    def __init__(self) -> None:
        super().__init__()
        self._f = None
        self._firstWrite = True

        self._filePath = ""
        self._trigger = 0
        self._targetSigName = ""

    @property
    def filePath(self) -> str:
        """str: Property representing the path to the file."""
        return self._filePath

    @filePath.setter
    def filePath(self, filePath: str) -> None:
        self._filePath = filePath

    @property
    def trigger(self) -> int:
        """int: Property representing the trigger, namely the gesture label."""
        return self._trigger

    @trigger.setter
    def trigger(self, trigger: int) -> None:
        self._trigger = trigger

    @property
    def targetSigName(self) -> str:
        """str: Property representing the target signal name."""
        return self._targetSigName

    @targetSigName.setter
    def targetSigName(self, targetSigName: str) -> None:
        self._targetSigName = targetSigName

    @Slot(DataPacket)
    def write(self, dataPacket: DataPacket) -> None:
        """This method is called automatically when the associated signal is received,
        and it writes to the file the received data.

        Parameters
        ----------
        dataPacket : DataPacket
            Data to write.
        """
        if dataPacket.id == self._targetSigName:
            if self._firstWrite:  # write number of channels
                self._f.write(struct.pack("<I", dataPacket.data.shape[1] + 1))  # type: ignore
                self._firstWrite = False
            data = np.concatenate(
                (
                    dataPacket.data,
                    np.repeat(self._trigger, dataPacket.data.shape[0]).reshape(-1, 1),
                ),
                axis=1,
            ).astype("float32")
            self._f.write(data.tobytes())  # type: ignore

    def openFile(self) -> None:
        """Open the file."""
        self._f = open(self._filePath, "wb")
        self._firstWrite = True
        logging.info("FileWriterWorker: file opened.")

    def closeFile(self) -> None:
        """Close the file."""
        self._f.close()  # type: ignore
        logging.info("FileWriterWorker: file closed.")


class _GesturesWidget(QWidget):
    """Widget showing the gestures to perform.

    Attributes
    ----------
    _pixmap : QPixmap
        Image widget.
    _label : QLabel
        Label containing the image widget.

    Class attributes
    ----------------
    closeSig : Signal
        Qt signal emitted when the widget is closed.
    """

    closeSig = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Gesture Viewer")
        self.resize(480, 480)

        self._pixmap = QPixmap(":/images/start.png")
        self._pixmap = self._pixmap.scaled(self.width(), self.height())
        self._label = QLabel(self)
        self._label.setPixmap(self._pixmap)

        self._imageFolder = ""

    @property
    def imageFolder(self) -> str:
        """str: Property representing the path to the folder containing
        the images for the gestures.
        """
        return self._imageFolder

    @imageFolder.setter
    def imageFolder(self, imageFolder: str) -> None:
        self._imageFolder = imageFolder

    def renderImage(self, image: str) -> None:
        """Render the image for the current gesture.

        Parameters
        ----------
        image : str
            Name of the image file.
        """
        if image == "start":
            imagePath = ":/images/start"
        elif image == "stop":
            imagePath = ":/images/stop"
        else:
            imagePath = os.path.join(self._imageFolder, image)

        pixmap = QPixmap(imagePath).scaled(self.width(), self.height())
        self._label.setPixmap(pixmap)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.closeSig.emit()
        event.accept()


class _AcquisitionConfigWidget(QWidget, Ui_AcquisitionConfig):
    """Widget providing configuration options for the acquisition.

    Parameters
    ----------
    mainWin : MainWindow
        Reference to MainWindow object.

    Attributes
    ----------
    _mainWin : MainWindow
        Reference to MainWindow object.
    """

    def __init__(self, mainWin: MainWindow) -> None:
        super().__init__(mainWin)

        self.setupUi(self)

        self._mainWin = mainWin
        self._config = {}
        self._sigInfo = []

        self.rescanSignalsButton.clicked.connect(self._rescanSignals)
        self.browseJSONButton.clicked.connect(self._browseAcqConfig)

    @property
    def config(self) -> dict:
        """dict: Property representing the JSON configuration."""
        return self._config

    def _browseAcqConfig(self) -> None:
        """Browse to select the JSON file with the experiment configuration."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load JSON configuration",
            filter="*.json",
        )
        if filePath:
            config = _loadValidateJSON(filePath)
            if config is None:
                QMessageBox.critical(
                    self,
                    "Invalid configuration",
                    "The provided JSON file has an invalid configuration.",
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                return

            self._config = config
            displayText = (
                filePath
                if len(filePath) <= 20
                else filePath[:6] + "..." + filePath[-14:]
            )
            self.configJSONPathLabel.setText(displayText)
            self.configJSONPathLabel.setToolTip(filePath)

    def _rescanSignals(self) -> None:
        """Re-scan the available signals."""
        self._sigInfo = self._mainWin.getSigInfo()
        self.signalComboBox.addItems(list(zip(*self._sigInfo))[0])


class AcquisitionController(QObject):
    """Controller for the acquisition.

    Parameters
    ----------
    mainWin : MainWindow
        Reference to MainWindow object.

    Attributes
    ----------
    _confWidget : _AcquisitionConfigWidget
        Instance of _AcquisitionConfigWidget.
    _gestWidget : _GesturesWidget
        Instance of _GesturesWidget.
    _fileWriterWorker : _FileWriterWorker
        Instance of _FileWriterWorker.
    _fileWriterThread : QThread
        The QThread associated to the file writer worker.
    _timer : QTimer
        Timer.
    _gesturesId : dict of {str : int}
        Dictionary containing pairs of gesture labels and integer indexes.
    _gesturesLabels : list of str
        List of gesture labels accounting for the number of repetitions.
    _gestCounter : int
        Counter for the gesture.
    _restFlag : bool
        Flag for rest vs gesture.

    Class attributes
    ----------------
    _dataReadySig : Signal
        Qt Signal that forwards the dataReadySig signal from MainWindow.
    """

    _dataReadySig = Signal(DataPacket)

    def __init__(self, mainWin: MainWindow) -> None:
        super().__init__()

        self._confWidget = _AcquisitionConfigWidget(mainWin)

        self._gestWidget = _GesturesWidget()
        self._gestWidget.closeSig.connect(self._actualStopAcquisition)

        self._fileWriterWorker = _FileWriterWorker()
        self._fileWriterThread = QThread()
        self._fileWriterWorker.moveToThread(self._fileWriterThread)
        self._fileWriterThread.started.connect(self._fileWriterWorker.openFile)  # type: ignore
        self._fileWriterThread.finished.connect(self._fileWriterWorker.closeFile)  # type: ignore

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._updateTriggerAndImage)  # type: ignore

        # Make connections with MainWindow
        mainWin.addConfWidget(self._confWidget)
        mainWin.startStreamingSig.connect(self._startAcquisition)
        mainWin.stopStreamingSig.connect(self._stopAcquisition)
        mainWin.closeSig.connect(self._stopAcquisition)
        mainWin.dataReadyRawSig.connect(lambda d: self._dataReadySig.emit(d))

        self._gesturesId = {}
        self._gesturesLabels = []
        self._gestCounter = 0
        self._restFlag = False

    def _updateTriggerAndImage(self) -> None:
        """Update the trigger for _FileWriterWorker and the image for the _GestureWidget"""
        logging.info(f"{self._gestCounter}")
        if self._gestCounter >= len(self._gesturesLabels):
            self._stopAcquisition()
            return

        if self._restFlag:  # rest
            old_trigger = self._fileWriterWorker.trigger
            new_trigger = 0
            image = "stop"

            self._restFlag = False
        else:  # gesture
            gestureLabel = self._gesturesLabels[self._gestCounter]
            old_trigger = self._fileWriterWorker.trigger
            new_trigger = self._gesturesId[gestureLabel]
            image = self._confWidget.config["gestures"][gestureLabel]

            self._gestCounter += 1
            self._restFlag = True

        self._fileWriterWorker.trigger = new_trigger
        self._gestWidget.renderImage(image)
        logging.info(f"Trigger updated: {old_trigger} -> {new_trigger}.")

    def _startAcquisition(self) -> None:
        """Start the acquisition."""
        self._confWidget.acquisitionGroupBox.setEnabled(False)
        if (
            self._confWidget.acquisitionGroupBox.isChecked()
            and len(self._confWidget.config) > 0
        ):
            logging.info("AcquisitionController: acquisition started.")

            # Gestures
            for i, k in enumerate(self._confWidget.config["gestures"].keys()):
                self._gesturesId[k] = i + 1
                self._gesturesLabels.extend([k] * self._confWidget.config["nReps"])

            self._gestWidget.imageFolder = self._confWidget.config["imageFolder"]
            self._gestWidget.renderImage("start")
            self._gestWidget.show()

            # Output file
            expDir = os.path.join(
                os.path.dirname(self._confWidget.configJSONPathLabel.text()), "data"
            )
            os.makedirs(expDir, exist_ok=True)
            outFileName = self._confWidget.acquisitionTextField.text()
            if outFileName == "":
                outFileName = (
                    f"acq_{datetime.datetime.now()}".replace(" ", "_")
                    .replace(":", "-")
                    .replace(".", "-")
                )
            outFileName = f"{outFileName}.bin"
            outFilePath = os.path.join(expDir, outFileName)

            print(self._gesturesLabels, len(self._gesturesLabels))

            # File writing
            self._fileWriterWorker.filePath = outFilePath
            self._fileWriterWorker.trigger = 0
            self._fileWriterWorker.targetSigName = (
                self._confWidget.signalComboBox.currentText()
            )
            self._dataReadySig.connect(self._fileWriterWorker.write)
            self._fileWriterThread.start()

            self._timer.start(self._confWidget.config["durationMs"])

    def _stopAcquisition(self) -> None:
        """Stop the acquisition by exploiting GestureWidget close event."""
        if self._gestWidget.isVisible():
            self._gestWidget.close()  # the close event calls the actual stopAcquisition
        else:
            self._actualStopAcquisition()

    def _actualStopAcquisition(self) -> None:
        """Stop the acquisition."""
        if self._fileWriterThread.isRunning():
            self._timer.stop()
            self._dataReadySig.disconnect(self._fileWriterWorker.write)
            self._fileWriterThread.quit()
            self._fileWriterThread.wait()

            self._gesturesId = {}
            self._gesturesLabels = []
            self._gestCounter = 0
            self._restFlag = False

        logging.info("AcquisitionController: acquisition stopped.")
        self._confWidget.acquisitionGroupBox.setEnabled(True)
