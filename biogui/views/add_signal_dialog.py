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

import datetime
import os

from PySide6.QtWidgets import QDialog, QFileDialog, QWidget
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtCore import QLocale

from biogui.ui.add_signal_dialog_ui import Ui_AddSignalDialog


class AddSignalDialog(QDialog, Ui_AddSignalDialog):
    """
    Dialog for adding a new signal to plot.

    Parameters
    ----------
    sourceName : str
        Name of the source.
    sigName : str
        Name of the signal.
    nCh : int
        Number of channels.
    fs : float
        Sampling frequency.
    parent : QWidget or None, default=None
        Parent widget.
    """

    def __init__(
        self,
        sourceName: str,
        sigName: str,
        nCh: int,
        fs: float,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self.buttonBox.accepted.connect(self._formValidationHandler)
        self.buttonBox.rejected.connect(self.close)
        self.filtTypeComboBox.currentTextChanged.connect(self._onFiltTypeChange)
        self.browseOutDirButton.clicked.connect(self._browseOutDir)

        self.sourceNameLabel.setText(sourceName)
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

        chSpacingValidator = QIntValidator(bottom=0, top=2147483647)
        self.chSpacingTextField.setValidator(chSpacingValidator)
        renderLenValidator = QIntValidator(bottom=1, top=8)
        self.renderLenTextField.setValidator(renderLenValidator)

        self._signalConfig = {
            "source": sourceName,
            "sigName": sigName,
            "nCh": nCh,
            "fs": fs,
        }
        self._isValid = False
        self._errMessage = ""

        self.destroyed.connect(self.deleteLater)

    @property
    def signalConfig(self) -> dict:
        """dict: Property for getting the dictionary with the signal configuration."""
        return self._signalConfig

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
            QFileDialog.ShowDirsOnly,
        )
        if outDirPath != "":
            self._signalConfig["filePath"] = outDirPath

            displayText = (
                outDirPath
                if len(outDirPath) <= 30
                else outDirPath[:13] + "..." + outDirPath[-14:]
            )
            self.outDirPathLabel.setText(displayText)
            self.outDirPathLabel.setToolTip(outDirPath)

    def _formValidationHandler(self) -> None:
        """Validate user input in the form."""
        lo = QLocale()

        nyq_fs = self._signalConfig["fs"] // 2

        # Check filtering settings
        if self.filteringGroupBox.isChecked():
            self._signalConfig["filtType"] = self.filtTypeComboBox.currentText()

            if not self.freq1TextField.hasAcceptableInput():
                self._isValid = False
                self._errMessage = 'The "Frequency 1" field is invalid.'
                return
            freq1 = lo.toFloat(self.freq1TextField.text())[0]

            if freq1 >= nyq_fs:
                self._isValid = False
                self._errMessage = "The 1st critical frequency cannot be higher than Nyquist frequency."
                return
            self._signalConfig["freqs"] = [freq1]

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
                self._signalConfig["freqs"].append(freq2)

            if not self.filtOrderTextField.hasAcceptableInput():
                self._isValid = False
                self._errMessage = 'The "filter order" field is invalid.'
                return
            self._signalConfig["filtOrder"] = lo.toInt(self.filtOrderTextField.text())[
                0
            ]

        # Check file saving settings
        if self.fileSavingGroupBox.isChecked():
            if "filePath" not in self._signalConfig.keys():
                self._isValid = False
                self._errMessage = "Select an output directory."
                return
            outFileName = self.fileNameTextField.text()
            if outFileName == "":
                outFileName = (
                    f"{self._signalConfig["sigName"]}_{datetime.datetime.now()}".replace(
                        " ", "_"
                    )
                    .replace(":", "-")
                    .replace(".", "-")
                )
            outFileName = f"{outFileName}.bin"
            self._signalConfig["filePath"] = os.path.join(
                self._signalConfig["filePath"], outFileName
            )

        # Plot settings
        if not self.chSpacingTextField.hasAcceptableInput():
            self._isValid = False
            self._errMessage = 'The "channel spacing" field is invalid.'
            return
        self._signalConfig["chSpacing"] = lo.toInt(self.chSpacingTextField.text())[0]
        if not self.renderLenTextField.hasAcceptableInput():
            self._isValid = False
            self._errMessage = 'The "render length" field is invalid.'
            return
        self._signalConfig["renderLen"] = lo.toInt(self.renderLenTextField.text())[0]

        self._isValid = True