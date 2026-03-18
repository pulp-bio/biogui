# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Main class for BioGUI application.
"""

from PySide6.QtWidgets import QApplication

from biogui.controllers import MainController, ModuleController
from biogui.views import MainWindow


class BioGUI(QApplication):
    """
    Main class for BioGUI application.

    Attributes
    ----------
    mainWin : MainWindow
        Main window of the application.
    mainController : MainController
        Main controller of the application.
    moduleController : ModuleController
        Controller for pluggable modules.
    """

    def __init__(self) -> None:
        super().__init__()

        self.mainWin = MainWindow()
        self.mainController = MainController(self.mainWin, parent=self)
        self.aboutToQuit.connect(self.mainController.stopStreaming)
        self.moduleController = ModuleController(self.mainController, self.mainWin, parent=self)
        self.mainWin.showMaximized()
