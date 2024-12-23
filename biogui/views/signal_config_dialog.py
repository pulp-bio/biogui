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

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from .signal_config_widget import SignalConfigWidget


class SignalConfigDialog(QDialog):
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
    parent : QWidget or None, default=None
        Parent widget.
    kwargs : dict
        Keyword arguments.
    """

    def __init__(
        self,
        sigName: str,
        fs: float,
        nCh: int,
        parent: QWidget | None = None,
        **kwargs,
    ) -> None:
        super().__init__(parent)

        self._configWidget = SignalConfigWidget(
            sigName, fs, nCh, parent=parent, edit=True, **kwargs
        )
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self  # type: ignore
        )
        layout = QVBoxLayout()
        layout.addWidget(self._configWidget)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

        self.buttonBox.accepted.connect(self._validateDialog)
        self.buttonBox.rejected.connect(self.reject)

        self.destroyed.connect(self.deleteLater)

    @property
    def sigConfig(self) -> dict:
        """
        dict: Property for getting the dictionary with the signal configuration, namely:
        - "fs": the sampling frequency;
        - "nCh": the number of channels;
        - "filtType": the filter type (optional);
        - "freqs": list with the cut-off frequencies (optional);
        - "filtOrder" the filter order (optional);
        - "chSpacing": the channel spacing (optional);
        - "showYAxis": whether to show the Y axis (optional);
        - "minRange": minimum of the Y range (optional);
        - "maxRange": maximum of the Y range (optional).
        """
        return self._configWidget.sigConfig

    def _validateDialog(self) -> None:
        """Validate the dialog."""
        isValid, errMessage = self._configWidget.validateForm()
        if not isValid:
            QMessageBox.critical(
                self,
                "Invalid signal configuration",
                errMessage,
                buttons=QMessageBox.Retry,  # type: ignore
                defaultButton=QMessageBox.Retry,  # type: ignore
            )
            return

        self.accept()
