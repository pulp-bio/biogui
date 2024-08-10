"""
View for the main window.


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

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow

from biogui.ui.main_window_ui import Ui_MainWindow
from biogui.utils import detectTheme

from .signal_plot_widget import SignalPlotWidget


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Main window.

    Attributes
    ----------
    sigPlotWidgets : dict of (str: SignalPlotWidget)
        Collection of SignalPlotWidget objects, indexed by the name of the signal.
    """

    def __init__(self) -> None:
        super().__init__()

        # Setup UI
        self.setupUi(self)
        theme = detectTheme()
        self.deleteDataSourceButton.setIcon(
            QIcon.fromTheme("user-trash", QIcon(f":icons/{theme}/trash"))
        )
        self.editSignalButton.setIcon(
            QIcon.fromTheme("edit-entry", QIcon(f":icons/{theme}/edit"))
        )
        self.moveLeftButton.setIcon(
            QIcon.fromTheme("arrow-left", QIcon(f":icons/{theme}/left-arrow"))
        )
        self.moveUpButton.setIcon(
            QIcon.fromTheme("arrow-up", QIcon(f":icons/{theme}/up-arrow"))
        )
        self.moveDownButton.setIcon(
            QIcon.fromTheme("arrow-down", QIcon(f":icons/{theme}/down-arrow"))
        )
        self.moveRightButton.setIcon(
            QIcon.fromTheme("arrow-right", QIcon(f":icons/{theme}/right-arrow"))
        )

        self.sigPlotWidgets: dict[str, SignalPlotWidget] = {}

    def adjustLayout(self) -> None:
        """Adjust the layout of the plots."""
        stretches = map(
            lambda n: 2**n, list(range(len(self.sigPlotWidgets) - 2, -1, -1)) + [0]
        )
        for i, s in enumerate(stretches):
            self.plotsLayout.setStretch(i, s)
