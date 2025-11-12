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
from sys import platform

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox, QWidget

from biogui import data_sources
from biogui.ui.data_source_config_dialog_ui import Ui_DataSourceConfigDialog
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
    if not isinstance(module.packetSize, int) or module.packetSize <= 0:
        return None, "The packet size must be a positive integer."

    for sigName in module.sigInfo.keys():
        if sigName in ("acq_ts", "trigger"):
            return None, '"acq_ts" and "trigger" are reserved signal names.'

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


class DataSourceConfigDialog(QDialog, Ui_DataSourceConfigDialog):
    """
    Dialog for adding a new data source.

    Parameters
    ----------
    dataSourceType : DataSourceType, default=None
        Data source type.
    parent : QWidget or None, default=None
        Parent widget.
    kwargs : dict
        Optional keyword arguments for pre-filling the form, namely:
        - "dataSourceType": the data source type;
        - "interfacePath": the interface module;
        - "interfaceModule": the interface module;
        - the data source type-specific configuration parameters;
        - "filePath": the file path (optional).

    Attributes
    ----------
    _configWidget : DataSourceConfigWidget
        Widget for data source configuration.
    _outDirPath : str or None
        Path to the output directory.
    """

    def __init__(
        self,
        dataSourceType: data_sources.DataSourceType | None = None,
        parent: QWidget | None = None,
        **kwargs: dict,
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        # Create data source configuration widget
        dataSources = list(
            map(lambda sourceType: sourceType.value, data_sources.DataSourceType)
        )
        if dataSourceType is None:
            dataSourceType = data_sources.DataSourceType(dataSources[0])
        self.dataSourceComboBox.addItems(dataSources)
        self.dataSourceComboBox.setCurrentText(dataSourceType.value)
        self._configWidget = data_sources.getConfigWidget(dataSourceType, self)
        self.dataSourceConfigContainer.addWidget(self._configWidget)
        self._updateTabOrder()

        # Disable Unix socket option on Windows
        if platform == "win32":
            index = self.dataSourceComboBox.findText("Unix socket")
            self.dataSourceComboBox.model().item(index).setEnabled(False)  # type: ignore

        self.buttonBox.accepted.connect(self._validateDialog)
        self.buttonBox.rejected.connect(self.reject)
        self.browseInterfaceModuleButton.clicked.connect(self._browseInterfaceModule)
        self.dataSourceComboBox.currentTextChanged.connect(self._onDataSourceChange)
        self.browseOutDirButton.clicked.connect(self._browseOutDir)

        self._dataSourceConfig = {}
        self._outDirPath = None

        # Pre-fill with provided configuration
        if kwargs:
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

    def _updateTabOrder(self) -> None:
        """Update the tab order when the data source widget changes."""
        self.setTabOrder(self.browseInterfaceModuleButton, self.dataSourceComboBox)

        tabOrderedFields = self._configWidget.getFieldsInTabOrder()
        if not tabOrderedFields:
            self.setTabOrder(self.dataSourceComboBox, self.fileSavingGroupBox)
            return

        self.setTabOrder(self.dataSourceComboBox, tabOrderedFields[0])
        for i in range(1, len(tabOrderedFields)):
            self.setTabOrder(tabOrderedFields[i - 1], tabOrderedFields[i])
        self.setTabOrder(tabOrderedFields[-1], self.fileSavingGroupBox)

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

            self.interfaceModulePathLabel.setText(interfacePath)

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

            self.outDirPathLabel.setText(outDirPath)

    def _onDataSourceChange(self, dataSourceType: str) -> None:
        """Detect if data source type has changed."""
        # Clear container
        self.dataSourceConfigContainer.removeWidget(self._configWidget)
        self._configWidget.deleteLater()

        # Add new widget
        self._configWidget = data_sources.getConfigWidget(
            data_sources.DataSourceType(dataSourceType), parent=self
        )
        self.dataSourceConfigContainer.addWidget(self._configWidget)

        # Update tab order
        self._updateTabOrder()

    def _validateDialog(self) -> None:
        """Validate user input in the form."""
        # 1. Interface module
        if "interfaceModule" not in self._dataSourceConfig:
            QMessageBox.critical(
                self,
                "Invalid signal configuration",
                "No interface was provided.",
                buttons=QMessageBox.Retry,  # type: ignore
                defaultButton=QMessageBox.Retry,  # type: ignore
            )
            return

        # 2. Data source-specific config
        if self.dataSourceComboBox.currentText() == "":
            QMessageBox.critical(
                self,
                "Invalid signal configuration",
                'The "source" field is invalid.',
                buttons=QMessageBox.Retry,  # type: ignore
                defaultButton=QMessageBox.Retry,  # type: ignore
            )
            return
        configResult = self._configWidget.validateConfig()
        if not configResult.isValid:
            QMessageBox.critical(
                self,
                "Invalid signal configuration",
                configResult.errMessage,
                buttons=QMessageBox.Retry,  # type: ignore
                defaultButton=QMessageBox.Retry,  # type: ignore
            )
            return
        self._dataSourceConfig["dataSourceType"] = configResult.dataSourceType
        self._dataSourceConfig |= configResult.dataSourceConfig

        # 3. File saving
        if self.fileSavingGroupBox.isChecked():
            if self._outDirPath is None:
                QMessageBox.critical(
                    self,
                    "Invalid signal configuration",
                    "Select an output directory.",
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                return
            outFileName = self.fileNameTextField.text()
            if outFileName == "":
                QMessageBox.critical(
                    self,
                    "Invalid signal configuration",
                    "Insert a file name.",
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                return
            self._dataSourceConfig["filePath"] = os.path.join(
                self._outDirPath, outFileName
            )

        self.accept()

    def _prefill(self, dataSourceConfig: dict):
        """Pre-fill the form with the provided configuration."""
        # 1. Interface module
        interfacePath = dataSourceConfig["interfacePath"]
        self._dataSourceConfig["interfacePath"] = interfacePath
        self._dataSourceConfig["interfaceModule"] = dataSourceConfig["interfaceModule"]
        displayText = (
            interfacePath
            if len(interfacePath) <= 40
            else interfacePath[:17] + "..." + interfacePath[-20:]
        )
        self.interfaceModulePathLabel.setText(displayText)
        self.interfaceModulePathLabel.setToolTip(interfacePath)

        # 2. Data source-specific config
        self._configWidget.prefill(dataSourceConfig)

        # 3. File saving
        if "filePath" in dataSourceConfig:
            self.fileSavingGroupBox.setChecked(True)
            outDirPath, fileName = os.path.split(dataSourceConfig["filePath"])
            self._outDirPath = outDirPath
            # Adjust display text
            displayText = (
                outDirPath
                if len(outDirPath) <= 40
                else outDirPath[:17] + "..." + outDirPath[-20:]
            )
            self.outDirPathLabel.setText(displayText)
            self.outDirPathLabel.setToolTip(outDirPath)
            self.fileNameTextField.setText(fileName)
        else:
            self.fileSavingGroupBox.setChecked(False)
