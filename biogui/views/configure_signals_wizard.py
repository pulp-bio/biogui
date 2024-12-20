"""
Wizard for configuring signals.


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

from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QWidget, QWizard, QWizardPage

from .configure_signal_widget import ConfigureSignalWidget


class ConfigureSignalWizardPage(QWizardPage):
    """
    Wizard page for configuring a signal.

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

    Attributes
    ----------
    _configWidget : ConfigureSignalWidget
        Instance of ConfigureSignalWidget.
    """

    def __init__(
        self,
        sigName: str,
        fs: float,
        nCh: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._configWidget = ConfigureSignalWidget(
            sigName, fs, nCh, prefillConfig=None, parent=parent
        )
        layout = QVBoxLayout()
        layout.addWidget(self._configWidget)
        self.setLayout(layout)

    @property
    def sigName(self) -> str:
        """str: Property for getting the signal name."""
        return self._configWidget.sigName

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

    def validatePage(self) -> bool:
        isValid, errMessage = self._configWidget.validateForm()
        if not isValid:
            QMessageBox.critical(
                self,
                "Invalid signal configuration",
                errMessage,
                buttons=QMessageBox.Retry,  # type: ignore
                defaultButton=QMessageBox.Retry,  # type: ignore
            )
            return False

        return True


class ConfigureSignalsWizard(QWizard):
    """
    Wizard for configuring signals.

    Parameters
    ----------
    sigInfo : dict
        Dictionary with the signal information, namely:
        - signal name;
        - sampling frequency;
        - number of channels.
    parent : QWidget or None, default=None
        Parent widget.
    """

    def __init__(
        self,
        sigInfo: dict,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        # Populate wizard
        for sigName in sigInfo:
            self.addPage(
                ConfigureSignalWizardPage(sigName, **sigInfo[sigName], parent=self)
            )

        finishButton = self.button(QWizard.FinishButton)  # type: ignore
        finishButton.clicked.connect(self.onFinishedClicked)

        self._sigsConfigs = {}

        self.destroyed.connect(self.deleteLater)

    @property
    def sigsConfigs(self) -> dict:
        """
        dict: Property for getting, for each signal, the dictionary with its configuration, namely:
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
        return self._sigsConfigs

    def onFinishedClicked(self) -> None:
        """Handler for the event raised when the finish button is clicked."""
        # Iterate through all pages in the wizard
        for pageId in self.pageIds():
            page = self.page(pageId)
            if isinstance(page, ConfigureSignalWizardPage):
                # Merge the configuration from each page
                self._sigsConfigs[page.sigName] = page.sigConfig
