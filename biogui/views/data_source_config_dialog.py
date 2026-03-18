# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Dialog to add a new data source.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from sys import platform

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox, QWidget

from biogui import data_sources, paths
from biogui.ui.ui_data_source_config_dialog import Ui_DataSourceConfigDialog
from biogui.utils import InterfaceModule


def _loadInterfacesFromDirectory() -> dict[str, Path]:
    """
    Load all interface modules from the interfaces directory.

    Returns
    -------
    dict of {str: Path}
        Dictionary mapping display names to full file paths.
    """
    interfaceFiles = {}
    for filePath in sorted(paths.INTERFACES_DIR.glob("interface_*.py")):
        displayName = filePath.stem[10:]  # remove 'interface_'
        interfaceFiles[displayName] = filePath

    return interfaceFiles


def _loadInterfaceFromFile(filePath: Path) -> tuple[InterfaceModule | None, str]:
    """
    Load an interface from a Python file.

    Parameters
    ----------
    filePath : Path
        Path to Python file.

    Returns
    -------
    InterfaceModule or None
        InterfaceModule object, or None if the module is not valid.
    str
        Error message.
    """
    # Remove ".py" extension and get file name
    moduleName = filePath.stem

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

    for sigName, sigData in module.sigInfo.items():
        if sigName in ("acq_ts", "trigger"):
            return None, '"acq_ts" and "trigger" are reserved signal names.'

        # Validate signal_type
        if "signal_type" not in sigData:
            return (
                None,
                f'Signal "{sigName}" is missing the required "signal_type" field.',
            )

        if not isinstance(sigData["signal_type"], dict):
            return None, f'Signal "{sigName}": "signal_type" must be a dictionary.'

        if "type" not in sigData["signal_type"]:
            return (
                None,
                f'Signal "{sigName}": "signal_type" dictionary must contain a "type" key.',
            )

        validTypes = ("ultrasound", "time-series")
        if sigData["signal_type"]["type"] not in validTypes:
            return (
                None,
                f'Signal "{sigName}": signal type must be one of {validTypes}, got "{sigData["signal_type"]["type"]}".',
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
    _outDirPath : Path or None
        Path to the output directory.
    """

    # Placeholder text for browsing interfaces
    _BROWSE_INTERFACE = "Browse..."

    def __init__(
        self,
        dataSourceType: data_sources.DataSourceType | None = None,
        parent: QWidget | None = None,
        **kwargs: dict,
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        # Populate combo box with interface modules
        self._interfaceModules = _loadInterfacesFromDirectory()
        # Add browse option as last item
        self.interfaceModuleComboBox.addItems(list(self._interfaceModules.keys()))
        self.interfaceModuleComboBox.setCurrentIndex(0)
        self.interfaceModuleComboBox.addItem(self._BROWSE_INTERFACE)

        # Populate combo box with data sources and create configuration widget
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
        self.interfaceModuleComboBox.currentTextChanged.connect(
            self._onInterfaceModuleChange
        )
        self.dataSourceComboBox.currentTextChanged.connect(self._onDataSourceChange)
        self.browseOutDirButton.clicked.connect(self._browseOutDir)

        self._dataSourceConfig = {}
        # Set default output directory to ./data/
        self._outDirPath = Path.cwd() / "data"
        self._outDirPath.mkdir(exist_ok=True)  # create it if it doesn't exist
        self.outDirPathLabel.setText(str(self._outDirPath))

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
        self.setTabOrder(self.interfaceModuleComboBox, self.dataSourceComboBox)

        tabOrderedFields = self._configWidget.getFieldsInTabOrder()
        if not tabOrderedFields:
            self.setTabOrder(self.dataSourceComboBox, self.fileSavingGroupBox)
            return

        self.setTabOrder(self.dataSourceComboBox, tabOrderedFields[0])
        for i in range(1, len(tabOrderedFields)):
            self.setTabOrder(tabOrderedFields[i - 1], tabOrderedFields[i])
        self.setTabOrder(tabOrderedFields[-1], self.fileSavingGroupBox)

    def _onInterfaceModuleChange(self, displayName: str) -> None:
        """Handle interface module selection from ComboBox."""
        if displayName == self._BROWSE_INTERFACE:
            # Browse interface module in external folder
            interfacePath = self._browseInterfaceModule()
        else:
            # Get interface from combo box
            interfacePath = self._interfaceModules.get(displayName)

        if interfacePath is None:
            return

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
            # Reset to placeholder on error
            self.interfaceModuleComboBox.setCurrentIndex(0)
            self.interfaceModulePathLabel.setText("")
            return

        self._dataSourceConfig["interfacePath"] = interfacePath
        self._dataSourceConfig["interfaceModule"] = interfaceModule
        self.interfaceModulePathLabel.setText(str(interfacePath))

    def _browseInterfaceModule(self) -> Path | None:
        """Browse files to select the module containing the decode function."""
        interfacePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Python module containing the decode function",
            filter="*.py",
        )
        return Path(interfacePath) if interfacePath is not None else None

    def _browseOutDir(self) -> None:
        """Browse directory where the data will be saved."""
        outDirPath = QFileDialog.getExistingDirectory(
            self,
            "Select destination directory",
            str(Path.cwd()),
            QFileDialog.ShowDirsOnly,  # type: ignore
        )
        if outDirPath != "":
            self._outDirPath = Path(outDirPath)

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
            self._dataSourceConfig["filePath"] = self._outDirPath / outFileName

        self.accept()

    def _prefill(self, dataSourceConfig: dict):
        """Pre-fill the form with the provided configuration."""
        # 1. Interface module
        interfacePath = dataSourceConfig["interfacePath"]
        self._dataSourceConfig["interfacePath"] = interfacePath
        self._dataSourceConfig["interfaceModule"] = dataSourceConfig["interfaceModule"]

        # Find and select the interface in the ComboBox
        filename = interfacePath.name
        if filename.startswith("interface_") and filename.endswith(".py"):
            displayName = filename[10:-3]
            index = self.interfaceModuleComboBox.findText(displayName)
            if index >= 0:
                self.interfaceModuleComboBox.setCurrentIndex(index)

        # 2. Data source-specific config
        self._configWidget.prefill(dataSourceConfig)

        # 3. File saving
        if "filePath" in dataSourceConfig:
            self.fileSavingGroupBox.setChecked(True)
            self._outDirPath = dataSourceConfig["filePath"].parent
            outDirPath = str(self._outDirPath)
            fileName = dataSourceConfig["filePath"].name

            self.outDirPathLabel.setText(outDirPath)
            self.outDirPathLabel.setToolTip(outDirPath)
            self.fileNameTextField.setText(fileName)
        else:
            self.fileSavingGroupBox.setChecked(False)
