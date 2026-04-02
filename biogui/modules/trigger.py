# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
This module contains controller and widgets for trigger configuration.
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
import time
from types import MappingProxyType

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QWidget

from biogui.controllers import MainController
from biogui.ui.ui_trigger_config_widget import Ui_TriggerConfigWidget
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
        "alternating",  # optional
        "shuffle",  # optional
    }
    requiredKeys = validKeys - {"alternating", "shuffle"}

    if not requiredKeys.issubset(providedKeys):
        return None, "Required keys are missing."
    if not providedKeys.issubset(validKeys):
        return None, "Invalid keys provided."

    # Check values
    if not isinstance(config["nReps"], int) or config["nReps"] <= 0:
        return None, "The number of repetitions must be a positive integer."
    if not isinstance(config["durationTrigger"], int) or config["durationTrigger"] <= 0:
        return None, "The duration of the trigger must be a positive int."
    if not isinstance(config["durationStart"], int) or config["durationStart"] < 0:
        return None, "The duration of the start period must be a non-negative int."
    if not isinstance(config["durationRest"], int) or config["durationRest"] < 0:
        return None, "The duration of the rest period must be a non-negative int."

    # Validate alternating if provided
    if "alternating" in config:
        if not isinstance(config["alternating"], bool):
            return None, "alternating must be true or false."

    # Validate shuffle if provided
    if "shuffle" in config:
        if not isinstance(config["shuffle"], bool):
            return None, "shuffle must be true or false."

    warnings: list[str] = []
    if config.get("alternating", False) and config.get("shuffle", False):
        warnings.append(
            'Both "alternating" and "shuffle" are enabled. "shuffle" takes precedence and alternating order is ignored.'
        )

    # Check paths
    if not os.path.isdir(config["imageFolder"]):
        return config, "The specified path does not exist."
    msg = ""
    for triggerLabel in config["triggers"]:
        imagePath = os.path.join(config["imageFolder"], config["triggers"][triggerLabel])
        if not (
            os.path.isfile(imagePath) and (imagePath.endswith(".png") or imagePath.endswith(".jpg"))
        ):
            config["triggers"][triggerLabel] = ""
            msg = "Some images do not exist; the name of the trigger will be displayed."

    if msg:
        warnings.append(msg)

    return config, "\n".join(warnings)


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
        self.resize(600, 600)

        self._label = QLabel(self)
        self._qColor = QColor("black" if detectTheme() == "light" else "white")

        self._imageFolder = ""
        # Store last render parameters for re-rendering on resize
        self._lastMainText = ""
        self._lastImagePath = ""
        self._lastSubText = ""

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
        # Store parameters for potential re-render
        self._lastMainText = mainText
        self._lastImagePath = imagePath
        self._lastSubText = subText

        pixmap = QPixmap(self.width(), self.height())
        pixmap.fill(Qt.transparent)  # type: ignore

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)  # type: ignore
        painter.setPen(self._qColor)

        if imagePath:
            # Display the image file scaled to widget size, preserving aspect ratio
            fullPath = os.path.join(self._imageFolder, imagePath)
            img = QPixmap(fullPath).scaled(
                self.width(),
                self.height(),
                Qt.KeepAspectRatio,  # type: ignore
                Qt.SmoothTransformation,  # type: ignore
            )
            # Center the image
            x = (self.width() - img.width()) // 2
            y = (self.height() - img.height()) // 2
            painter.drawPixmap(x, y, img)

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
                    pixmap.rect(),
                    Qt.AlignCenter,  # type: ignore
                    mainText.upper().replace(" ", "\n"),
                )

        painter.end()
        self._label.setPixmap(pixmap)

    def resizeEvent(self, event) -> None:
        """Re-render when window is resized."""
        super().resizeEvent(event)
        self._label.resize(self.size())
        if self._lastMainText:  # Only if we've rendered something
            self.renderImage(self._lastMainText, self._lastImagePath, self._lastSubText)

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

    _STOP_SENTINEL = "__internal_stop_sentinel__"

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

        # Secondary timer: checks rest deadline frequently for accurate transition timing.
        self._countdownTimer = QTimer(self)
        self._countdownTimer.setInterval(100)
        self._countdownTimer.timeout.connect(self._updateCountdown)

        self._triggerIds: dict[str, int] = {}
        self._triggerLabels: list[str] = []
        self._triggerCounter = 0
        self._restFlag = True
        self._restCounter = 0
        self._restEndsAt = 0.0
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
            # Check rest duration
            restMs = self._confWidget.config["durationRest"]
            if restMs == 0:
                self._restFlag = False
                # Don't recurse - just fall through to stimulus code below
            else:
                self._restEndsAt = time.monotonic() + (restMs / 1000.0)
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
                    f"Next is:\n{self._upcomingLabel}", "", str(self._restCounter)
                )
                # Force triggers to zero during rest
                for streamingController in self._streamingControllers.values():
                    streamingController.setTrigger(0)
                    streamingController.setTriggerStr("rest")
                logging.info(
                    f"Rest started: upcoming='{self._upcomingLabel}' \
                    countdown={self._restCounter}s (durationRest={restMs}ms)."
                )
                # Use one timer source for countdown and rest end to avoid race conditions.
                self._countdownTimer.start()
                return  # ← Exit here for rest phase

        # Stimulus interval (executed when _restFlag is False)
        if not self._restFlag:
            seqLabel = self._triggerLabels[self._triggerCounter]
            isStopMarker = seqLabel == self._STOP_SENTINEL

            if not isStopMarker:
                triggerLabel = seqLabel
                newTrigger = self._triggerIds[triggerLabel]
                imagePath = self._confWidget.config["triggers"][triggerLabel]
            else:
                newTrigger = 0
                triggerLabel, imagePath = "stop", ""

            # Show either the image or label for the stimulus
            self._triggerWidget.renderImage(triggerLabel, imagePath)
            for streamingController in self._streamingControllers.values():
                streamingController.setTrigger(newTrigger)
                streamingController.setTriggerStr(triggerLabel)
            logging.info(f"Trigger updated: {newTrigger} (label: {triggerLabel}).")

            self._triggerCounter += 1

            # Check if this was the stop trigger - if so, we're done
            if isStopMarker:
                # Don't start timer, just let it finish
                self._stopTriggerGen()
                return

            # Enter rest after each stimulus, except right before the final stop.
            if (
                self._triggerCounter < len(self._triggerLabels)
                and self._triggerLabels[self._triggerCounter] == self._STOP_SENTINEL
            ):
                self._restFlag = False
            else:
                self._restFlag = True

            # After `durationTrigger` ms, call this same function again
            self._timer.start(self._confWidget.config["durationTrigger"])

    def _updateCountdown(self) -> None:
        """
        Called during rest to refresh countdown and end rest exactly at deadline.
        """
        if self._restEndsAt <= 0.0:
            return

        remainingMs = max(0.0, (self._restEndsAt - time.monotonic()) * 1000.0)
        remainingSeconds = math.ceil(remainingMs / 1000.0) if remainingMs > 0 else 0

        if remainingSeconds > 0 and remainingSeconds != self._restCounter:
            self._restCounter = remainingSeconds
            self._triggerWidget.renderImage(
                f"Next is:\n{self._upcomingLabel}", "", str(self._restCounter)
            )
            logging.info(
                f"Rest countdown: upcoming='{self._upcomingLabel}', {self._restCounter}s remaining."
            )

        if remainingMs <= 0:
            self._endRest()

    def _endRest(self) -> None:
        """
        Called once when rest interval (durationRest ms) elapses. Stop countdown timer, switch back to stimulus flow.
        """
        if self._countdownTimer.isActive():
            self._countdownTimer.stop()
        self._restEndsAt = 0.0
        self._restFlag = False
        logging.info("Rest ended, proceeding to next trigger.")
        self._updateTriggerAndImage()

    def _startTriggerGen(self) -> None:
        if not self._confWidget.config:
            return

        for streamingController in self._streamingControllers.values():
            streamingController.setTrigger(0)
            streamingController.setTriggerStr("init")

        self._triggerIds = {}
        self._triggerLabels = []
        self._triggerCounter = 0

        triggerNames = list(self._confWidget.config["triggers"].keys())

        # IDs stay deterministic (based on JSON order)
        for i, k in enumerate(triggerNames):
            self._triggerIds[k] = i + 1

        # Create trigger sequence
        alternating = self._confWidget.config.get("alternating", False)
        shuffle = self._confWidget.config.get("shuffle", False)
        nReps = self._confWidget.config["nReps"]

        self._triggerLabels = []
        if shuffle:
            # Balanced shuffle: each trigger appears exactly nReps times in random order.
            for triggerName in triggerNames:
                self._triggerLabels.extend([triggerName] * nReps)
            random.shuffle(self._triggerLabels)
        elif alternating:
            # Alternating mode: [T1, T2, T1, T2, ...] x nReps
            for _ in range(nReps):
                for triggerName in triggerNames:
                    self._triggerLabels.append(triggerName)
        else:
            # Blocked mode (default, original behavior): [T1, T1, ..., T2, T2, ...]
            for triggerName in triggerNames:
                self._triggerLabels.extend([triggerName] * nReps)

        self._triggerLabels.append(self._STOP_SENTINEL)

        self._triggerWidget.imageFolder = self._confWidget.config["imageFolder"]
        # Show an initial "start" label and begin with rest phase to show upcoming gesture
        self._restFlag = True
        self._triggerWidget.renderImage("start", "")
        self._triggerWidget.show()

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
        self._restEndsAt = 0.0
        self._upcomingLabel = ""

        # Reset triggers for all streaming controllers
        for streamingController in self._streamingControllers.values():
            streamingController.setTrigger(None)
            streamingController.setTriggerStr(None)
