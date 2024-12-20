"""
Dialog for configuring signals.


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

from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget

from .configure_signal_widget import ConfigureSignalWidget


class ConfigureSignalDialog(QDialog):
    """
    Dialog for configuring a signal.

    Parameters
    ----------
    sigName : str
        Name of the signal.
    fs : float
        Sampling frequency.
    nCh : int
        Number of channels.
    prefillConfig : dict
        Dictionary containing the configuration to prefill the form.
    parent : QWidget or None, default=None
        Parent widget.
    """

    def __init__(
        self,
        sigName: str,
        fs: float,
        nCh: int,
        prefillConfig: dict,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._configWidget = ConfigureSignalWidget(
            sigName, fs, nCh, prefillConfig, parent
        )
        layout = QVBoxLayout()
        layout.addWidget(self._configWidget)
        self.setLayout(layout)

        # self.buttonBox.accepted.connect(self._formValidationHandler)
        # self.buttonBox.rejected.connect(self.close)

        self.destroyed.connect(self.deleteLater)
