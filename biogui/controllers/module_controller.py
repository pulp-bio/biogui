# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Controller of pluggable modules.
"""

from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction

from biogui import modules
from biogui.views import MainWindow

from .main_controller import MainController


class ModuleController(QObject):
    """
    Controller of pluggable modules.

    Parameters
    ----------
    mainController : MainController
        Instance of MainController.
    mainWin : MainWindow
        Instance of MainWindow.
    parent : QObject or None, default=None
        Parent QObject.

    Attributes
    ----------
    _mainController : MainController
        Instance of MainController.
    _mainWin : MainWindow
        Instance of MainWindow.
    _modules : dict
        Collection of pluggable modules.
    """

    def __init__(
        self,
        mainController: MainController,
        mainWin: MainWindow,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._mainController = mainController
        self._mainWin = mainWin
        self._modules: dict = {}

        moduleMenu = self._mainWin.menuBar().addMenu("Modules")

        # Add checkable action for each module
        # 1. Trigger
        triggerAction = QAction("Configure triggers", self)
        triggerAction.setCheckable(True)
        triggerAction.triggered.connect(self._triggerActionHandler)
        moduleMenu.addAction(triggerAction)

        # 2. Forwarding
        processingAction = QAction("Configure forwarding", self)
        processingAction.setCheckable(True)
        processingAction.triggered.connect(self._processingActionHandler)
        moduleMenu.addAction(processingAction)

        # 3. Teleprompter
        teleprompterAction = QAction("Configure teleprompter", self)
        teleprompterAction.setCheckable(True)
        teleprompterAction.triggered.connect(self._teleprompterActionHandler)
        moduleMenu.addAction(teleprompterAction)

    def _triggerActionHandler(self, checked: bool) -> None:
        """Handler for the "configure triggers" action."""
        if checked:
            triggerModule = modules.TriggerController(
                self._mainController.streamingControllers, self
            )
            triggerModule.subscribe(self._mainController, self._mainWin)
            self._modules["trigger"] = triggerModule
        else:
            triggerModule = self._modules.pop("trigger")
            triggerModule.unsubscribe(self._mainController, self._mainWin)
            triggerModule.deleteLater()

    def _processingActionHandler(self, checked: bool) -> None:
        """Handler for the "configure forwarding" action."""
        if checked:
            forwardingModule = modules.ForwardingController(
                self._mainController.streamingControllers, parent=self
            )
            forwardingModule.subscribe(self._mainController, self._mainWin)
            self._modules["forwardingModule"] = forwardingModule
        else:
            forwardingModule = self._modules.pop("forwardingModule")
            forwardingModule.unsubscribe(self._mainController, self._mainWin)
            forwardingModule.deleteLater()

    def _teleprompterActionHandler(self, checked: bool) -> None:
        """Handler for the "configure teleprompter" action."""
        if checked:
            teleprompterModule = modules.TeleprompterController(
                self._mainController.streamingControllers, parent=self
            )
            teleprompterModule.subscribe(self._mainController, self._mainWin)
            self._modules["teleprompter"] = teleprompterModule
        else:
            teleprompterModule = self._modules.pop("teleprompter")
            teleprompterModule.unsubscribe(self._mainController, self._mainWin)
            del teleprompterModule
