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
import math
from types import MappingProxyType

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
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            return None, f"JSON decode error: {e}"

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

    # Check values
    if not isinstance(config["nReps"], int) or config["nReps"] <= 0:
        return None, "The number of repetitions must be a positive integer."
    if not isinstance(config["durationTrigger"], int) or config["durationTrigger"] <= 0:
        return None, "The duration of the trigger must be a positive int."
    if not isinstance(config["durationStart"], int) or config["durationStart"] < 0:
        return None, "The duration of the start period must be a non-negative int."
    if not isinstance(config["durationRest"], int) or config["durationRest"] < 0:
        return None, "The duration of the rest period must be a non-negative int."

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
            msg = "Some images do not exist; the name of the trigger will be displayed."

    return config, msg


class _TriggerWidget(QWidget):
    """
    Widget showing either a stimulus image/label or a countdown with next stimulus label during rest.

    Attributes
    ----------
    _label : QLabel
        The QLabel that holds a combined QPixmap for countdown and upcoming label.
    _qColor : QColor
        Text color (black in light theme, white in dark theme).
    """

    widgetClosed = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Trigger Viewer")
        self.resize(480, 480)

        self._label = QLabel(self)
        self._qColor = QColor("black" if detectTheme() == "light" else "white")

        self._imageFolder = ""

    @property
    def imageFolder(self) -> str:
        """str: Path to the folder containing the images for the triggers."""
        return self._imageFolder

    @imageFolder.setter
    def imageFolder(self, imageFolder: str) -> None:
        self._imageFolder = imageFolder

    def renderImage(self, mainText: str, imagePath: str, subText: str = "") -> None:
        """
        Render:
        - Stimulus image if imagePath is non-empty.
        - For plain text (no imagePath): if subText is provided,
          draw mainText (next label) above and subText (countdown) below.
        - If no subText, draw mainText centered.

        Parameters
        ----------
        mainText : str
            For stimulus: label or "stop"/"start". For rest: upcoming stimulus label.
        imagePath : str
            If non-empty, filename of the image inside imageFolder.
        subText : str
            If provided (during rest), the countdown number as a string.
        """
        pixmap = QPixmap(self.width(), self.height())
        pixmap.fill(Qt.transparent)  # type: ignore

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)  # type: ignore
        painter.setPen(self._qColor)

        if imagePath:
            # Display the image file scaled to widget size
            fullPath = os.path.join(self._imageFolder, imagePath)
            img = QPixmap(fullPath).scaled(self.width(), self.height())
            painter.drawPixmap(0, 0, img)
        else:
            if subText:
                # Rest period: draw upcoming label and countdown
                # Draw next label at top half, smaller font
                painter.setFont(QFont("Arial", 48))
                rect_top = pixmap.rect().adjusted(0, 0, 0, -self.height() // 2)
                painter.drawText(rect_top, Qt.AlignCenter, mainText.upper())  # type: ignore
                # Draw countdown at bottom half, larger font
                painter.setFont(QFont("Arial", 72))
                rect_bot = pixmap.rect().adjusted(0, self.height() // 2, 0, 0)
                painter.drawText(rect_bot, Qt.AlignCenter, subText)  # type: ignore
            else:
                # Plain label (start/stop or stimulus without image)
                try:
                    # If mainText can be parsed as int, treat as countdown-only
                    _ = int(mainText)
                    painter.setFont(QFont("Arial", 72))
                except ValueError:
                    painter.setFont(QFont("Arial", 48))
                painter.drawText(
                    pixmap.rect(), Qt.AlignCenter, mainText.upper().replace(" ", "\n")  # type: ignore
                )

        painter.end()
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

    @property
    def config(self) -> dict:
        """dict: JSON configuration."""
        return self._config

    def _browseTriggerConfig(self) -> None:
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
                    errMessage,
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

    Parameters
    ----------
    streamingControllers : MappingProxyType
        Read-only reference to the streaming controller dictionary.
    parent : QObject or None, default=None
        Parent QObject.

    Attributes
    ----------
    _streamingControllers : MappingProxyType
        Read-only reference to the streaming controller dictionary.
    _timer : QTimer
        Primary timer for switching between stimulus and rest.
    _countdownTimer : QTimer
        Secondary timer for the countdown during rest.
    _triggerIds : dict of (str: int)
        Dictionary containing the trigger IDs.
    _triggerLabels : list of str
        List containing the trigger labels.
    _triggerCounter : int
        Counter for the trigger.
    _restFlag : bool
        Flag denoting the rest state.
    _restCounter : int
        Counter for the rest state.
    _upcomingLabel : str
        Upcoming label.
    """

    def __init__(
        self, streamingControllers: MappingProxyType, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)

        self._streamingControllers = streamingControllers
        self._confWidget = _TriggerConfigWidget()
        self._triggerWidget = _TriggerWidget()
        self._triggerWidget.widgetClosed.connect(self._actualStopTriggerGen)

        # Primary timer for switching between stimulus and rest
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._updateTriggerAndImage)

        # Secondary timer: fires every second during rest to decrement the countdown
        self._countdownTimer = QTimer(self)
        self._countdownTimer.setInterval(1000)
        self._countdownTimer.timeout.connect(self._updateCountdown)

        self._triggerIds: dict[str, int] = {}
        self._triggerLabels: list[str] = []
        self._triggerCounter = 0
        self._restFlag = True
        self._restCounter = 0
        self._upcomingLabel = ""

    def subscribe(self, mainController: MainController, mainWin: MainWindow) -> None:
        # Add configuration widget to main window
        mainWin.moduleContainer.layout().addWidget(self._confWidget)  # type: ignore

        # Make connections with main controller
        mainController.streamingStarted.connect(self._startTriggerGen)
        mainController.streamingStopped.connect(self._stopTriggerGen)

        self._streamingControllers = mainController.streamingControllers

    def unsubscribe(self, mainController: MainController, mainWin: MainWindow) -> None:
        # Remove configuration widget from main window
        mainWin.moduleContainer.layout().removeWidget(self._confWidget)  # type: ignore
        self._confWidget.deleteLater()

        # Undo connections with main controller
        mainController.streamingStarted.disconnect(self._startTriggerGen)
        mainController.streamingStopped.disconnect(self._stopTriggerGen)

    def _updateTriggerAndImage(self) -> None:
        """Called when the primary timer times out. Decides whether to show a stimulus or start the rest countdown."""
        # If the countdownTimer is running, do nothing
        if self._countdownTimer.isActive():
            return

        # If we've shown all triggers, stop
        if self._triggerCounter >= len(self._triggerLabels):
            self._stopTriggerGen()
            return

        if self._restFlag:
            # Start a new rest interval
            restMs = self._confWidget.config["durationRest"]
            # Compute initial seconds for countdown (round up)
            self._restCounter = math.ceil(restMs / 1000)
            # Determine upcoming stimulus label
            if self._triggerCounter < len(self._triggerLabels):
                nextLabel = self._triggerLabels[self._triggerCounter]
                self._upcomingLabel = nextLabel
            else:
                self._upcomingLabel = ""
            # Draw countdown with upcoming label
            self._triggerWidget.renderImage(
                self._upcomingLabel, "", str(self._restCounter)
            )
            # Force triggers to zero during rest
            for streamingController in self._streamingControllers.values():
                streamingController.setTrigger(0)
            logging.info(
                f"Rest started: upcoming='{self._upcomingLabel}' \
                countdown={self._restCounter}s (durationRest={restMs}ms)."
            )
            # Schedule end of rest after exactly restMs
            QTimer.singleShot(restMs, self._endRest)
            # Begin per-second countdown updates
            self._countdownTimer.start()

        else:
            # Stimulus interval
            triggerLabel = self._triggerLabels[self._triggerCounter]
            if triggerLabel != "last_stop":
                newTrigger = self._triggerIds[triggerLabel]
                imagePath = self._confWidget.config["triggers"][triggerLabel]
            else:
                newTrigger = 0
                triggerLabel, imagePath = "stop", ""

            # Show either the image or label for the stimulus
            self._triggerWidget.renderImage(triggerLabel, imagePath)
            for streamingController in self._streamingControllers.values():
                streamingController.setTrigger(newTrigger)
            logging.info(f"Trigger updated: {newTrigger} (label: {triggerLabel}).")

            self._triggerCounter += 1
            self._restFlag = True
            # After `durationTrigger` ms, call this same function again
            self._timer.start(self._confWidget.config["durationTrigger"])

    def _updateCountdown(self) -> None:
        """
        Called every 1 second during rest: decrement restCounter, update display.
        Actual end of rest is scheduled by singleShot.
        """
        self._restCounter -= 1
        if self._restCounter > 0:
            self._triggerWidget.renderImage(
                self._upcomingLabel, "", str(self._restCounter)
            )
            logging.info(
                f"Rest countdown: upcoming='{self._upcomingLabel}', {self._restCounter}s remaining."
            )

    def _endRest(self) -> None:
        """
        Called once when rest interval (durationRest ms) elapses. Stop countdown timer, switch back to stimulus flow.
        """
        if self._countdownTimer.isActive():
            self._countdownTimer.stop()
        self._restFlag = False
        logging.info("Rest ended, proceeding to next trigger.")
        self._updateTriggerAndImage()

    def _startTriggerGen(self) -> None:
        """Begin the whole trigger sequence (called once when streaming starts)."""
        if not self._confWidget.config:
            return

        # Initialize the trigger to zero for all streaming controllers
        for streamingController in self._streamingControllers.values():
            streamingController.setTrigger(0)

        # Build trigger IDs and replicate each label nReps times
        for i, k in enumerate(self._confWidget.config["triggers"].keys()):
            self._triggerIds[k] = i + 1
            self._triggerLabels.extend([k] * self._confWidget.config["nReps"])
        self._triggerLabels.append("last_stop")

        self._triggerWidget.imageFolder = self._confWidget.config["imageFolder"]
        # Show an initial “start” label
        self._restFlag = True
        self._triggerWidget.renderImage("start", "")
        self._triggerWidget.show()

        # Wait for durationStart before firing the very first stimulus
        self._timer.start(self._confWidget.config["durationStart"])

    def _stopTriggerGen(self) -> None:
        """Halt everything and close the viewer."""
        if self._triggerWidget.isVisible():
            self._triggerWidget.close()
        else:
            self._actualStopTriggerGen()

    def _actualStopTriggerGen(self) -> None:
        """Cleanup: stop timers and reset state."""
        if self._timer.isActive():
            self._timer.stop()
        if self._countdownTimer.isActive():
            self._countdownTimer.stop()

        self._triggerIds = {}
        self._triggerLabels = []
        self._triggerCounter = 0
        self._restFlag = False
        self._restCounter = 0
        self._upcomingLabel = ""

        # Reset triggers for all streaming controllers
        for streamingController in self._streamingControllers.values():
            streamingController.setTrigger(None)
