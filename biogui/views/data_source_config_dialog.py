# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Dialog to add a new data source.
"""

from __future__ import annotations

import importlib.util
import traceback
from pathlib import Path
from sys import platform

from PySide6.QtWidgets import QCheckBox, QDialog, QFileDialog, QMessageBox, QWidget

from biogui import data_sources, paths
from biogui.platforms.wulpus.runtime import isolate_wulpus_interface_module
from biogui.platforms.wulpus_pro.runtime import (
    isolate_wulpus_interface_module as isolate_wulpus_pro_interface_module,
)
from biogui.ui.ui_data_source_config_dialog import Ui_DataSourceConfigDialog
from biogui.utils import InterfaceModule, PlatformConfig


def _is_bundled_interface_path(interface_path: Path) -> bool:
    """Return True if the path is a bundled interface_*.py under paths.PLATFORMS_DIR."""
    if not (
        interface_path.is_file()
        and interface_path.name.startswith("interface_")
        and interface_path.suffix == ".py"
    ):
        return False
    try:
        interface_path.resolve().relative_to(paths.PLATFORMS_DIR.resolve())
    except ValueError:
        return False
    return True


def _platform_and_variant_for(filePath: Path) -> tuple[str, str]:
    """
    Derive the (platform, variant) display names for a bundled interface file.

    The platform is the top-level folder under ``paths.INTERFACES_DIR``; the
    variant is the filename stem with ``interface_`` and, when present, the
    redundant ``<platform>_`` prefix stripped (e.g.
    ``interface_biogapultra_eeg_mic.py`` under platform ``biogapultra`` ->
    variant ``eeg_mic``). Falls back to the full stem when the file doesn't
    happen to start with ``<platform>_``.
    """
    platformName = filePath.relative_to(paths.INTERFACES_DIR).parts[0]
    stem = filePath.stem[10:]  # remove 'interface_'
    prefix = platformName + "_"
    variantName = stem[len(prefix):] if stem.startswith(prefix) else stem
    return platformName, variantName


def _loadInterfacesFromDirectory() -> dict[str, dict[str, Path]]:
    """
    Load all interface modules from the platforms tree (interface_*.py in
    subfolders), grouped by their top-level platform folder.

    Returns
    -------
    dict of {str: dict of {str: Path}}
        Platform display name -> {variant display name -> file path}. A
        platform with exactly one interface has exactly one entry in its
        inner dict.
    """
    platforms: dict[str, dict[str, Path]] = {}
    for filePath in sorted(paths.INTERFACES_DIR.rglob("interface_*.py")):
        platformName, variantName = _platform_and_variant_for(filePath)
        platforms.setdefault(platformName, {})[variantName] = filePath

    return platforms


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
    except Exception as e:
        # Print detailed traceback to terminal for debugging
        traceback.print_exc()
        return None, f"Failed to import module: {type(e).__name__}: {e}"

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
    packet_size = module.packetSize
    if not isinstance(packet_size, (int, list)):
        return None, "The packet size must be a positive integer or a list of (header, size) tuples with positive sizes."
    if isinstance(packet_size, int):
        if packet_size <= 0:
            return None, "The packet size must be a positive integer or a list of (header, size) tuples with positive sizes."
    elif isinstance(packet_size, list):
        for header, size in packet_size:
            if not isinstance(header, int) or not isinstance(size, int) or size <= 0:
                return None, "The packet size must be a positive integer or a list of (header, size) tuples with positive sizes."

    platformConfig = getattr(module, "platformConfig", None)
    if platformConfig is not None and not isinstance(platformConfig, PlatformConfig):
        return None, '"platformConfig" must be a PlatformConfig object when provided.'

    for sigName, sigData in module.sigInfo.items():
        if sigName in ("acq_ts", "trigger"):
            return None, '"acq_ts" and "trigger" are reserved signal names.'

        # Validate extra arguments
        if "extras" not in sigData:  # default to time series
            sigData["extras"] = {"type": "time-series"}
            continue

        if not isinstance(sigData["extras"], dict):
            return None, f'Signal "{sigName}": "extras" must be a dictionary.'

        if "type" not in sigData["extras"]:
            return (
                None,
                f'Signal "{sigName}": "extras" dictionary must contain a "type" key.',
            )

        validTypes = ("ultrasound", "time-series", "radar")
        if sigData["extras"]["type"] not in validTypes:
            return (
                None,
                f'Signal "{sigName}": signal type must be one of {validTypes}, got "{sigData["extras"]["type"]}".',
            )

    interface_module = InterfaceModule(
        packetSize=module.packetSize,
        startSeq=module.startSeq,
        stopSeq=module.stopSeq,
        sigInfo=module.sigInfo,
        decodeFn=module.decodeFn,
        platformConfig=platformConfig,
        headerByte=getattr(module, "headerByte", None),
        tailerByte=getattr(module, "tailerByte", None),
        wifiPacketSize=getattr(module, "wifiPacketSize", None),
        stripTransportFraming=getattr(module, "stripTransportFraming", False),
    )
    interface_module = _isolate_platform_interface_module(interface_module)

    return (interface_module, "")


def _isolate_platform_interface_module(interface_module: InterfaceModule) -> InterfaceModule:
    """Apply platform-specific decoder isolation for bundled mutable interfaces."""
    interface_module = isolate_wulpus_interface_module(interface_module)
    interface_module = isolate_wulpus_pro_interface_module(interface_module)
    return interface_module


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

        # Populate combo box with platforms; the "Shield:" row appears only
        # when the selected platform has more than one interface variant.
        self._interfacesByPlatform = _loadInterfacesFromDirectory()
        self.interfaceModuleComboBox.addItems(sorted(self._interfacesByPlatform.keys()))
        self.interfaceModuleComboBox.setCurrentIndex(0)
        # Add browse option as last item
        self.interfaceModuleComboBox.addItem(self._BROWSE_INTERFACE)
        self.formLayout.setRowVisible(self.interfaceVariantComboBox, False)

        # Populate combo box with data sources and create configuration widget
        dataSources = list(map(lambda sourceType: sourceType.value, data_sources.DataSourceType))
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
        self.interfaceModuleComboBox.activated.connect(self._onPlatformSelected)
        self.interfaceVariantComboBox.activated.connect(self._onVariantSelected)
        self.dataSourceComboBox.currentTextChanged.connect(self._onDataSourceChange)
        self.browseOutDirButton.clicked.connect(self._browseOutDir)

        self._dataSourceConfig = {}
        # Set default output directory to the runtime data folder.
        self._outDirPath = paths.DATARUNTIME_DIR
        self.outDirPathLabel.setText(str(self._outDirPath))
        self.fileSavingGroupBox.setChecked(True)
        self.fileNameTextField.setText("run")
        self.plotAfterRunCheckBox = QCheckBox("Enable post-run plotting", self.fileSavingGroupBox)
        self.formLayout_2.addRow(self.plotAfterRunCheckBox)

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

    def _onPlatformSelected(self, index: int) -> None:
        """Handle platform selection from the Interface ComboBox."""
        itemSelected = self.interfaceModuleComboBox.itemText(index)
        if itemSelected == self._BROWSE_INTERFACE:
            self.formLayout.setRowVisible(self.interfaceVariantComboBox, False)
            interfacePath = self._browseInterfaceModule()
            if interfacePath is None:
                return
            self._loadAndStoreInterface(interfacePath, fromBrowsing=True)
            return

        variants = self._interfacesByPlatform.get(itemSelected, {})
        if len(variants) <= 1:
            # Single-shield platform: load it directly, same as before this
            # platform grouping existed.
            self.formLayout.setRowVisible(self.interfaceVariantComboBox, False)
            interfacePath = next(iter(variants.values()), None)
            if interfacePath is None:
                return
            self._loadAndStoreInterface(interfacePath, fromBrowsing=False)
            return

        # Multiple shields under this platform: show the Shield row and
        # default to its first entry.
        self.interfaceVariantComboBox.clear()
        self.interfaceVariantComboBox.addItems(sorted(variants.keys()))
        self.interfaceVariantComboBox.setCurrentIndex(0)
        self.formLayout.setRowVisible(self.interfaceVariantComboBox, True)
        self._loadAndStoreInterface(
            variants[self.interfaceVariantComboBox.currentText()], fromBrowsing=False
        )

    def _onVariantSelected(self, index: int) -> None:
        """Handle shield selection from the Shield ComboBox."""
        platformSelected = self.interfaceModuleComboBox.currentText()
        variantSelected = self.interfaceVariantComboBox.itemText(index)
        interfacePath = self._interfacesByPlatform.get(platformSelected, {}).get(
            variantSelected
        )
        if interfacePath is None:
            return
        self._loadAndStoreInterface(interfacePath, fromBrowsing=False)

    def _loadAndStoreInterface(self, interfacePath: Path, fromBrowsing: bool) -> None:
        """Load an interface module from `interfacePath` and store it in the
        pending data source config, or show an error and reset on failure."""
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
            self.formLayout.setRowVisible(self.interfaceVariantComboBox, False)
            self.interfaceModulePathLabel.setText("")
            return

        self._dataSourceConfig["interfacePath"] = interfacePath
        self._dataSourceConfig["interfaceModule"] = interfaceModule
        if fromBrowsing:
            self.interfaceModulePathLabel.setText(str(interfacePath))

    def _browseInterfaceModule(self) -> Path | None:
        """Browse files to select the module containing the decode function."""
        interfacePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Python module containing the decode function",
            filter="*.py",
        )
        return Path(interfacePath) if interfacePath else None

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

        self._dataSourceConfig["plotAfterRun"] = self.plotAfterRunCheckBox.isChecked()

        self.accept()

    def _prefill(self, dataSourceConfig: dict):
        """Pre-fill the form with the provided configuration."""
        # 1. Interface module
        interfacePath = dataSourceConfig["interfacePath"]
        self._dataSourceConfig["interfacePath"] = interfacePath
        self._dataSourceConfig["interfaceModule"] = dataSourceConfig["interfaceModule"]

        if _is_bundled_interface_path(interfacePath):
            # Find and select the platform + shield in the ComboBoxes
            platformName, variantName = _platform_and_variant_for(interfacePath)
            platformIndex = self.interfaceModuleComboBox.findText(platformName)
            if platformIndex >= 0:
                self.interfaceModuleComboBox.setCurrentIndex(platformIndex)
                variants = self._interfacesByPlatform.get(platformName, {})
                if len(variants) > 1:
                    self.interfaceVariantComboBox.clear()
                    self.interfaceVariantComboBox.addItems(sorted(variants.keys()))
                    self.formLayout.setRowVisible(self.interfaceVariantComboBox, True)
                    variantIndex = self.interfaceVariantComboBox.findText(variantName)
                    if variantIndex >= 0:
                        self.interfaceVariantComboBox.setCurrentIndex(variantIndex)
                else:
                    self.formLayout.setRowVisible(self.interfaceVariantComboBox, False)
        else:
            displayName = self._BROWSE_INTERFACE
            index = self.interfaceModuleComboBox.findText(displayName)
            if index >= 0:
                self.interfaceModuleComboBox.setCurrentIndex(index)
            self.formLayout.setRowVisible(self.interfaceVariantComboBox, False)
            self.interfaceModulePathLabel.setText(str(interfacePath))

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

        if "plotAfterRun" in dataSourceConfig:
            self.plotAfterRunCheckBox.setChecked(bool(dataSourceConfig["plotAfterRun"]))
