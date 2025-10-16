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

import logging

from PySide6.QtCore import QLocale
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QButtonGroup, QWidget

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
    signal_type : dict
        Type of the signal.
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
        signal_type: dict,
        parent: QWidget | None = None,
        edit: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        # Track if M-Mode display handlers are connected (to avoid disconnect warnings)
        self._mmode_handlers_connected = False

        self.sigNameLabel.setText(sigName)
        self.nChLabel.setText(str(nCh))
        self.freqLabel.setText(str(fs))
        if nCh == 1:
            self.label10.setEnabled(False)
            self.chSpacingTextField.setEnabled(False)
            self.chSpacingTextField.setText("0")

        # Disable powerline noise filtering if incompatible with the sampling rate
        if fs / 2 <= 50:
            self.notchFilterGroupBox.setEnabled(False)
            self.notchFilterGroupBox.setToolTip(
                "The sampling rate is too low to apply the 50 Hz notch filter"
            )
        elif fs / 2 <= 60:
            self.notchFreqComboBox.removeItem(1)
            self.notchFilterGroupBox.setToolTip(
                "The sampling rate is too low to apply the 60 Hz notch filter"
            )

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
        orderValidator = QIntValidator(bottom=1, top=10)
        self.filtOrderTextField.setValidator(orderValidator)
        qFactorValidator = QIntValidator(bottom=10, top=50)
        self.qFactorTextField.setValidator(qFactorValidator)
        chSpacingValidator = QDoubleValidator(bottom=0, top=1e308, decimals=nDec)
        self.chSpacingTextField.setValidator(chSpacingValidator)
        rangeValidator = QDoubleValidator(bottom=0, top=1e308, decimals=nDec)
        self.minRangeTextField.setValidator(rangeValidator)
        self.maxRangeTextField.setValidator(rangeValidator)

        self._sigName = sigName
        self._sigConfig: dict = {"fs": fs, "nCh": nCh, "signal_type": signal_type}

        # Pre-fill with provided configuration
        if edit:
            self._prefill(kwargs)

        self.filtTypeComboBox.currentTextChanged.connect(self._onFiltTypeChange)
        self.rangeModeComboBox.currentTextChanged.connect(self._onRangeModeChange)

        # activate ultrasound dropdown only for ultrasound signals
        if signal_type["type"] == "ultrasound":
            self.label14.setEnabled(True)
            self.ultrasoundModeComboBox.setEnabled(True)

            self.filterGroupBox.setEnabled(False)
            self.filterGroupBox.setToolTip(
                "Filtering is not recommended for A-Mode and M-Mode ultrasound data"
            )
            self.notchFilterGroupBox.setEnabled(False)
            self.notchFilterGroupBox.setToolTip(
                "Powerline filtering is not applicable to ultrasound spatial data"
            )

            # Enable ultrasound-specific filter controls
            self.label15.setEnabled(True)

            # For M-Mode: use radio buttons (only one view at a time)
            # For A-Mode: use checkboxes (can show multiple)
            self.showRawCheckBox.setEnabled(True)
            self.showFilteredCheckBox.setEnabled(True)
            self.showEnvelopeCheckBox.setEnabled(True)

            # Enable bandpass controls
            self.label16.setEnabled(True)  # "Bandpass Range (MHz):" label
            self.lowFreqSpinBox.setEnabled(False)  # Initially disabled
            self.highFreqSpinBox.setEnabled(False)

            # Use ADC sampling frequency for ultrasound, not the measurement rate
            adc_fs = signal_type.get("adc_sampling_freq", fs)
            nyquist_mhz = adc_fs / 2 / 1e6

            # Connect ultrasound mode change to update display options
            self.ultrasoundModeComboBox.currentTextChanged.connect(
                self._onUltrasoundModeChange
            )

            # Initially configure display options based on mode
            self._configureDisplayOptionsForMode(
                self.ultrasoundModeComboBox.currentText()
            )

            # Set default bandpass range based on ADC sampling frequency
            default_low = adc_fs / 2 * 0.1 / 1e6  # 10% of Nyquist in MHz
            default_high = adc_fs / 2 * 0.9 / 1e6  # 90% of Nyquist in MHz
            min_freq_mhz = 0.3  # 300 kHz minimum
            default_low = max(min_freq_mhz, default_low)

            self.lowFreqSpinBox.setRange(0.1, nyquist_mhz)
            self.highFreqSpinBox.setRange(0.1, nyquist_mhz)

            # Only set default values if NOT in edit mode
            if not edit:
                self.lowFreqSpinBox.setValue(default_low)
                self.highFreqSpinBox.setValue(default_high)

            # Connect show filtered/envelope to auto-enable bandpass
            self.showFilteredCheckBox.toggled.connect(self._updateBandpassState)
            self.showEnvelopeCheckBox.toggled.connect(self._updateBandpassState)

            # Initialize bandpass state
            self._updateBandpassState()

        else:
            self.label14.setEnabled(False)
            self.ultrasoundModeComboBox.setEnabled(False)

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
        - "signal_type": the signal type;
        - "filtType": the filter type (optional);
        - "freqs": list with the cut-off frequencies (optional);
        - "filtOrder" the filter order (optional);
        - "notchFreq": frequency of the notch filter (optional);
        - "qFactor": quality factor of the notch filter (optional);
        - "chSpacing": the channel spacing (optional);
        - "minRange": minimum of the Y range (optional);
        - "maxRange": maximum of the Y range (optional).
        """
        # if self.ultrasoundModeComboBox.isEnabled():
        #     self._sigConfig["ultrasoundMode"] = self.ultrasoundModeComboBox.currentText()
        #     print(f"{self._sigConfig=}")

        return self._sigConfig

    def _onFiltTypeChange(self, filtType: str) -> None:
        """Detect if filter type has changed."""
        # Disable field for second frequency depending on the filter type
        if filtType in ("highpass", "lowpass"):
            self.freq2TextField.setEnabled(False)
            self.freq2TextField.clear()
        else:
            self.freq2TextField.setEnabled(True)

    def _updateBandpassState(self) -> None:
        """Auto-enable bandpass filter if filtered/envelope display is active."""
        needs_filter = (
            self.showFilteredCheckBox.isChecked()
            or self.showEnvelopeCheckBox.isChecked()
        )

        # Enable/disable frequency controls
        self.lowFreqSpinBox.setEnabled(needs_filter)
        self.highFreqSpinBox.setEnabled(needs_filter)

    def _onRangeModeChange(self, rangeMode: str) -> None:
        """Detect if range mode has changed"""
        if rangeMode == "Automatic":
            self.label12.setEnabled(False)
            self.minRangeTextField.setEnabled(False)
            self.label13.setEnabled(False)
            self.maxRangeTextField.setEnabled(False)
        else:
            self.label12.setEnabled(True)
            self.minRangeTextField.setEnabled(True)
            self.label13.setEnabled(True)
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

        # 1. Filtering settings:
        # 1.1. Butterworth filter
        if self.filterGroupBox.isChecked():
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

        # 1.2. Powerline noise filter
        if self.notchFilterGroupBox.isChecked():
            if not self.qFactorTextField.hasAcceptableInput():
                return False, 'The "Quality factor" field is invalid.'
            self._sigConfig["notchFreq"] = lo.toFloat(
                self.notchFreqComboBox.currentText()
            )[0]
            self._sigConfig["qFactor"] = lo.toFloat(self.qFactorTextField.text())[0]

        # 3. Plot settings
        if not self.plotGroupBox.isChecked():
            return True, ""

        if not self.chSpacingTextField.hasAcceptableInput():
            return False, 'The "channel spacing" field is invalid.'
        self._sigConfig["chSpacing"] = lo.toFloat(self.chSpacingTextField.text())[0]
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

        if self.ultrasoundModeComboBox.isEnabled():
            self._sigConfig["ultrasoundMode"] = (
                self.ultrasoundModeComboBox.currentText()
            )

            # Add ultrasound display configuration
            self._sigConfig["showRaw"] = self.showRawCheckBox.isChecked()
            self._sigConfig["showFiltered"] = self.showFilteredCheckBox.isChecked()
            self._sigConfig["showEnvelope"] = self.showEnvelopeCheckBox.isChecked()

            # Bandpass wird automatisch aktiviert wenn filtered/envelope gezeigt wird
            bandpass_needed = (
                self._sigConfig["showFiltered"] or self._sigConfig["showEnvelope"]
            )
            self._sigConfig["enableBandpass"] = bandpass_needed

            if bandpass_needed:
                self._sigConfig["bandpassLow"] = (
                    self.lowFreqSpinBox.value() * 1e6
                )  # Convert to Hz
                self._sigConfig["bandpassHigh"] = self.highFreqSpinBox.value() * 1e6
            else:
                self._sigConfig["bandpassLow"] = 0.0
                self._sigConfig["bandpassHigh"] = 0.0

        logging.info(f"SignalConfigWidget: {self._sigConfig=}")

        return True, ""

    def _prefill(self, sigConfig: dict):
        """Pre-fill the form with the provided configuration."""
        lo = QLocale()

        # 1. Filtering settings:
        # 1.1. Butterworth filter
        if "filtType" in sigConfig:
            self.filterGroupBox.setChecked(True)
            self.filtTypeComboBox.setCurrentText(sigConfig["filtType"])
            freqs = sigConfig["freqs"]
            self.freq1TextField.setText(lo.toString(freqs[0]))
            if len(freqs) == 2:
                self.freq2TextField.setEnabled(True)
                self.freq2TextField.setText(lo.toString(freqs[1]))
            self.filtOrderTextField.setText(lo.toString(sigConfig["filtOrder"]))
        else:
            self.filterGroupBox.setChecked(False)

        # 1.2. Powerline noise filter
        if "notchFreq" in sigConfig:
            self.notchFilterGroupBox.setChecked(True)
            self.notchFreqComboBox.setCurrentText(
                lo.toString(int(sigConfig["notchFreq"]))
            )
            self.qFactorTextField.setText(lo.toString(sigConfig["qFactor"]))
        else:
            self.notchFilterGroupBox.setChecked(False)

        # 2. Plot settings
        if "chSpacing" not in sigConfig:
            self.plotGroupBox.setChecked(False)
            return

        self.plotGroupBox.setChecked(True)
        self.chSpacingTextField.setText(lo.toString(sigConfig["chSpacing"]))
        if "minRange" in sigConfig and "maxRange" in sigConfig:
            self.rangeModeComboBox.setCurrentText("Manual")
            self.minRangeTextField.setText(lo.toString(sigConfig["minRange"]))
            self.maxRangeTextField.setText(lo.toString(sigConfig["maxRange"]))
            self.label12.setEnabled(True)
            self.minRangeTextField.setEnabled(True)
            self.label13.setEnabled(True)
            self.maxRangeTextField.setEnabled(True)
        else:
            self.rangeModeComboBox.setCurrentText("Automatic")
            self.label12.setEnabled(False)
            self.minRangeTextField.setEnabled(False)
            self.label13.setEnabled(False)
            self.maxRangeTextField.setEnabled(False)

        # 3. Ultrasound settings
        if "ultrasoundMode" in sigConfig:
            self.ultrasoundModeComboBox.setCurrentText(sigConfig["ultrasoundMode"])

            # Restore ultrasound display settings
            if "showRaw" in sigConfig:
                self.showRawCheckBox.setChecked(sigConfig["showRaw"])
            if "showFiltered" in sigConfig:
                self.showFilteredCheckBox.setChecked(sigConfig["showFiltered"])
            if "showEnvelope" in sigConfig:
                self.showEnvelopeCheckBox.setChecked(sigConfig["showEnvelope"])

            # Restore bandpass filter settings
            if "bandpassLow" in sigConfig and "bandpassHigh" in sigConfig:
                self.lowFreqSpinBox.setValue(
                    sigConfig["bandpassLow"] / 1e6
                )  # Convert from Hz to MHz
                self.highFreqSpinBox.setValue(sigConfig["bandpassHigh"] / 1e6)

            # Re-apply mode configuration after prefilling
            self._configureDisplayOptionsForMode(sigConfig["ultrasoundMode"])

    def _onUltrasoundModeChange(self, mode: str) -> None:
        """Detect if ultrasound mode has changed and adjust display options."""
        self._configureDisplayOptionsForMode(mode)

    def _configureDisplayOptionsForMode(self, mode: str) -> None:
        """Configure display options based on ultrasound mode (A-Mode vs M-Mode)."""
        if mode == "M-Mode":
            # For M-Mode: Only allow one option at a time
            # Disconnect first if already connected to avoid RuntimeWarning
            if self._mmode_handlers_connected:
                self.showRawCheckBox.toggled.disconnect(self._onMModeDisplayToggle)
                self.showFilteredCheckBox.toggled.disconnect(self._onMModeDisplayToggle)
                self.showEnvelopeCheckBox.toggled.disconnect(self._onMModeDisplayToggle)

            # Connect the handlers
            self.showRawCheckBox.toggled.connect(self._onMModeDisplayToggle)
            self.showFilteredCheckBox.toggled.connect(self._onMModeDisplayToggle)
            self.showEnvelopeCheckBox.toggled.connect(self._onMModeDisplayToggle)
            self._mmode_handlers_connected = True

            # Make sure at least one is checked
            if not any(
                [
                    self.showRawCheckBox.isChecked(),
                    self.showFilteredCheckBox.isChecked(),
                    self.showEnvelopeCheckBox.isChecked(),
                ]
            ):
                self.showRawCheckBox.setChecked(True)
        else:
            # For A-Mode: Allow multiple selections
            # Disconnect M-Mode handlers if they are connected
            if self._mmode_handlers_connected:
                self.showRawCheckBox.toggled.disconnect(self._onMModeDisplayToggle)
                self.showFilteredCheckBox.toggled.disconnect(self._onMModeDisplayToggle)
                self.showEnvelopeCheckBox.toggled.disconnect(self._onMModeDisplayToggle)
                self._mmode_handlers_connected = False

    def _onMModeDisplayToggle(self, checked: bool) -> None:
        """Handle M-Mode display toggle - ensure only one option is selected."""
        if not checked:
            # Don't allow unchecking if it's the only one checked
            if not any(
                [
                    self.showRawCheckBox.isChecked(),
                    self.showFilteredCheckBox.isChecked(),
                    self.showEnvelopeCheckBox.isChecked(),
                ]
            ):
                # Re-check the sender
                sender = self.sender()
                if sender:
                    sender.setChecked(True)
            return

        # If checked, uncheck the others
        sender = self.sender()
        if sender == self.showRawCheckBox:
            self.showFilteredCheckBox.setChecked(False)
            self.showEnvelopeCheckBox.setChecked(False)
        elif sender == self.showFilteredCheckBox:
            self.showRawCheckBox.setChecked(False)
            self.showEnvelopeCheckBox.setChecked(False)
        elif sender == self.showEnvelopeCheckBox:
            self.showRawCheckBox.setChecked(False)
            self.showFilteredCheckBox.setChecked(False)
