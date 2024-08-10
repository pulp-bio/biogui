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

import importlib.util

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox, QWidget

from biogui import data_sources
from biogui.controllers.streaming_controller import InterfaceModule
from biogui.ui.add_data_source_dialog_ui import Ui_AddDataSourceDialog


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
    if not hasattr(module, "fs"):
        return (
            None,
            'The selected Python module does not contain a "fs" variable.',
        )
    if not hasattr(module, "nCh"):
        return (
            None,
            'The selected Python module does not contain a "nCh" variable.',
        )
    if not hasattr(module, "SigsPacket"):
        return (
            None,
            'The selected Python module does not contain a "SigsPacket" named tuple.',
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
            fs=module.fs,
            nCh=module.nCh,
            sigNames=module.SigsPacket._fields,
            decodeFn=module.decodeFn,
        ),
        "",
    )


class AddDataSourceDialog(QDialog, Ui_AddDataSourceDialog):
    """
    Dialog for adding a new data source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent widget.

    Attributes
    ----------
    _configWidget : ConfigWidget
        Widget for data source configuration.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self.buttonBox.accepted.connect(self._addSourceHandler)
        self.buttonBox.rejected.connect(self.close)

        self.browseInterfaceModuleButton.clicked.connect(self._browseInterfaceModule)
        self.sourceComboBox.addItems(
            list(map(lambda sourceType: sourceType.value, data_sources.DataSourceType))
        )
        self.sourceComboBox.currentTextChanged.connect(self._onSourceChange)

        # Source type (default is serial port)
        self._configWidget = data_sources.getConfigWidget(
            data_sources.DataSourceType.SERIAL, self
        )
        self.sourceConfigContainer.addWidget(self._configWidget)

        self._dataSourceConfig = {}
        self._isValid = False
        self._errMessage = ""

        self.destroyed.connect(self.deleteLater)

    @property
    def dataSourceConfig(self) -> dict:
        """dict: Property for getting the data source configuration."""
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
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Python module containing the decode function",
            filter="*.py",
        )
        if filePath != "":
            interfaceModule, errMessage = _loadInterfaceFromFile(filePath)
            if interfaceModule is None:
                QMessageBox.critical(
                    self,
                    "Invalid Python file",
                    errMessage,
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                return

            self._dataSourceConfig["interfaceModule"] = interfaceModule
            # Limit display text to 50 characters
            displayText = (
                filePath
                if len(filePath) <= 50
                else filePath[:20] + "..." + filePath[-30:]
            )
            self.interfaceModulePathLabel.setText(displayText)
            self.interfaceModulePathLabel.setToolTip(filePath)

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

        if "interfaceModule" not in self._dataSourceConfig:
            self._isValid = False
            self._errMessage = "No interface was provided."
            return

        if self.sourceComboBox.currentText() == "":
            self._isValid = False
            self._errMessage = 'The "source" field is invalid.'
            return

        configResult = self._configWidget.validateConfig()
        if not configResult.isValid:
            self._isValid = False
            self._errMessage = configResult.errMessage
            return

        self._dataSourceConfig["dataSourceType"] = configResult.dataSourceType
        self._dataSourceConfig.update(configResult.dataSourceConfig)
        self._isValid = True
