"""
This module contains controller and widgets for trigger configuration.


Copyright 2024 Mattia Orlandi, Pierangelo Maria Rapa

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
from PySide6.QtGui import QCloseEvent, QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QWidget

from biogui.controllers import MainController
from biogui.ui.trigger_config_widget_ui import Ui_TriggerConfigWidget
from biogui.utils import detectTheme
from biogui.views import MainWindow


def _loadConfigFromJson(filePath: str) -> tuple[dict | None, str]:
    """
    Load and validate a JSON file representing the trigger configuration.

    Parameters
    ----------
    filePath : str
        Path to the JSON file.

    Returns
    -------
    dict or None
        Dictionary corresponding to the configuration, or None if it's not valid.
    str
        Error message.
    """
    with open(filePath) as f:
        config = json.load(f)

    # Check keys
    providedKeys = set(config.keys())
    validKeys = {
        "triggers",
        "nReps",
        "durationTrigger",
        "durationStart",
        "durationRest",
        "imageFolder",
    }
    if providedKeys != validKeys:
        return None, "The provided keys are not valid."

    # Check paths
    if not os.path.isdir(config["imageFolder"]):
        return config, "The specified path does not exist."
    msg = ""
    for triggerLabel in config["triggers"]:
        imagePath = os.path.join(
            config["imageFolder"], config["triggers"][triggerLabel]
        )
        if not (
            os.path.isfile(imagePath)
            and (imagePath.endswith(".png") or imagePath.endswith(".jpg"))
        ):
            config["triggers"][triggerLabel] = ""
            msg = "Some images do not exist, the name of the trigger will be displayed."

    return config, msg


class _TriggerWidget(QWidget):
    """
    Widget showing the trigger.

    Attributes
    ----------
    _label : QLabel
        Label containing the image widget.
    _qColor : QColor
        Color for text.

    Class attributes
    ----------------
    widgetClosed : Signal
        Qt signal emitted when the widget is closed.
    """

    widgetClosed = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Trigger Viewer")
        self.resize(480, 480)

        self._label = QLabel(self)
        self._qColor = QColor("black" if detectTheme() == "light" else "white")

        self._imageFolder = ""

        self.destroyed.connect(self.deleteLater)

    @property
    def imageFolder(self) -> str:
        """str: Property representing the path to the folder containing the images for the triggers."""
        return self._imageFolder

    @imageFolder.setter
    def imageFolder(self, imageFolder: str) -> None:
        self._imageFolder = imageFolder

    def renderImage(self, triggerLabel: str, imagePath: str) -> None:
        """
        Render the image for the current trigger.

        Parameters
        ----------
        triggerLabel : str
            Name of the trigger.
        imagePath : str
            Path to the image file of the trigger.
        """

        def createTextPixmap(text: str) -> QPixmap:
            """Create a QPixmap containing text."""
            pixmap = QPixmap(self.width(), self.height())
            pixmap.fill(Qt.transparent)  # type: ignore

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)  # type: ignore
            painter.setPen(self._qColor)
            painter.setFont(QFont("Arial", 48))

            painter.drawText(pixmap.rect(), Qt.AlignCenter, text)  # type: ignore
            painter.end()

            return pixmap

        if imagePath == "":
            pixmap = createTextPixmap(triggerLabel.upper().replace(" ", "\n"))
        else:
            imagePath = os.path.join(self._imageFolder, imagePath)
            pixmap = QPixmap(imagePath).scaled(self.width(), self.height())

        self._label.setPixmap(pixmap)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.widgetClosed.emit()
        event.accept()


class _TriggerConfigWidget(QWidget, Ui_TriggerConfigWidget):
    """Widget providing configuration options for the trigger."""

    def __init__(self) -> None:
        super().__init__()

        self.setupUi(self)

        self._config = {}

        self.browseTriggerConfigButton.clicked.connect(self._browseTriggerConfig)
        self.destroyed.connect(self.deleteLater)

    @property
    def config(self) -> dict:
        """dict: Property representing the JSON configuration."""
        return self._config

    def _browseTriggerConfig(self) -> None:
        """Browse to select the JSON file with the trigger configuration."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load JSON configuration",
            filter="*.json",
        )
        if filePath:
            config, errMessage = _loadConfigFromJson(filePath)
            if config is None:
                QMessageBox.critical(
                    self,
                    "Invalid configuration",
                    "The provided JSON file has an invalid configuration.",
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                return
            if len(errMessage) > 0:
                QMessageBox.warning(
                    self,
                    "Invalid configuration",
                    errMessage,
                    buttons=QMessageBox.Ok,  # type: ignore
                    defaultButton=QMessageBox.Ok,  # type: ignore
                )
            self._config = config
            self.triggerConfigPathLabel.setText(filePath)


class TriggerController(QObject):
    """
    Controller for the triggers.

    Attributes
    ----------
    _confWidget : _TriggerConfigWidget
        Instance of _TriggerConfigWidget.
    _triggerWidget : _TriggerWidget
        Instance of _TriggerWidget.
    _timer : QTimer
        Timer.
    _streamControllers : dict of (str: StreamingController)
        Reference to the streaming controller dictionary.
    _triggerIds : dict of str: int
        Dictionary containing pairs of trigger labels and integer indexes.
    _triggerLabels : list of str
        List of trigger labels accounting for the number of repetitions.
    _triggerCounter : int
        Counter for the trigger.
    _restFlag : bool
        Flag for rest vs trigger.
    """

    def __init__(self) -> None:
        super().__init__()

        self._confWidget = _TriggerConfigWidget()
        self._confWidget.triggerGroupBox.clicked.connect(self._checkHandler)

        self._triggerWidget = _TriggerWidget()
        self._triggerWidget.widgetClosed.connect(self._actualStopTriggerGen)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._updateTriggerAndImage)  # type: ignore

        self._streamingControllers = {}
        self._triggerIds = {}
        self._triggerLabels = []
        self._triggerCounter = 0
        self._restFlag = False

    def subscribe(self, mainController: MainController, mainWin: MainWindow) -> None:
        """
        Subscribe to the main controller.

        Parameters
        ----------
        mainController : MainController
            Reference to the main controller.
        mainWin : MainWindow
            Reference to the main window.
        """
        # Make connections with MainWindow
        mainWin.moduleContainer.layout().addWidget(self._confWidget)  # type: ignore
        mainController.streamingStarted.connect(self._startTriggerGen)
        mainController.streamingStopped.connect(self._stopTriggerGen)
        mainController.appClosed.connect(self._stopTriggerGen)

        # Get reference to StreamingControllers
        self._streamingControllers = mainController.streamingControllers

    def unsubscribe(self, mainController: MainController, mainWin: MainWindow) -> None:
        """
        Unsubscribe from the main controller.

        Parameters
        ----------
        mainController : MainController
            Reference to the main controller.
        mainWin : MainWindow
            Reference to the main window.
        """
        # Undo connections with MainWindow
        mainWin.moduleContainer.layout().removeWidget(self._confWidget)  # type: ignore
        self._confWidget.deleteLater()
        mainController.streamingStarted.disconnect(self._startTriggerGen)
        mainController.streamingStopped.disconnect(self._stopTriggerGen)
        mainController.appClosed.disconnect(self._stopTriggerGen)

    def _checkHandler(self, checked: bool) -> None:
        """Handler for detecting whether the groupbox has been checked or not."""
        if not checked:
            # Reset trigger
            for streamingController in self._streamingControllers.values():
                streamingController.setTrigger(None)

    def _updateTriggerAndImage(self) -> None:
        """Update the trigger and the image to display."""
        if self._triggerCounter >= len(self._triggerLabels):
            self._stopTriggerGen()
            return

        if self._restFlag:  # rest
            self._timer.start(self._confWidget.config["durationRest"])

            newTrigger = 0
            triggerLabel, imagePath = "stop", ""

            self._restFlag = False

        else:  # trigger
            self._timer.start(self._confWidget.config["durationTrigger"])

            triggerLabel = self._triggerLabels[self._triggerCounter]
            if triggerLabel != "last_stop":
                newTrigger = self._triggerIds[triggerLabel]
                imagePath = self._confWidget.config["triggers"][triggerLabel]
            else:
                newTrigger = 0
                triggerLabel, imagePath = "stop", ""

            self._triggerCounter += 1
            self._restFlag = True

        # Show trigger
        self._triggerWidget.renderImage(triggerLabel, imagePath)

        # Update trigger in streaming controllers
        for streamingController in self._streamingControllers.values():
            streamingController.setTrigger(newTrigger)
        logging.info(f"Trigger updated: {newTrigger}.")

    def _startTriggerGen(self) -> None:
        """Start the trigger generation."""
        self._confWidget.triggerGroupBox.setEnabled(False)
        if self._confWidget.triggerGroupBox.isChecked() and self._confWidget.config:
            # Set initial trigger
            for streamingController in self._streamingControllers.values():
                streamingController.setTrigger(0)

            # Triggers
            for i, k in enumerate(self._confWidget.config["triggers"].keys()):
                self._triggerIds[k] = i + 1
                self._triggerLabels.extend([k] * self._confWidget.config["nReps"])
            self._triggerLabels.append("last_stop")

            self._triggerWidget.imageFolder = self._confWidget.config["imageFolder"]
            self._triggerWidget.renderImage("start", "")
            self._triggerWidget.show()

            self._timer.start(self._confWidget.config["durationStart"])

    def _stopTriggerGen(self) -> None:
        """Stop trigger generation by exploiting _TriggerWidget close event."""
        if self._triggerWidget.isVisible():
            self._triggerWidget.close()  # the close event calls _actualStopTriggerGen
        else:
            self._actualStopTriggerGen()

    def _actualStopTriggerGen(self) -> None:
        """Stop trigger generation."""
        self._timer.stop()

        self._triggerIds = {}
        self._triggerLabels = []
        self._triggerCounter = 0
        self._restFlag = False

        self._confWidget.triggerGroupBox.setEnabled(True)
