# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Widget for configuring signals.
"""

from __future__ import annotations

from PySide6.QtCore import QLocale
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QWidget

from biogui.ui.ui_signal_config_widget import Ui_SignalConfigWidget


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
    extras : dict
        Dictionary with extra configuration.
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
        extras: dict,
        parent: QWidget | None = None,
        edit: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        # Track if M-mode display handlers are connected (to avoid disconnect warnings)
        self._mmode_handlers_connected = False

        self.sigNameLabel.setText(sigName)
        self.nChLabel.setText(str(nCh))

        if extras["type"] == "ultrasound":
            self.label3.setText("Pulse Repetition Frequency (PRF):")

            num_samples = extras.get("num_samples", 397)  # default value for wulpus
            prf = fs / num_samples if num_samples > 0 else fs
            self.freqLabel.setText(f"{self._formatRateForDisplay(prf)} Hz")
        else:
            self.freqLabel.setText(self._formatRateForDisplay(fs))

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
        freqValidator.setNotation(QDoubleValidator.Notation.StandardNotation)
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
        self._sigConfig: dict = {"fs": fs, "nCh": nCh, "extras": extras}

        # Pre-fill with provided configuration
        if edit:
            self._prefill(kwargs)

        self.filtTypeComboBox.currentTextChanged.connect(self._onFiltTypeChange)
        self.rangeModeComboBox.currentTextChanged.connect(self._onRangeModeChange)

        # Activate ultrasound dropdown only for ultrasound signals
        if extras.get("type") == "ultrasound":
            # Hide traditional filtering for ultrasound
            self.filterGroupBox.setVisible(False)
            self.notchFilterGroupBox.setVisible(False)

            # Enable ultrasound mode dropdown
            self.label14.setEnabled(True)
            self.ultrasoundModeComboBox.setEnabled(True)

            # Enable processing mode section
            self.label15.setEnabled(True)

            # Enable all processing mode options (as checkboxes)
            self.showRawCheckBox.setEnabled(True)
            self.showFilteredCheckBox.setEnabled(True)
            self.showEnvelopeCheckBox.setEnabled(True)

            # Get ADC sampling frequency
            adc_fs = extras.get("adc_sampling_freq", fs)
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

            # Connect checkbox changes to enable/disable frequency controls
            self.showFilteredCheckBox.toggled.connect(self._onUsProcessingModeChange)
            self.showEnvelopeCheckBox.toggled.connect(self._onUsProcessingModeChange)

            # Connect ultrasound mode change
            self.ultrasoundModeComboBox.currentTextChanged.connect(self._onUltrasoundModeChange)

            # Initialize state
            self._onUsProcessingModeChange()
            self._configureDisplayOptionsForMode(self.ultrasoundModeComboBox.currentText())

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

    def _formatRateForDisplay(self, value: float, precision: int = 2) -> str:
        """Format sampling-rate labels with at most {precision} decimal places."""
        return f"{value:.{precision}f}".rstrip("0").rstrip(".")

    def _onUsProcessingModeChange(self) -> None:
        """Enable/disable frequency controls based on ultrasound processing mode."""
        # Enable frequency controls only if filtered or envelope is selected
        needs_filter = (
            self.showFilteredCheckBox.isChecked() or self.showEnvelopeCheckBox.isChecked()
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

        extras = config.get("extras", {})
        if extras.get("type") == "ultrasound":
            # Ultrasound visualization mode
            config["ultrasoundMode"] = self.ultrasoundModeComboBox.currentText()

            # Display options for visualization
            config["showRaw"] = self.showRawCheckBox.isChecked()
            config["showFiltered"] = self.showFilteredCheckBox.isChecked()
            config["showEnvelope"] = self.showEnvelopeCheckBox.isChecked()

            # Bandpass is enabled if filtered or envelope is shown
            config["enableBandpass"] = (
                self.showFilteredCheckBox.isChecked() or self.showEnvelopeCheckBox.isChecked()
            )

            # Bandpass settings for plot mode
            config["bandpassLow"] = self.lowFreqSpinBox.value() * 1e6  # MHz to Hz
            config["bandpassHigh"] = self.highFreqSpinBox.value() * 1e6  # MHz to Hz

        return config

    def _onFiltTypeChange(self, filtType: str) -> None:
        """Detect if filter type has changed."""
        # Disable field for second frequency depending on the filter type
        if filtType in ("highpass", "lowpass"):
            self.freq2TextField.setEnabled(False)
            self.freq2TextField.clear()
        else:
            self.freq2TextField.setEnabled(True)

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
            self._sigConfig["notchFreq"] = lo.toFloat(self.notchFreqComboBox.currentText())[0]
            self._sigConfig["qFactor"] = lo.toFloat(self.qFactorTextField.text())[0]

        # 2. Plot settings
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

        # 3. Ultrasound-specific validation
        if self.ultrasoundModeComboBox.isEnabled():
            # Validate that at least one display option is selected
            if not any(
                [
                    self.showRawCheckBox.isChecked(),
                    self.showFilteredCheckBox.isChecked(),
                    self.showEnvelopeCheckBox.isChecked(),
                ]
            ):
                return (
                    False,
                    "At least one display option must be selected for ultrasound data.",
                )

            # For M-mode, validate that exactly one option is selected
            if self.ultrasoundModeComboBox.currentText() == "M-Mode":
                checked_count = sum(
                    [
                        self.showRawCheckBox.isChecked(),
                        self.showFilteredCheckBox.isChecked(),
                        self.showEnvelopeCheckBox.isChecked(),
                    ]
                )
                if checked_count > 1:
                    return (
                        False,
                        "M-Mode can only display one data type at a time (Raw, Filtered, or Envelope).",
                    )

        return True, ""

    def _prefill(self, kwargs: dict):
        """Pre-fill the form with the provided configuration."""
        lo = QLocale()

        # 1. Filtering settings:
        # 1.1. Butterworth filter
        if "filtType" in kwargs:
            self.filterGroupBox.setChecked(True)
            self.filtTypeComboBox.setCurrentText(kwargs["filtType"])
            freqs = kwargs["freqs"]
            self.freq1TextField.setText(lo.toString(freqs[0]))
            if len(freqs) == 2:
                self.freq2TextField.setEnabled(True)
                self.freq2TextField.setText(lo.toString(freqs[1]))
            self.filtOrderTextField.setText(lo.toString(kwargs["filtOrder"]))
        else:
            self.filterGroupBox.setChecked(False)

        # 1.2. Powerline noise filter
        if "notchFreq" in kwargs:
            self.notchFilterGroupBox.setChecked(True)
            self.notchFreqComboBox.setCurrentText(lo.toString(int(kwargs["notchFreq"])))
            self.qFactorTextField.setText(lo.toString(kwargs["qFactor"]))
        else:
            self.notchFilterGroupBox.setChecked(False)

        # 2. Plot settings
        if "chSpacing" not in kwargs:
            self.plotGroupBox.setChecked(False)
            return

        self.plotGroupBox.setChecked(True)
        self.chSpacingTextField.setText(lo.toString(kwargs["chSpacing"]))
        if "minRange" in kwargs and "maxRange" in kwargs:
            self.rangeModeComboBox.setCurrentText("Manual")
            self.minRangeTextField.setText(lo.toString(kwargs["minRange"]))
            self.maxRangeTextField.setText(lo.toString(kwargs["maxRange"]))
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
        if "ultrasoundMode" in kwargs:
            self.ultrasoundModeComboBox.setCurrentText(kwargs["ultrasoundMode"])

            # Restore ultrasound display settings
            if "showRaw" in kwargs:
                self.showRawCheckBox.setChecked(kwargs["showRaw"])
            if "showFiltered" in kwargs:
                self.showFilteredCheckBox.setChecked(kwargs["showFiltered"])
            if "showEnvelope" in kwargs:
                self.showEnvelopeCheckBox.setChecked(kwargs["showEnvelope"])

            # Restore bandpass filter settings
            if "bandpassLow" in kwargs and "bandpassHigh" in kwargs:
                self.lowFreqSpinBox.setValue(kwargs["bandpassLow"] / 1e6)  # Convert from Hz to MHz
                self.highFreqSpinBox.setValue(kwargs["bandpassHigh"] / 1e6)

            # Re-apply mode configuration after prefilling
            self._configureDisplayOptionsForMode(kwargs["ultrasoundMode"])

    def _onUltrasoundModeChange(self, mode: str) -> None:
        """Detect if ultrasound mode has changed and adjust display options."""
        self._configureDisplayOptionsForMode(mode)

    def _configureDisplayOptionsForMode(self, mode: str) -> None:
        """Configure display options based on ultrasound mode (A-mode vs M-mode)."""
        if mode == "M-Mode":
            # For M-mode: Only allow one option at a time
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
            # Disconnect M-mode handlers if they are connected
            if self._mmode_handlers_connected:
                self.showRawCheckBox.toggled.disconnect(self._onMModeDisplayToggle)
                self.showFilteredCheckBox.toggled.disconnect(self._onMModeDisplayToggle)
                self.showEnvelopeCheckBox.toggled.disconnect(self._onMModeDisplayToggle)
                self._mmode_handlers_connected = False

    def _onMModeDisplayToggle(self, checked: bool) -> None:
        """Handle M-mode display toggle - ensure only one option is selected."""
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
                    sender.setChecked(True)  # type: ignore
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
