"""
View for the real-time plot of a signal.


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

from PySide6.QtWidgets import QWidget

from biogui.ui.ui_signal_plots_widget import Ui_SignalPlotsWidget


class SignalPlotWidget(QWidget, Ui_SignalPlotsWidget):
    """
    Widget showing the real-time plot of a signal.

    Parameters
    ----------
    sigName : str
        Name of the signal to display.
    parent : QWidget or None
        Parent widget.
    """

    def __init__(self, sigName: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)
        self.graphWidget.setTitle(sigName)
        self.graphWidget.setLabel("bottom", "Time (s)")
        self.graphWidget.getPlotItem().hideAxis("left")
        self.graphWidget.getPlotItem().setMouseEnabled(False, False)
