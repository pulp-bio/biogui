"""
Widget for configuring signals.


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

from PySide6.QtCore import QLocale
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QWidget

from biogui.ui.signal_config_widget_ui import Ui_SignalConfigWidget


class SignalConfigWidget(QWidget, Ui_SignalConfigWidget):
    """
    Widget for configuring a signal.

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
    edit : bool, default=False
        Whether to open the dialog in edit mode and prefill the form
        with the configuration provided via the keyword arguments.
    kwargs : dict
        Keyword arguments.
    """

    def __init__(
        self,
        sigName: str,
        fs: float,
        nCh: int,
        parent: QWidget | None = None,
        edit: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self.sigNameLabel.setText(sigName)
        self.nChLabel.setText(str(nCh))
        self.freqLabel.setText(str(fs))
        self.filtTypeComboBox.currentTextChanged.connect(self._onFiltTypeChange)
        self.rangeModeComboBox.currentIndexChanged.connect(self._onRangeModeChange)
        if nCh == 1:
            self.label8.setEnabled(False)
            self.chSpacingTextField.setEnabled(False)
            self.chSpacingTextField.setText("0")

        # Validation rules
        nDec = 3
        minFreq = 10 ** (-nDec)
        maxFreq = round(fs / 2 - minFreq, nDec)  # Nyquist frequency
        lo = QLocale()
        self.freq1TextField.setToolTip(
            f"Float between {lo.toString(minFreq)} and {lo.toString(maxFreq)}"
        )
        self.freq2TextField.setToolTip(
            f"Float between {lo.toString(minFreq)} and {lo.toString(maxFreq)}"
        )

        freqValidator = QDoubleValidator(bottom=minFreq, top=maxFreq, decimals=nDec)
        freqValidator.setNotation(QDoubleValidator.StandardNotation)  # type: ignore
        self.freq1TextField.setValidator(freqValidator)
        self.freq2TextField.setValidator(freqValidator)
        orderValidator = QIntValidator(bottom=1, top=2147483647)
        self.filtOrderTextField.setValidator(orderValidator)
        chSpacingValidator = QIntValidator(bottom=0, top=2147483647)
        self.chSpacingTextField.setValidator(chSpacingValidator)
        rangeValidator = QDoubleValidator(bottom=-1e308, top=1e308, decimals=nDec)
        self.minRangeTextField.setValidator(rangeValidator)
        self.maxRangeTextField.setValidator(rangeValidator)

        self._sigName = sigName
        self._sigConfig = {"fs": fs, "nCh": nCh}

        # Pre-fill with provided configuration
        if edit:
            self._prefill(kwargs)

        self.destroyed.connect(self.deleteLater)

    @property
    def sigName(self) -> str:
        """str: Property for getting the signal name."""
        return self._sigName

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
        return self._sigConfig

    def _onFiltTypeChange(self) -> None:
        """Detect if filter type has changed."""
        filtType = self.filtTypeComboBox.currentText()
        # Disable field for second frequency depending on the filter type
        if filtType in ("highpass", "lowpass"):
            self.freq2TextField.setEnabled(False)
            self.freq2TextField.clear()
        else:
            self.freq2TextField.setEnabled(True)

    def _onRangeModeChange(self) -> None:
        """Detect if range mode has changed"""
        if self.rangeModeComboBox.currentText() == "Automatic":
            self.label10.setEnabled(False)
            self.minRangeTextField.setEnabled(False)
            self.label11.setEnabled(False)
            self.maxRangeTextField.setEnabled(False)
        else:
            self.label10.setEnabled(True)
            self.minRangeTextField.setEnabled(True)
            self.label11.setEnabled(True)
            self.maxRangeTextField.setEnabled(True)

    def validateForm(self) -> tuple[bool, str]:
        """
        Validate user input in the form.

        Returns
        -------
        bool
            Whether the configuration is valid.
        str
            Error message (if relevant.)
        """
        lo = QLocale()

        # Check filtering settings
        if self.filteringGroupBox.isChecked():
            if not self.freq1TextField.hasAcceptableInput():
                return False, 'The "Frequency 1" field is invalid.'
            freq1 = lo.toFloat(self.freq1TextField.text())[0]
            freqs = [freq1]

            if self.freq2TextField.isEnabled():
                if not self.freq2TextField.hasAcceptableInput():
                    return False, 'The "Frequency 2" field is invalid.'
                freq2 = lo.toFloat(self.freq2TextField.text())[0]

                if freq2 <= freq1:
                    return (
                        False,
                        "The 2nd critical frequency cannot be lower than the 1st critical frequency.",
                    )
                freqs.append(freq2)

            if not self.filtOrderTextField.hasAcceptableInput():
                return False, 'The "filter order" field is invalid.'

            self._sigConfig["filtType"] = self.filtTypeComboBox.currentText()
            self._sigConfig["freqs"] = freqs
            self._sigConfig["filtOrder"] = lo.toInt(self.filtOrderTextField.text())[0]

        # Check plot settings
        if self.plotGroupBox.isChecked():
            if not self.chSpacingTextField.hasAcceptableInput():
                return False, 'The "channel spacing" field is invalid.'
            self._sigConfig["chSpacing"] = lo.toInt(self.chSpacingTextField.text())[0]
            self._sigConfig["showYAxis"] = self.showYAxisCheckBox.isChecked()
            if self.rangeModeComboBox.currentText() == "Manual":
                if not self.minRangeTextField.hasAcceptableInput():
                    return False, 'The "minimum range" field is invalid.'
                minRange = lo.toFloat(self.minRangeTextField.text())[0]
                if not self.maxRangeTextField.hasAcceptableInput():
                    return False, 'The "maximum range" field is invalid.'
                maxRange = lo.toFloat(self.maxRangeTextField.text())[0]
                if maxRange <= minRange:
                    return (
                        False,
                        "The maximum range cannot be lower than the minimum range.",
                    )

                self._sigConfig["minRange"] = minRange
                self._sigConfig["maxRange"] = maxRange

        return True, ""

    def _prefill(self, sigConfig: dict):
        """Pre-fill the form with the provided configuration."""
        lo = QLocale()
        if "filtType" in sigConfig:
            self.filteringGroupBox.setChecked(True)
            idx = self.filtTypeComboBox.findText(sigConfig["filtType"])
            self.filtTypeComboBox.setCurrentIndex(idx)
            freqs = sigConfig["freqs"]
            self.freq1TextField.setText(lo.toString(freqs[0]))
            if len(freqs) == 2:
                self.freq2TextField.setText(lo.toString(freqs[1]))
            self.filtOrderTextField.setText(lo.toString(sigConfig["filtOrder"]))
        else:
            self.filteringGroupBox.setChecked(False)

        if "chSpacing" in sigConfig:
            self.plotGroupBox.setChecked(True)
            self.chSpacingTextField.setText(lo.toString(sigConfig["chSpacing"]))
            self.showYAxisCheckBox.setChecked(sigConfig["showYAxis"])
            if "minRange" in sigConfig and "maxRange" in sigConfig:
                self.rangeModeComboBox.setCurrentText("Manual")
                self.minRangeTextField.setText(lo.toString(sigConfig["minRange"]))
                self.maxRangeTextField.setText(lo.toString(sigConfig["maxRange"]))
                self.label10.setEnabled(True)
                self.minRangeTextField.setEnabled(True)
                self.label11.setEnabled(True)
                self.maxRangeTextField.setEnabled(True)
            else:
                self.rangeModeComboBox.setCurrentText("Automatic")
                self.label10.setEnabled(False)
                self.minRangeTextField.setEnabled(False)
                self.label11.setEnabled(False)
                self.maxRangeTextField.setEnabled(False)
        else:
            self.plotGroupBox.setChecked(False)
