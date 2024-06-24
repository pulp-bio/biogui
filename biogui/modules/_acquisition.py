"""
This module contains the acquisition controller and widgets.


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
import os

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QPixmap
from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QWidget

from ..main_window import MainWindow
from ..ui.ui_acquisition_config import Ui_AcquisitionConfig


def _loadValidateJSON(filePath: str) -> dict | None:
    """
    Load and validate a JSON file representing the experiment configuration.

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
    validKeys = {
        "gestures",
        "nReps",
        "durationGesture",
        "durationStart",
        "durationRest",
        "imageFolder",
    }
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


class _GesturesWidget(QWidget):
    """
    Widget showing the gestures to perform.

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

        self.destroyed.connect(self.deleteLater)

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
        """
        Render the image for the current gesture.

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
    """
    Widget providing configuration options for the acquisition.

    Class attributes
    ----------------
    validConfigSig : Signal
        Qt Signal emitted when the acquisition configuration is validated.
    """

    validConfigSig = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.setupUi(self)

        self._config = {}

        self.browseJSONButton.clicked.connect(self._browseAcqConfig)

        self.destroyed.connect(self.deleteLater)

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
            self._configJSONPath = filePath

            displayText = (
                filePath
                if len(filePath) <= 20
                else filePath[:6] + "..." + filePath[-14:]
            )
            self.configJSONPathLabel.setText(displayText)
            self.configJSONPathLabel.setToolTip(filePath)


class AcquisitionController(QObject):
    """
    Controller for the acquisition.

    Attributes
    ----------
    _confWidget : _AcquisitionConfigWidget
        Instance of _AcquisitionConfigWidget.
    _gestWidget : _GesturesWidget
        Instance of _GesturesWidget.
    _timer : QTimer
        Timer.
    _streamControllers : list of StreamingController
        List containing the references to the streaming controllers.
    _gesturesId : dict of (str: int)
        Dictionary containing pairs of gesture labels and integer indexes.
    _gesturesLabels : list of str
        List of gesture labels accounting for the number of repetitions.
    _gestCounter : int
        Counter for the gesture.
    _restFlag : bool
        Flag for rest vs gesture.
    """

    def __init__(self) -> None:
        super().__init__()

        self._confWidget = _AcquisitionConfigWidget()

        self._gestWidget = _GesturesWidget()
        self._gestWidget.closeSig.connect(self._actualStopAcquisition)

        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._updateTriggerAndImage)  # type: ignore

        self._streamControllers = []
        self._gesturesId = {}
        self._gesturesLabels = []
        self._gestCounter = 0
        self._restFlag = False

    def subscribeToMainWin(self, mainWin: MainWindow) -> None:
        """
        Subscribe to the main window.

        Parameters
        ----------
        mainWin : MainWindow
            Reference to the main window.
        """
        # Make connections with MainWindow
        mainWin.addConfWidget(self._confWidget)
        mainWin.startStreamingSig.connect(self._startAcquisition)
        mainWin.stopStreamingSig.connect(self._stopAcquisition)
        mainWin.closeSig.connect(self._stopAcquisition)

        # Subscribe to NewSourceAdded Signal
        mainWin.newSourceAddedSig.connect(
            lambda streamController: self._streamControllers.append(streamController)
        )

    def _updateTriggerAndImage(self) -> None:
        """Update the trigger and the image to display."""
        logging.info(f"{self._gestCounter}")
        if self._gestCounter >= len(self._gesturesLabels):
            self._stopAcquisition()
            return

        if self._restFlag:  # rest
            self._timer.start(self._confWidget.config["durationRest"])

            new_trigger = 0
            image = "stop"

            self._restFlag = False

        else:  # gesture
            self._timer.start(self._confWidget.config["durationGesture"])

            gestureLabel = self._gesturesLabels[self._gestCounter]
            if gestureLabel != "last_stop":
                new_trigger = self._gesturesId[gestureLabel]
                image = self._confWidget.config["gestures"][gestureLabel]
            else:
                new_trigger = 0
                image = "stop"

            self._gestCounter += 1
            self._restFlag = True

        for streamController in self._streamControllers:
            streamController.setTrigger(new_trigger)
        self._gestWidget.renderImage(image)
        logging.info(f"Trigger updated: {new_trigger}.")

    def _startAcquisition(self) -> None:
        """Start the acquisition."""
        self._confWidget.acquisitionGroupBox.setEnabled(False)
        if (
            self._confWidget.acquisitionGroupBox.isChecked()
            and len(self._confWidget.config) > 0
        ):
            logging.info("AcquisitionController: acquisition started.")

            # Set initial trigger
            for streamController in self._streamControllers:
                streamController.setTrigger(0)

            # Gestures
            for i, k in enumerate(self._confWidget.config["gestures"].keys()):
                self._gesturesId[k] = i + 1
                self._gesturesLabels.extend([k] * self._confWidget.config["nReps"])
            self._gesturesLabels.append("last_stop")

            self._gestWidget.imageFolder = self._confWidget.config["imageFolder"]
            self._gestWidget.renderImage("start")
            self._gestWidget.show()

            self._timer.start(self._confWidget.config["durationStart"])

    def _stopAcquisition(self) -> None:
        """Stop the acquisition by exploiting GestureWidget close event."""
        if self._gestWidget.isVisible():
            self._gestWidget.close()  # the close event calls the actual stopAcquisition
        else:
            self._actualStopAcquisition()

    def _actualStopAcquisition(self) -> None:
        """Stop the acquisition."""
        self._timer.stop()

        self._gesturesId = {}
        self._gesturesLabels = []
        self._gestCounter = 0
        self._restFlag = False

        logging.info("AcquisitionController: acquisition stopped.")
        self._confWidget.acquisitionGroupBox.setEnabled(True)
