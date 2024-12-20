"""
Dialog to add a new data source.


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

import importlib.util
import os

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox, QWidget

from biogui import data_sources
from biogui.ui.add_data_source_dialog_ui import Ui_AddDataSourceDialog
from biogui.utils import InterfaceModule


def _loadInterfaceFromFile(filePath: str) -> tuple[InterfaceModule | None, str]:
    """
    Load an interface from a Python file.

    Parameters
    ----------
    filePath : str
        Path to Python file.

    Returns
    -------
    InterfaceModule or None
        InterfaceModule object, or None if the module is not valid.
    str
        Error message.
    """
    # Remove ".py" extension and get file name
    moduleName = filePath[:-3].split("/")[-1]

    # Load module
    spec = importlib.util.spec_from_file_location(moduleName, filePath)
    if spec is None or spec.loader is None:
        return None, "The selected file is not a valid Python module."

    module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(module)
    except ImportError:
        return None, "Cannot import the selected Python module."

    if not hasattr(module, "packetSize"):
        return (
            None,
            'The selected Python module does not contain a "packetSize" constant.',
        )
    if not hasattr(module, "startSeq"):
        return (
            None,
            'The selected Python module does not contain a "startSeq" variable.',
        )
    if not hasattr(module, "stopSeq"):
        return (
            None,
            'The selected Python module does not contain a "stopSeq" variable.',
        )
    if not hasattr(module, "sigInfo"):
        return (
            None,
            'The selected Python module does not contain a "sigInfo" variable.',
        )
    if not hasattr(module, "decodeFn"):
        return (
            None,
            'The selected Python module does not contain a "decodeFn" function.',
        )

    return (
        InterfaceModule(
            packetSize=module.packetSize,
            startSeq=module.startSeq,
            stopSeq=module.stopSeq,
            sigInfo=module.sigInfo,
            decodeFn=module.decodeFn,
        ),
        "",
    )


class AddDataSourceDialog(QDialog, Ui_AddDataSourceDialog):
    """
    Dialog for adding a new data source.

    Parameters
    ----------
    edit : bool
        Whether to open the dialog in edit mode.
    parent : QWidget or None, default=None
        Parent widget.
    kwargs : dict
        Optional keyword arguments for pre-filling the form, namely:
        - "filtType": the filter type (optional);
        - "freqs": list with the cut-off frequencies (optional);
        - "filtOrder" the filter order (optional);
        - "chSpacing": the channel spacing;
        - "showYAxis": whether to show the Y axis (optional);
        - "minRange": minimum of the Y range (optional);
        - "maxRange": maximum of the Y range (optional).

    Attributes
    ----------
    _configWidget : ConfigWidget
        Widget for data source configuration.
    _outDirPath : str or None
        Path to the output directory.
    """

    def __init__(
        self, edit: bool, parent: QWidget | None = None, **kwargs: dict
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)
        self.sourceComboBox.addItems(
            list(map(lambda sourceType: sourceType.value, data_sources.DataSourceType))
        )

        self.buttonBox.accepted.connect(self._addSourceHandler)
        self.buttonBox.rejected.connect(self.close)
        self.destroyed.connect(self.deleteLater)
        self.browseInterfaceModuleButton.clicked.connect(self._browseInterfaceModule)
        self.sourceComboBox.currentTextChanged.connect(self._onSourceChange)
        self.browseOutDirButton.clicked.connect(self._browseOutDir)

        # Source type (default is serial port)
        self._configWidget = data_sources.getConfigWidget(
            data_sources.DataSourceType.SERIAL, self
        )
        self.sourceConfigContainer.addWidget(self._configWidget)

        self._dataSourceConfig = {}
        self._outDirPath = None
        self._isValid = False
        self._errMessage = ""

        # Pre-fill with provided configuration
        self.browseInterfaceModuleButton.setEnabled(not edit)
        if edit:
            self._prefill(kwargs)

    @property
    def dataSourceConfig(self) -> dict:
        """
        dict: Property for getting the data source configuration, namely:
        - "dataSourceType": the data source type;
        - "interfacePath": the interface module;
        - "interfaceModule": the interface module;
        - the data source type-specific configuration parameters;
        - "filePath": the file path (optional).
        """
        return self._dataSourceConfig

    @property
    def isValid(self) -> bool:
        """bool: Property representing whether the form is valid."""
        return self._isValid

    @property
    def errMessage(self) -> str:
        """str: Property for getting the error message if the form is not valid."""
        return self._errMessage

    def _browseInterfaceModule(self) -> None:
        """Browse files to select the module containing the decode function."""
        interfacePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Python module containing the decode function",
            filter="*.py",
        )
        if interfacePath != "":
            # Load interface module
            interfaceModule, errMessage = _loadInterfaceFromFile(interfacePath)
            if interfaceModule is None:
                QMessageBox.critical(
                    self,
                    "Invalid Python file",
                    errMessage,
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                return
            self._dataSourceConfig["interfacePath"] = interfacePath
            self._dataSourceConfig["interfaceModule"] = interfaceModule

            # Limit display text to 40 characters
            displayText = (
                interfacePath
                if len(interfacePath) <= 40
                else interfacePath[:17] + "..." + interfacePath[-20:]
            )
            self.interfaceModulePathLabel.setText(displayText)
            self.interfaceModulePathLabel.setToolTip(interfacePath)

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

            # Limit display text to 40 characters
            displayText = (
                outDirPath
                if len(outDirPath) <= 40
                else outDirPath[:17] + "..." + outDirPath[-20:]
            )
            self.outDirPathLabel.setText(displayText)
            self.outDirPathLabel.setToolTip(outDirPath)

    def _onSourceChange(self) -> None:
        """Detect if source type has changed."""
        # Clear container
        self.sourceConfigContainer.removeWidget(self._configWidget)
        self._configWidget.deleteLater()

        # Add new widget
        self._configWidget = data_sources.getConfigWidget(
            data_sources.DataSourceType(self.sourceComboBox.currentText()), self
        )
        self.sourceConfigContainer.addWidget(self._configWidget)

    def _addSourceHandler(self) -> None:
        """Validate user input in the form."""
        # Interface module
        if "interfaceModule" not in self._dataSourceConfig:
            self._isValid = False
            self._errMessage = "No interface was provided."
            return

        # Data source type
        if self.sourceComboBox.currentText() == "":
            self._isValid = False
            self._errMessage = 'The "source" field is invalid.'
            return

        # Data source-specific config
        configResult = self._configWidget.validateConfig()
        if not configResult.isValid:
            self._isValid = False
            self._errMessage = configResult.errMessage
            return
        self._dataSourceConfig["dataSourceType"] = configResult.dataSourceType
        self._dataSourceConfig |= configResult.dataSourceConfig

        # File saving
        if self.fileSavingGroupBox.isChecked():
            if self._outDirPath is None:
                self._isValid = False
                self._errMessage = "Select an output directory."
                return
            outFileName = self.fileNameTextField.text()
            if outFileName == "":
                self._isValid = False
                self._errMessage = "Insert a file name."
                return
            self._dataSourceConfig["filePath"] = os.path.join(
                self._outDirPath, outFileName
            )

        self._isValid = True

    def _prefill(self, dataSourceConfig: dict):
        """Pre-fill the form with the provided configuration."""
        # Interface module
        self.interfaceModulePathLabel.setText(dataSourceConfig["interfacePath"])
        self._dataSourceConfig["interfacePath"] = dataSourceConfig["interfacePath"]
        self._dataSourceConfig["interfaceModule"] = dataSourceConfig["interfaceModule"]

        # Data source type
        self.sourceComboBox.setCurrentText(self._dataSourceConfig["dataSourceType"])

        # File saving
        if "filePath" in dataSourceConfig:
            self.fileSavingGroupBox.setChecked(True)
            outDirPath, fileName = os.path.split(dataSourceConfig["filePath"])
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
