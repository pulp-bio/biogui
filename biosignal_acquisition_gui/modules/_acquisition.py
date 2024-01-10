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
from PySide6.QtWidgets import QFileDialog, QLabel, QWidget

from ..ui import resources_rc
from ..ui.ui_acquisition_config import Ui_AcquisitionConfig
from ..main_window import MainWindow


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

    @Slot(np.ndarray)
    def write(self, data: np.ndarray) -> None:
        """This method is called automatically when the associated signal is received,
        and it writes to the file the received data.

        Parameters
        ----------
        data : ndarray
            Data to write.
        """
        if self._firstWrite:  # write number of channels
            self._f.write(struct.pack("<I", data.shape[1] + 1))
            self._firstWrite = False
        data = np.concatenate(
            (data, np.repeat(self._trigger, data.shape[0]).reshape(-1, 1)), axis=1
        ).astype("float32")
        self._f.write(data.tobytes())

    def openFile(self) -> None:
        """Open the file."""
        self._f = open(self._filePath, "wb")
        self._firstWrite = True
        logging.info("FileWriterWorker: file opened.")

    def closeFile(self) -> None:
        """Close the file."""
        self._f.close()
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
            imagePath = ":/images/start.png"
        elif image == "stop":
            imagePath = ":/images/stop.png"
        else:
            imagePath = os.path.join(self._imageFolder, image)

        pixmap = QPixmap(imagePath).scaled(self.width(), self.height())
        self._label.setPixmap(pixmap)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.closeSig.emit()
        event.accept()


class _AcquisitionConfigWidget(QWidget, Ui_AcquisitionConfig):
    """Widget providing configuration options for the acquisition.

    Attributes
    ----------
    config : dict or None
        Dictionary representing the configuration of the acquisition.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setupUi(self)

        self.config = None
        self.browseJSONButton.clicked.connect(self._browseJSON)

    def _browseJSON(self) -> None:
        """Browse to select the JSON file with the experiment configuration."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load JSON configuration",
            filter="*.json",
        )
        displayText = ""
        if filePath:
            self.config = _loadValidateJSON(filePath)
            displayText = "JSON config invalid!" if self.config is None else filePath
        self.JSONLabel.setText(displayText)


class AcquisitionController(QObject):
    """Controller for the acquisition.

    Attributes
    ----------
    confWidget : _AcquisitionConfigWidget
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
        Qt signal that forwards the dataReadySig signal from MainWindow.
    """

    _dataReadySig = Signal(np.ndarray)

    def __init__(self) -> None:
        super().__init__()

        self.confWidget = _AcquisitionConfigWidget()

        self._gestWidget = _GesturesWidget()
        self._gestWidget.closeSig.connect(self._actualStopAcquisition)

        self._fileWriterWorker = _FileWriterWorker()
        self._fileWriterThread = QThread()
        self._fileWriterWorker.moveToThread(self._fileWriterThread)
        self._fileWriterThread.started.connect(self._fileWriterWorker.openFile)
        self._fileWriterThread.finished.connect(self._fileWriterWorker.closeFile)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._updateTriggerAndImage)

        self._gestCounter = 0
        self._restFlag = False

    def subscribe(self, mainWin: MainWindow) -> None:
        """Subscribe to instance of MainWindow.

        Parameters
        ----------
        mainWin : MainWindow
            Instance of MainWindow.
        """
        mainWin.addConfWidget(self.confWidget)
        mainWin.startStreamingSig.connect(self._startAcquisition)
        mainWin.stopStreamingSig.connect(self._stopAcquisition)
        mainWin.closeSig.connect(self._stopAcquisition)
        mainWin.dataReadyRawSig.connect(lambda d: self._dataReadySig.emit(d))

    def _updateTriggerAndImage(self) -> None:
        """Update the trigger for _FileWriterWorker and the image for the _GestureWidget"""
        if self._gestCounter == len(self._gesturesLabels):
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
            image = self.confWidget.config["gestures"][gestureLabel]

            self._gestCounter += 1
            self._restFlag = True

        self._fileWriterWorker.trigger = new_trigger
        self._gestWidget.renderImage(image)
        logging.info(f"Trigger updated: {old_trigger} -> {new_trigger}.")

    def _startAcquisition(self) -> None:
        """Start the acquisition."""
        if (
            self.confWidget.acquisitionGroupBox.isChecked()
            and self.confWidget.config is not None
        ):
            logging.info("AcquisitionController: acquisition started.")
            self.confWidget.acquisitionGroupBox.setEnabled(False)

            self._gestCounter = 0
            self._restFlag = False

            # Gestures
            self._gesturesId, self._gesturesLabels = {}, []
            for i, k in enumerate(self.confWidget.config["gestures"].keys()):
                self._gesturesId[k] = i + 1
                self._gesturesLabels.extend([k] * self.confWidget.config["nReps"])

            self._gestWidget.imageFolder = self.confWidget.config["imageFolder"]
            self._gestWidget.renderImage("start")
            self._gestWidget.show()

            # Output file
            expDir = os.path.join(
                os.path.dirname(self.confWidget.JSONLabel.text()), "data"
            )
            os.makedirs(expDir, exist_ok=True)
            outFileName = self.confWidget.acquisitionTextField.text()
            if outFileName == "":
                outFileName = (
                    f"acq_{datetime.datetime.now()}".replace(" ", "_")
                    .replace(":", "-")
                    .replace(".", "-")
                )
            outFileName = f"{outFileName}.bin"
            outFilePath = os.path.join(expDir, outFileName)

            # File writing
            self._fileWriterWorker.filePath = outFilePath
            self._fileWriterWorker.trigger = 0
            self._dataReadySig.connect(self._fileWriterWorker.write)
            self._fileWriterThread.start()

            self._timer.start(self.confWidget.config["durationMs"])

    def _stopAcquisition(self) -> None:
        """Stop the acquisition by exploiting GestureWidget close event."""
        self._gestWidget.close()  # the close event calls the actual stopAcquisition

    def _actualStopAcquisition(self) -> None:
        """Stop the acquisition."""
        if self._fileWriterThread.isRunning():
            self._timer.stop()
            self._dataReadySig.disconnect(self._fileWriterWorker.write)
            self._fileWriterThread.quit()
            self._fileWriterThread.wait()

            logging.info("AcquisitionController: acquisition stopped.")
            self.confWidget.acquisitionGroupBox.setEnabled(True)
