"""
Main class for BioGUI application.


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

from PySide6.QtWidgets import QApplication

from biogui.controllers import MainController, ModuleController
from biogui.views import MainWindow


class BioGUI(QApplication):
    """
    Main class for BioGUI application.

    Attributes
    ----------
    _mainWin : MainWindow
        Main window of the application.
    _mainController : MainController
        Main controller of the application.
    _moduleController : ModuleController
        Controller for pluggable modules.
    """

    def __init__(self) -> None:
        super().__init__()

        self._mainWin = MainWindow()
        self._mainController = MainController(self._mainWin)
        self._moduleController = ModuleController(self._mainController, self._mainWin)
        self._mainWin.show()
