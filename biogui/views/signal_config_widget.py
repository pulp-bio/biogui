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

        # Configure based on signal type
        if signal_type["type"] == "ultrasound":
            # Hide time-series filters
            self.filterGroupBox.setVisible(False)
            self.notchFilterGroupBox.setVisible(False)

            # Enable ultrasound mode dropdown
            self.label14.setEnabled(True)
            self.ultrasoundModeComboBox.setEnabled(True)

            # Enable processing mode section
            self.label15.setEnabled(True)

            # Create button group for exclusive selection
            self._usProcessingGroup = QButtonGroup(self)
            self._usProcessingGroup.addButton(self.showRawCheckBox, 0)
            self._usProcessingGroup.addButton(self.showFilteredCheckBox, 1)
            self._usProcessingGroup.addButton(self.showEnvelopeCheckBox, 2)

            # Enable all processing mode options
            self.showRawCheckBox.setEnabled(True)
            self.showFilteredCheckBox.setEnabled(True)
            self.showEnvelopeCheckBox.setEnabled(True)

            # Get ADC sampling frequency
            adc_fs = signal_type.get("adc_sampling_freq", fs)
            nyquist_mhz = adc_fs / 2 / 1e6

            # Configure frequency spinboxes ranges
            self.lowFreqSpinBox.setRange(0.1, nyquist_mhz)
            self.highFreqSpinBox.setRange(0.1, nyquist_mhz)

            # Set default values if not in edit mode
            if not edit:
                default_low = max(0.3, adc_fs * 0.1 / 1e6)  # 10% of Nyquist, min 300kHz
                default_high = adc_fs * 0.45 / 1e6  # 45% of Nyquist
                self.lowFreqSpinBox.setValue(default_low)
                self.highFreqSpinBox.setValue(default_high)

            # Connect processing mode changes to enable/disable frequency controls
            self._usProcessingGroup.buttonToggled.connect(
                self._onUsProcessingModeChange
            )

            # Connect ultrasound mode change
            self.ultrasoundModeComboBox.currentTextChanged.connect(
                self._onUltrasoundModeChange
            )

            # Initialize state
            self._onUsProcessingModeChange()
            self._configureDisplayOptionsForMode(
                self.ultrasoundModeComboBox.currentText()
            )

        else:
            # Time-series signal - disable ultrasound controls
            self.label14.setEnabled(False)
            self.ultrasoundModeComboBox.setEnabled(False)
            self.label15.setEnabled(False)
            self.showRawCheckBox.setEnabled(False)
            self.showFilteredCheckBox.setEnabled(False)
            self.showEnvelopeCheckBox.setEnabled(False)
            self.lowFreqSpinBox.setEnabled(False)
            self.highFreqSpinBox.setEnabled(False)

    def _onUsProcessingModeChange(self) -> None:
        """Enable/disable frequency controls based on ultrasound processing mode."""
        # Enable frequency controls only if filtered or envelope is selected
        needs_filter = (
            self.showFilteredCheckBox.isChecked()
            or self.showEnvelopeCheckBox.isChecked()
        )

        self.lowFreqSpinBox.setEnabled(needs_filter)
        self.highFreqSpinBox.setEnabled(needs_filter)

    @property
    def sigName(self) -> str:
        """str: Property for getting the signal name."""
        return self._sigName

    @property
    def sigConfig(self) -> dict:
        """
        dict: Property for getting the dictionary with the signal configuration.
        """
        config = self._sigConfig.copy()

        signal_type = config.get("signal_type", {})

        if signal_type.get("type") == "ultrasound":
            # Ultrasound processing configuration

            # Determine processing mode based on radio button selection
            if self.showEnvelopeCheckBox.isChecked():
                processing_mode = "envelope"
            elif self.showFilteredCheckBox.isChecked():
                processing_mode = "filtered"
            else:  # showRawCheckBox
                processing_mode = "raw"

            # Configure ultrasound filter
            if processing_mode != "raw":
                config["ultrasoundFilterConfig"] = {
                    "processingMode": processing_mode,
                    "lowCutoff": self.lowFreqSpinBox.value() * 1e6,  # MHz to Hz
                    "highCutoff": self.highFreqSpinBox.value() * 1e6,  # MHz to Hz
                    "transWidth": 0.2e6,  # 200 kHz transition width
                    "nTaps": 31,  # Number of filter taps
                }
            else:
                config["ultrasoundFilterConfig"] = {
                    "processingMode": "raw",
                }

            # Ultrasound visualization mode
            config["ultrasoundMode"] = self.ultrasoundModeComboBox.currentText()

            # Display options for visualization (keep existing behavior)
            config["showRaw"] = self.showRawCheckBox.isChecked()
            config["showFiltered"] = self.showFilteredCheckBox.isChecked()
            config["showEnvelope"] = self.showEnvelopeCheckBox.isChecked()

            # Bandpass settings for plot mode (for backwards compatibility)
            config["bandpassLow"] = self.lowFreqSpinBox.value() * 1e6
            config["bandpassHigh"] = self.highFreqSpinBox.value() * 1e6

        return config

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

        signal_type = self._sigConfig.get("signal_type", {})

        if signal_type.get("type") == "ultrasound":
            # Validate ultrasound configuration

            # Check if at least one processing mode is selected
            if not (
                self.showRawCheckBox.isChecked()
                or self.showFilteredCheckBox.isChecked()
                or self.showEnvelopeCheckBox.isChecked()
            ):
                return False, "Please select a processing mode for ultrasound data."

            # Validate frequency settings if filtering is enabled
            if (
                self.showFilteredCheckBox.isChecked()
                or self.showEnvelopeCheckBox.isChecked()
            ):
                low_freq = self.lowFreqSpinBox.value()
                high_freq = self.highFreqSpinBox.value()

                if low_freq >= high_freq:
                    return (
                        False,
                        "Low cutoff frequency must be less than high cutoff frequency.",
                    )

                # Check if frequencies are reasonable
                adc_fs = signal_type.get("adc_sampling_freq", self._sigConfig["fs"])
                nyquist_mhz = adc_fs / 2 / 1e6

                if high_freq > nyquist_mhz:
                    return (
                        False,
                        f"High cutoff frequency cannot exceed Nyquist frequency ({nyquist_mhz:.2f} MHz).",
                    )

            # Store configuration
            if self.showEnvelopeCheckBox.isChecked():
                processing_mode = "envelope"
            elif self.showFilteredCheckBox.isChecked():
                processing_mode = "filtered"
            else:
                processing_mode = "raw"

            if processing_mode != "raw":
                self._sigConfig["ultrasoundFilterConfig"] = {
                    "processingMode": processing_mode,
                    "lowCutoff": self.lowFreqSpinBox.value() * 1e6,
                    "highCutoff": self.highFreqSpinBox.value() * 1e6,
                    "transWidth": 0.2e6,
                    "nTaps": 31,
                }
            else:
                self._sigConfig["ultrasoundFilterConfig"] = {
                    "processingMode": "raw",
                }

            self._sigConfig["ultrasoundMode"] = (
                self.ultrasoundModeComboBox.currentText()
            )
            self._sigConfig["showRaw"] = self.showRawCheckBox.isChecked()
            self._sigConfig["showFiltered"] = self.showFilteredCheckBox.isChecked()
            self._sigConfig["showEnvelope"] = self.showEnvelopeCheckBox.isChecked()
            self._sigConfig["bandpassLow"] = self.lowFreqSpinBox.value() * 1e6
            self._sigConfig["bandpassHigh"] = self.highFreqSpinBox.value() * 1e6

        else:
            # Time-series validation (original code)
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
                self._sigConfig["filtOrder"] = lo.toInt(self.filtOrderTextField.text())[
                    0
                ]

            # 1.2. Notch filter
            if self.notchFilterGroupBox.isChecked():
                if not self.qFactorTextField.hasAcceptableInput():
                    return False, 'The "quality factor" field is invalid.'

                self._sigConfig["notchFreq"] = lo.toFloat(
                    self.notchFreqComboBox.currentText()
                )[0]
                self._sigConfig["qFactor"] = lo.toInt(self.qFactorTextField.text())[0]

        # 2. Plot settings (common for both signal types)
        if self.plotGroupBox.isChecked():
            if self._sigConfig["nCh"] > 1:
                if not self.chSpacingTextField.hasAcceptableInput():
                    return False, 'The "channel spacing" field is invalid.'
                self._sigConfig["chSpacing"] = lo.toFloat(
                    self.chSpacingTextField.text()
                )[0]
            else:
                self._sigConfig["chSpacing"] = 0

            # 2.1. Range
            if self.rangeModeComboBox.currentText() == "Manual":
                if not self.minRangeTextField.hasAcceptableInput():
                    return False, 'The "minimum range" field is invalid.'
                if not self.maxRangeTextField.hasAcceptableInput():
                    return False, 'The "maximum range" field is invalid.'

                minRange = lo.toFloat(self.minRangeTextField.text())[0]
                maxRange = lo.toFloat(self.maxRangeTextField.text())[0]
                if maxRange <= minRange:
                    return (
                        False,
                        "The maximum range cannot be lower than the minimum range.",
                    )

                self._sigConfig["minRange"] = minRange
                self._sigConfig["maxRange"] = maxRange

        return True, ""

    def _prefill(self, kwargs: dict) -> None:
        """Pre-fill the form with provided configuration."""
        lo = QLocale()

        signal_type = self._sigConfig.get("signal_type", {})

        if signal_type.get("type") == "ultrasound":
            # Prefill ultrasound-specific configuration
            us_config = kwargs.get("ultrasoundFilterConfig", {})
            processing_mode = us_config.get("processingMode", "raw")

            # Set processing mode radio button
            if processing_mode == "envelope":
                self.showEnvelopeCheckBox.setChecked(True)
            elif processing_mode == "filtered":
                self.showFilteredCheckBox.setChecked(True)
            else:
                self.showRawCheckBox.setChecked(True)

            # Prefill frequencies
            if "lowCutoff" in us_config:
                self.lowFreqSpinBox.setValue(us_config["lowCutoff"] / 1e6)  # Hz to MHz
            if "highCutoff" in us_config:
                self.highFreqSpinBox.setValue(
                    us_config["highCutoff"] / 1e6
                )  # Hz to MHz

            # Prefill ultrasound visualization mode
            if "ultrasoundMode" in kwargs:
                idx = self.ultrasoundModeComboBox.findText(kwargs["ultrasoundMode"])
                if idx >= 0:
                    self.ultrasoundModeComboBox.setCurrentIndex(idx)

            # Prefill display options (backwards compatibility)
            if "showRaw" in kwargs:
                self.showRawCheckBox.setChecked(kwargs["showRaw"])
            if "showFiltered" in kwargs:
                self.showFilteredCheckBox.setChecked(kwargs["showFiltered"])
            if "showEnvelope" in kwargs:
                self.showEnvelopeCheckBox.setChecked(kwargs["showEnvelope"])

            # Prefill bandpass settings (backwards compatibility)
            if "bandpassLow" in kwargs:
                self.lowFreqSpinBox.setValue(kwargs["bandpassLow"] / 1e6)
            if "bandpassHigh" in kwargs:
                self.highFreqSpinBox.setValue(kwargs["bandpassHigh"] / 1e6)

        else:
            # Time-series prefill (original code)
            # 1. Filtering
            # 1.1. Butterworth filter
            if "filtType" in kwargs:
                self.filterGroupBox.setChecked(True)
                self.filtTypeComboBox.setCurrentText(kwargs["filtType"])

                freqs = kwargs["freqs"]
                self.freq1TextField.setText(lo.toString(freqs[0]))
                if len(freqs) > 1:
                    self.freq2TextField.setText(lo.toString(freqs[1]))

                self.filtOrderTextField.setText(str(kwargs["filtOrder"]))

            # 1.2. Notch filter
            if "notchFreq" in kwargs:
                self.notchFilterGroupBox.setChecked(True)
                self.notchFreqComboBox.setCurrentText(str(int(kwargs["notchFreq"])))
                self.qFactorTextField.setText(str(kwargs["qFactor"]))

        # 2. Plot settings (common for both)
        if "chSpacing" in kwargs:
            self.plotGroupBox.setChecked(True)
            if self._sigConfig["nCh"] > 1:
                self.chSpacingTextField.setText(lo.toString(kwargs["chSpacing"]))

            # 2.1. Range
            if "minRange" in kwargs:
                self.rangeModeComboBox.setCurrentText("Manual")
                self.minRangeTextField.setText(lo.toString(kwargs["minRange"]))
                self.maxRangeTextField.setText(lo.toString(kwargs["maxRange"]))

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
