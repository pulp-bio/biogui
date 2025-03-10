"""
Controller of pluggable modules.


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

    Attributes
    ----------
    _mainController : MainController
        Instance of MainController.
    _mainWin : MainWindow
        Instance of MainWindow.
    _modules : dict
        Collection of pluggable modules.
    """

    def __init__(self, mainController: MainController, mainWin: MainWindow) -> None:
        super().__init__()

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

        # 2. Custom processing
        processingAction = QAction("Configure custom processing", self)
        processingAction.setCheckable(True)
        processingAction.triggered.connect(self._processingActionHandler)
        moduleMenu.addAction(processingAction)

    def _triggerActionHandler(self, checked: bool) -> None:
        """Handler for the "configure triggers" action."""
        if checked:
            triggerModule = modules.TriggerController()
            triggerModule.subscribe(self._mainController, self._mainWin)
            self._modules["trigger"] = triggerModule
        else:
            triggerModule = self._modules.pop("trigger")
            triggerModule.unsubscribe(self._mainController, self._mainWin)
            del triggerModule

    def _processingActionHandler(self, checked: bool) -> None:
        """Handler for the "configure custom processing" action."""
        if checked:
            processingModule = modules.ProcessingController()
            processingModule.subscribe(self._mainController, self._mainWin)
            self._modules["processingModule"] = processingModule
        else:
            processingModule = self._modules.pop("processingModule")
            processingModule.unsubscribe(self._mainController, self._mainWin)
            del processingModule
