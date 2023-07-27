"""This module contains the acquisition module.


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

import numpy as np
from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QCloseEvent, QPixmap
from PySide6.QtWidgets import QFileDialog, QLabel, QWidget

from emg_armband_gui._ui import resources_rc
from emg_armband_gui._ui.ui_acquisition_config import Ui_AcquisitionConfig
from emg_armband_gui.main_window import MainWindow


def _loadValidateJSON(filePath: str) -> dict | None:
    """Load and validate a JSON file representing the experiment configuration.

    Parameters
    ----------
    file_path : str
        Path the the JSON file.

    Returns
    -------
    dict or None
        Dictionary corresponding to the configuration, or None if it's not valid.
    """
    with open(filePath) as f:
        config = json.load(f)
    # Check keys
    providedKeys = set(config.keys())
    validKeys = set(("gestures", "nReps", "durationMs", "imageFolder"))
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

    Parameters
    ----------
    filePath : str
        Path to the file.

    Attributes
    ----------
    _f : BinaryIO
        File object.
    _trigger : int
        Trigger value to save together with the data.
    """

    def __init__(self, filePath: str) -> None:
        super(_FileWriterWorker, self).__init__()
        self._f = open(filePath, "wb")
        self._trigger = 0

    @Slot(int)
    def updateTrigger(self, trigger: int) -> None:
        """"""
        logging.info(f"Trigger updated: {self._trigger} -> {trigger}")
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
        data = np.concatenate(
            (data, np.repeat(self._trigger, data.shape[0]).reshape(-1, 1)), axis=1
        ).astype("float32")
        self._f.write(data.tobytes())

    def closeFile(self) -> None:
        """Close the file."""
        self._f.close()
        logging.info("File closed")


class _GesturesWindow(QWidget):
    """Widget showing the gestures to perform.

    Parameters
    ----------
    gestures : dict of {str : str
        Dictionary containing pairs of gesture labels and paths to images.
    nReps : int
        Number of repetitions for each gesture.
    imageFolder : str
        Path to the image folder containing the images.

    Attributes
    ----------
    _gestureDict : dict of {str : str}
        Dictionary containing pairs of gesture labels and paths to images.
    _gesturesId : dict of {str : int}
        Dictionary containing pairs of gesture labels and integer indexes.
    _gesturesLabels : list of str
        List of gesture labels accounting for the number of repetitions.
    _label : QLabel
        Label containing the image widget.
    _pixmap : QPixmap
        Image widget.
    _repIdx : int
        Repetition index.
    _restFlag : bool
        Flag for rest vs gesture.
    """

    triggerSig = Signal(int)
    closeWinSig = Signal()

    def __init__(
        self,
        gestures: list[str],
        nReps: str,
        imageFolder: str,
    ) -> None:
        super().__init__()

        self._gestureDict = gestures
        self._gesturesId = {k: i + 1 for i, k in enumerate(gestures.keys())}
        self._gesturesLabels = []
        for k in gestures.keys():
            self._gesturesLabels.extend([k] * nReps)
        self._image_folder = imageFolder

        self.setWindowTitle("Gesture Viewer")
        self.resize(480, 480)

        self._label = QLabel(self)
        self._pixmap = QPixmap(":/images/start.png")
        self._pixmap = self._pixmap.scaled(self.width(), self.height())
        self._label.setPixmap(self._pixmap)

        self._repIdx = 0
        self._restFlag = True

    def renderImage(self) -> None:
        """Render the image for the current gesture."""
        if self._repIdx == len(self._gesturesLabels):
            self.close()
        elif self._restFlag:
            image_path = os.path.join(
                self._image_folder,
                self._gestureDict[self._gesturesLabels[self._repIdx]],
            )
            self._pixmap = QPixmap(image_path)
            self._pixmap = self._pixmap.scaled(self.width(), self.height())
            self._label.setPixmap(self._pixmap)

            self._restFlag = False
            self.triggerSig.emit(self._gesturesId[self._gesturesLabels[self._repIdx]])
            self._repIdx += 1
        else:
            self._pixmap = QPixmap(":/images/stop.png")
            self._pixmap = self._pixmap.scaled(self.width(), self.height())
            self._label.setPixmap(self._pixmap)

            self._restFlag = True
            self.triggerSig.emit(0)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.closeWinSig.emit()
        event.accept()


class _AcquisitionConfigWidget(QWidget, Ui_AcquisitionConfig):
    """Widget providing configuration options for the acquisition."""

    def __init__(self) -> None:
        super(_AcquisitionConfigWidget, self).__init__()

        self.setupUi(self)

        self.config = None
        self.browseJSONButton.clicked.connect(self._browseJson)

    def _browseJson(self) -> None:
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
    _gestWin : _GesturesWindow or None
        Instance of _GesturesWindow.
    _fileWriterWorker : _FileWriterWorker or None
        Instance of _FileWriterWorker.
    _timer : QTimer
        Timer.
    """

    _dataReadySig = Signal(np.ndarray)

    def __init__(self) -> None:
        super(AcquisitionController, self).__init__()

        self.confWidget = _AcquisitionConfigWidget()
        self._gestWin: _GesturesWindow | None = None
        self._fileWriterWorker: _FileWriterWorker | None = None

        self._timer = QTimer(self)

    def subscribe(self, mainWin: MainWindow) -> None:
        """Subscribe to instance of MainWindow.

        Parameters
        ----------
        mainWin : MainWindow
            Instance of MainWindow.
        """
        mainWin.addWidget(self.confWidget)
        mainWin.startStreamingSig.connect(self.startAcquisition)
        mainWin.stopStreamingSig.connect(self.stopAcquisition)
        mainWin.dataReadySig.connect(lambda d: self._dataReadySig.emit(d))

    def startAcquisition(self) -> None:
        """Start the acquisition."""
        if (
            self.confWidget.acquisitionGroupBox.isChecked()
            and self.confWidget.config is not None
        ):
            logging.info("Acquisition started.")

            config = self.confWidget.config.copy()
            durationMs = config.pop("durationMs")

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

            # File writer worker and thread
            self._fileWriterWorker = _FileWriterWorker(outFilePath)
            self._fileWriterThread = QThread()
            self._fileWriterWorker.moveToThread(self._fileWriterThread)
            self._dataReadySig.connect(self._fileWriterWorker.write)

            # Gesture window
            self._gestWin = _GesturesWindow(**config)
            self._gestWin.show()
            self._gestWin.triggerSig.connect(self._fileWriterWorker.updateTrigger)
            self._gestWin.closeWinSig.connect(self.stopAcquisition)
            self._timer.timeout.connect(self._gestWin.renderImage)

            self._fileWriterThread.start()
            self._timer.start(durationMs)

    def stopAcquisition(self) -> None:
        """Stop the acquisition."""
        if self._gestWin is not None:
            self._timer.stop()
            self._gestWin.close()
        if self._fileWriterWorker is not None:
            self._fileWriterWorker.closeFile()
            self._fileWriterThread.quit()
            self._fileWriterThread.wait()
            self._gestWin = None
            self._fileWriterWorker = None
        logging.info("Acquisition stopped.")
