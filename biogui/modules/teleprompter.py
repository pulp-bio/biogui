"""
This module provides a teleprompter that loads sentences from a JSON file,
displays a "START" screen, then displays sentences one by one, uses setTrigger to mark each sentence,
and highlights each word with duration proportional to its length.

JSON structure:
{
    "sentences": ["First sentence.", "Second sentence.", ...],
    "durationStart": 1000,
    "durationPerSentence": 2000
}

Copyright 2024

Licensed under the Apache License, Version 2.0 (the "License");
...
"""

from __future__ import annotations

import json
import logging
import os
import math

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QColor, QFont
from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QWidget, QVBoxLayout

from biogui.controllers import MainController
from biogui.ui.teleprompter_config_widget_ui import Ui_TeleprompterConfigWidget
from biogui.utils import detectTheme
from biogui.views import MainWindow


def _loadTeleprompterConfig(filePath: str) -> tuple[dict | None, str]:
    """
    Load and validate a JSON file representing the teleprompter configuration.

    Expected JSON structure:
    {
        "sentences": ["First sentence.", "Second sentence.", ...],
        "durationStart": 1000,
        "durationPerSentence": 2000
    }

    Returns:
        (config dict or None, error message)
    """
    with open(filePath) as f:
        config = json.load(f)

    provided = set(config.keys())
    valid = {"sentences", "durationStart", "durationPerSentence"}
    if provided != valid:
        return None, "JSON must contain exactly 'sentences', 'durationStart', and 'durationPerSentence'."

    if not isinstance(config["sentences"], list) or len(config["sentences"]) == 0:
        return None, "'sentences' must be a non-empty list of strings."
    for idx, s in enumerate(config["sentences"]):
        if not isinstance(s, str) or s.strip() == "":
            return None, f"Sentence at index {idx} is not a valid non-empty string."

    if not isinstance(config["durationStart"], int) or config["durationStart"] < 0:
        return None, "'durationStart' must be a non-negative integer (milliseconds)."
    if not isinstance(config["durationPerSentence"], int) or config["durationPerSentence"] <= 0:
        return None, "'durationPerSentence' must be a positive integer (milliseconds)."

    return config, ""


class _TeleprompterWidget(QWidget):
    """
    Widget that displays text, highlighting each word.

    Attributes
    ----------
    _label: QLabel
        Shows the current text with HTML formatting to highlight words.
    _qColor: QColor
        Text color depending on theme.
    """

    widgetClosed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Teleprompter")
        self.resize(800, 200)

        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setWordWrap(True)
        self._label.setFont(QFont("Arial", 24))
        self._label.setTextFormat(Qt.RichText)

        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        self.setLayout(layout)

        self._qColor = QColor("black" if detectTheme() == "light" else "white")
        self._label.setStyleSheet(f"color: {self._qColor.name()};")

        self.destroyed.connect(self.deleteLater)

    def displaySentence(self, sentence: str, duration_ms: int) -> None:
        """Highlight words with timing based on word length relative to total characters."""
        words = sentence.split()
        total_chars = sum(len(w) for w in words)
        if total_chars == 0:
            return
        self._words = words
        self._char_counts = [len(w) for w in words]
        self._current_word_idx = 0
        self._duration_ms = duration_ms
        self._computeIntervals(total_chars)
        self._updateLabel()
        try:
            self._wordTimer.stop()
        except AttributeError:
            pass
        self._wordTimer = QTimer(self)
        self._wordTimer.setInterval(self._intervals[0])
        self._wordTimer.timeout.connect(self._advanceWord)
        self._wordTimer.start()

    def _computeIntervals(self, total_chars: int) -> None:
        """Compute interval for each word proportional to its length."""
        self._intervals = []
        for count in self._char_counts:
            interval = math.floor(self._duration_ms * (count / total_chars))
            # Ensure each interval at least 1 ms
            self._intervals.append(max(interval, 1))
        # Adjust last interval to fill any rounding gap
        sum_intervals = sum(self._intervals)
        if sum_intervals < self._duration_ms:
            self._intervals[-1] += self._duration_ms - sum_intervals

    def _updateLabel(self) -> None:
        """Update the QLabel HTML to highlight the current word."""
        highlighted = []
        for idx, w in enumerate(self._words):
            if idx == self._current_word_idx:
                highlighted.append(f"<span style='background-color: yellow;'>{w}</span>")
            else:
                highlighted.append(w)
        html = " ".join(highlighted)
        self._label.setText(html)

    def _advanceWord(self) -> None:
        self._current_word_idx += 1
        if self._current_word_idx >= len(self._words):
            self._wordTimer.stop()
            return
        self._updateLabel()
        self._wordTimer.setInterval(self._intervals[self._current_word_idx])

    def displayStart(self, text: str) -> None:
        """Display a plain start text centered."""
        self._label.setText(f"<span style='font-size: 32px; font-weight: bold;'>{text}</span>")

    def closeEvent(self, event: QCloseEvent) -> None:
        self.widgetClosed.emit()
        event.accept()


class _TeleprompterConfigWidget(QWidget, Ui_TeleprompterConfigWidget):
    """
    Configuration widget to load teleprompter JSON.

    UI should contain:
    - QGroupBox teleprompterGroupBox (checkbox)
    - QPushButton browseTeleprompterConfigButton
    - QLabel teleprompterConfigPathLabel
    """

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self._config = {}

        self.teleprompterGroupBox.clicked.connect(self._checkHandler)
        self.browseTeleprompterConfigButton.clicked.connect(self._browseConfig)
        self.destroyed.connect(self.deleteLater)

    @property
    def config(self) -> dict:
        return self._config

    def _browseConfig(self) -> None:
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Teleprompter JSON",
            filter="*.json",
        )
        if filePath:
            config, err = _loadTeleprompterConfig(filePath)
            if config is None:
                QMessageBox.critical(self, "Invalid JSON", err)
                return
            self._config = config
            self.teleprompterConfigPathLabel.setText(filePath)

    def _checkHandler(self, checked: bool) -> None:
        if not checked:
            self.parentController._stopTeleprompter()


class TeleprompterController(QObject):
    """
    Controller for the teleprompter. On streaming start, displays a START screen,
    then iterates through sentences, calls the widget to highlight words for each sentence,
    then moves to next.

    Attributes
    ----------
    _timer: QTimer
        Timer to advance to the next sentence.
    _startTimer: QTimer
        Single-shot timer for start display.
    _sentences: list[str]
        List of sentences loaded from JSON.
    _index: int
        Current sentence index.
    _streamingControllers: dict of str: StreamingController
        References to all streaming controllers for setTrigger calls.
    """

    def __init__(self) -> None:
        super().__init__()
        self._confWidget = _TeleprompterConfigWidget()
        self._confWidget.parentController = self

        self._teleWidget = _TeleprompterWidget()
        self._teleWidget.widgetClosed.connect(self._stopTeleprompter)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._showNextSentence)

        self._sentences: list[str] = []
        self._duration = 0
        self._durationStart = 0
        self._index = 0
        self._streamingControllers: dict[str, object] = {}

    def subscribe(self, mainController: MainController, mainWin: MainWindow) -> None:
        mainWin.moduleContainer.layout().addWidget(self._confWidget)
        mainController.streamingStarted.connect(self._startTeleprompter)
        mainController.streamingStopped.connect(self._stopTeleprompter)
        mainController.appClosed.connect(self._stopTeleprompter)
        self._streamingControllers = mainController.streamingControllers

    def unsubscribe(self, mainController: MainController, mainWin: MainWindow) -> None:
        mainWin.moduleContainer.layout().removeWidget(self._confWidget)
        self._confWidget.deleteLater()
        mainController.streamingStopped.disconnect(self._stopTeleprompter)
        mainController.appClosed.disconnect(self._stopTeleprompter)

    def _startTeleprompter(self) -> None:
        if not self._confWidget.teleprompterGroupBox.isChecked() or not self._confWidget.config:
            return
        config = self._confWidget.config
        self._sentences = config["sentences"]
        self._duration = config["durationPerSentence"]
        self._durationStart = config["durationStart"]
        self._index = 0

        for ctrl in self._streamingControllers.values():
            ctrl.setTrigger(0)

        # Show START screen
        self._teleWidget.displayStart("START")
        self._teleWidget.show()
        QTimer.singleShot(self._durationStart, self._beginSentences)

    def _beginSentences(self) -> None:
        # After start duration, show first sentence
        for ctrl in self._streamingControllers.values():
            ctrl.setTrigger(1)
        self._teleWidget.displaySentence(self._sentences[self._index], self._duration)
        self._timer.start(self._duration)

    def _showNextSentence(self) -> None:
        self._index += 1
        if self._index >= len(self._sentences):
            self._stopTeleprompter()
            return
        for ctrl in self._streamingControllers.values():
            ctrl.setTrigger(self._index + 1)
        self._teleWidget.displaySentence(self._sentences[self._index], self._duration)

    def _stopTeleprompter(self) -> None:
        if self._teleWidget.isVisible():
            self._teleWidget.close()
        self._timer.stop()
        for ctrl in self._streamingControllers.values():
            ctrl.setTrigger(0)
        self._sentences = []
        self._index = 0
