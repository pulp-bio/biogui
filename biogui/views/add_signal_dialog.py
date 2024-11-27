"""
Dialog to add a new signal.


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

import os

from PySide6.QtCore import QLocale
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QDialog, QFileDialog, QWidget

from biogui.ui.add_signal_dialog_ui import Ui_AddSignalDialog


class AddSignalDialog(QDialog, Ui_AddSignalDialog):
    """
    Dialog for adding a new signal to plot.

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
        Optional keyword arguments for pre-filling the form, namely:
        - "filtType": the filter type (optional);
        - "freqs": list with the cut-off frequencies (optional);
        - "filtOrder" the filter order (optional);
        - "filePath": the file path (optional);
        - "chSpacing": the channel spacing;
        - "renderLengthS": the render length.

    Attributes
    ----------
    _outDirPath : str or None
        Path to the output directory.
    """

    def __init__(
        self,
        sigName: str,
        fs: float,
        nCh: int,
        parent: QWidget | None = None,
        editMode: bool = False,
        **kwargs: dict,
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self.buttonBox.accepted.connect(self._formValidationHandler)
        self.buttonBox.rejected.connect(self.close)
        self.filtTypeComboBox.currentTextChanged.connect(self._onFiltTypeChange)
        self.browseOutDirButton.clicked.connect(self._browseOutDir)
        self.rangeModeComboBox.currentIndexChanged.connect(self._onRangeModeChange)
        if nCh == 1:
            self.label12.setEnabled(False)
            self.chSpacingTextField.setEnabled(False)
            self.chSpacingTextField.setText("0")

        self.sigNameLabel.setText(sigName)
        self.nChLabel.setText(str(nCh))
        self.freqLabel.setText(str(fs))

        # Validation rules
        nDec = 3
        minFreq, maxFreq = 1 * 10 ** (-nDec), 20_000.0
        minOrd, maxOrd = 1, 20

        self.freq1TextField.setToolTip(
            f"Float between {minFreq:.3f} and {maxFreq / 2:.3f}"
        )
        self.freq2TextField.setToolTip(
            f"Float between {minFreq:.3f} and {maxFreq / 2:.3f}"
        )
        freqValidator = QDoubleValidator(bottom=minFreq, top=maxFreq / 2, decimals=nDec)
        freqValidator.setNotation(QDoubleValidator.StandardNotation)  # type: ignore
        self.freq1TextField.setValidator(freqValidator)
        self.freq2TextField.setValidator(freqValidator)

        self.filtOrderTextField.setToolTip(f"Integer between {minOrd} and {maxOrd}")
        orderValidator = QIntValidator(bottom=minOrd, top=maxOrd)
        self.filtOrderTextField.setValidator(orderValidator)

        renderLenValidator = QIntValidator(bottom=1, top=10)
        self.renderLenTextField.setValidator(renderLenValidator)
        chSpacingValidator = QIntValidator(bottom=0, top=2147483647)
        self.chSpacingTextField.setValidator(chSpacingValidator)
        rangeValidator = QDoubleValidator(bottom=-1e308, top=1e308, decimals=nDec)
        self.minRangeTextField.setValidator(rangeValidator)
        self.maxRangeTextField.setValidator(rangeValidator)

        self._sigConfig = {"fs": fs, "nCh": nCh}
        self._outDirPath = None
        self._isValid = False
        self._errMessage = ""

        self.destroyed.connect(self.deleteLater)

        # Pre-fill with provided configuration
        if editMode:
            self._prefill(kwargs)

    @property
    def sigConfig(self) -> dict:
        """
        dict: Property for getting the dictionary with the signal configuration, namely:
        - "fs": the sampling frequency;
        - "nCh": the number of channels;
        - "filtType": the filter type (optional);
        - "freqs": list with the cut-off frequencies (optional);
        - "filtOrder" the filter order (optional);
        - "filePath": the file path (optional);
        - "chSpacing": the channel spacing;
        - "renderLengthS": the render length.
        """
        return self._sigConfig

    @property
    def isValid(self) -> bool:
        """bool: Property representing whether the form is valid."""
        return self._isValid

    @property
    def errMessage(self) -> str:
        """str: Property for getting the error message if the form is not valid."""
        return self._errMessage

    def _onFiltTypeChange(self) -> None:
        """Detect if filter type has changed."""
        filtType = self.filtTypeComboBox.currentText()
        # Disable field for second frequency depending on the filter type
        if filtType in ("highpass", "lowpass"):
            self.freq2TextField.setEnabled(False)
            self.freq2TextField.clear()
        else:
            self.freq2TextField.setEnabled(True)

    def _browseOutDir(self) -> None:
        """Browse directory where the data will be saved."""
        outDirPath = QFileDialog.getExistingDirectory(
            self,
            "Select destination directory",
            os.getcwd(),
            QFileDialog.ShowDirsOnly,  # type: ignore
        )
        if outDirPath != "":
            self._outDirPath = outDirPath

            displayText = (
                outDirPath
                if len(outDirPath) <= 30
                else outDirPath[:13] + "..." + outDirPath[-14:]
            )
            self.outDirPathLabel.setText(displayText)
            self.outDirPathLabel.setToolTip(outDirPath)

    def _onRangeModeChange(self) -> None:
        """Detect if range mode has changed"""
        if self.rangeModeComboBox.currentText() == "Automatic":
            self.label14.setEnabled(False)
            self.minRangeTextField.setEnabled(False)
            self.label15.setEnabled(False)
            self.maxRangeTextField.setEnabled(False)
        else:
            self.label14.setEnabled(True)
            self.minRangeTextField.setEnabled(True)
            self.label15.setEnabled(True)
            self.maxRangeTextField.setEnabled(True)

    def _formValidationHandler(self) -> None:
        """Validate user input in the form."""
        lo = QLocale()

        nyq_fs = self._sigConfig["fs"] // 2

        # Check filtering settings
        if self.filteringGroupBox.isChecked():
            if not self.freq1TextField.hasAcceptableInput():
                self._isValid = False
                self._errMessage = 'The "Frequency 1" field is invalid.'
                return
            freq1 = lo.toFloat(self.freq1TextField.text())[0]

            if freq1 >= nyq_fs:
                self._isValid = False
                self._errMessage = "The 1st critical frequency cannot be higher than Nyquist frequency."
                return
            freqs = [freq1]

            if self.freq2TextField.isEnabled():
                if not self.freq2TextField.hasAcceptableInput():
                    self._isValid = False
                    self._errMessage = 'The "Frequency 2" field is invalid.'
                    return
                freq2 = lo.toFloat(self.freq2TextField.text())[0]

                if freq2 >= nyq_fs:
                    self._isValid = False
                    self._errMessage = "The 2nd critical frequency cannot be higher than Nyquist frequency."
                    return
                if freq2 <= freq1:
                    self._isValid = False
                    self._errMessage = "The 2nd critical frequency cannot be lower than the 1st critical frequency."
                    return
                freqs.append(freq2)

            if not self.filtOrderTextField.hasAcceptableInput():
                self._isValid = False
                self._errMessage = 'The "filter order" field is invalid.'
                return

            self._sigConfig["filtType"] = self.filtTypeComboBox.currentText()
            self._sigConfig["freqs"] = freqs
            self._sigConfig["filtOrder"] = lo.toInt(self.filtOrderTextField.text())[0]

        # Check file saving settings
        if self.fileSavingGroupBox.isChecked():
            if self._outDirPath is None:
                self._isValid = False
                self._errMessage = "Select an output directory."
                return
            outFileName = self.fileNameTextField.text()
            if outFileName == "":
                outFileName = self.sigNameLabel.text()
            self._sigConfig["filePath"] = os.path.join(self._outDirPath, outFileName)

        # Check plot settings
        if self.plotGroupBox.isChecked():
            if not self.renderLenTextField.hasAcceptableInput():
                self._isValid = False
                self._errMessage = 'The "render length" field is invalid.'
                return
            self._sigConfig["renderLengthS"] = lo.toInt(self.renderLenTextField.text())[
                0
            ]
            if not self.chSpacingTextField.hasAcceptableInput():
                self._isValid = False
                self._errMessage = 'The "channel spacing" field is invalid.'
                return
            self._sigConfig["chSpacing"] = lo.toInt(self.chSpacingTextField.text())[0]
            self._sigConfig["showYAxis"] = self.showYAxisCheckBox.isChecked()
            if self.rangeModeComboBox.currentText() == "Manual":
                if not self.minRangeTextField.hasAcceptableInput():
                    self._isValid = False
                    self._errMessage = 'The "minimum range" field is invalid.'
                    return
                minRange = lo.toFloat(self.minRangeTextField.text())[0]
                if not self.maxRangeTextField.hasAcceptableInput():
                    self._isValid = False
                    self._errMessage = 'The "maximum range" field is invalid.'
                    return
                maxRange = lo.toFloat(self.maxRangeTextField.text())[0]
                if maxRange <= minRange:
                    self._isValid = False
                    self._errMessage = (
                        "The maximum range cannot be lower than the minimum range."
                    )
                    return

                self._sigConfig["minRange"] = minRange
                self._sigConfig["maxRange"] = maxRange

        self._isValid = True

    def _prefill(self, sigConfig):
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
            self.fileSavingGroupBox.setChecked(False)

        if "filePath" in sigConfig:
            self.fileSavingGroupBox.setChecked(True)
            outDirPath, fileName = os.path.split(sigConfig["filePath"])
            self._outDirPath = outDirPath
            # Adjust display text
            displayText = (
                outDirPath
                if len(outDirPath) <= 30
                else outDirPath[:13] + "..." + outDirPath[-14:]
            )
            self.outDirPathLabel.setText(displayText)
            self.outDirPathLabel.setToolTip(outDirPath)
            self.fileNameTextField.setText(fileName)
        else:
            self.fileSavingGroupBox.setChecked(False)

        if "renderLengthS" in sigConfig:
            self.plotGroupBox.setChecked(True)
            self.renderLenTextField.setText(lo.toString(sigConfig["renderLengthS"]))
            self.chSpacingTextField.setText(lo.toString(sigConfig["chSpacing"]))
            self.showYAxisCheckBox.setChecked(sigConfig["showYAxis"])
            if "minRange" in sigConfig and "maxRange" in sigConfig:
                self.rangeModeComboBox.setCurrentText("Manual")
                self.minRangeTextField.setText(lo.toString(sigConfig["minRange"]))
                self.maxRangeTextField.setText(lo.toString(sigConfig["maxRange"]))
                self.label14.setEnabled(True)
                self.minRangeTextField.setEnabled(True)
                self.label15.setEnabled(True)
                self.maxRangeTextField.setEnabled(True)
            else:
                self.rangeModeComboBox.setCurrentText("Automatic")
                self.label14.setEnabled(False)
                self.minRangeTextField.setEnabled(False)
                self.label15.setEnabled(False)
                self.maxRangeTextField.setEnabled(False)
        else:
            self.plotGroupBox.setChecked(False)
