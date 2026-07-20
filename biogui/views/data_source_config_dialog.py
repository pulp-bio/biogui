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
from dataclasses import dataclass
from pathlib import Path
from sys import platform

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QMessageBox,
    QTreeView,
    QWidget,
)

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


@dataclass
class InterfaceLeaf:
    """A single bundled interface, shown as a selectable item in the interface tree."""

    displayName: str
    path: Path


@dataclass
class InterfaceGroup:
    """A platform folder bundling several interfaces, shown as an expandable sub-menu."""

    name: str
    children: list["InterfaceLeaf | InterfaceGroup"]


# Role used to stash the interface file path on leaf items of the tree model.
_INTERFACE_PATH_ROLE = Qt.UserRole + 1


def _flattenLeaves(nodes: list["InterfaceLeaf | InterfaceGroup"]) -> list[InterfaceLeaf]:
    """Recursively collect every leaf under the given nodes."""
    leaves: list[InterfaceLeaf] = []
    for node in nodes:
        if isinstance(node, InterfaceLeaf):
            leaves.append(node)
        else:
            leaves.extend(_flattenLeaves(node.children))
    return leaves


def _buildInterfaceNode(dirPath: Path) -> "InterfaceLeaf | InterfaceGroup | None":
    """
    Recursively turn a platform folder into a tree node: a folder bundling a single interface
    (whether direct or nested in sub-folders) collapses into a flat leaf, while one bundling
    several becomes an expandable group so its interfaces open in a sub-menu.
    """
    children: list[InterfaceLeaf | InterfaceGroup] = [
        InterfaceLeaf(filePath.stem[10:], filePath)  # remove 'interface_' prefix
        for filePath in sorted(dirPath.glob("interface_*.py"))
    ]
    subDirPaths = sorted(
        p for p in dirPath.iterdir() if p.is_dir() and not p.name.startswith((".", "__"))
    )
    for subDirPath in subDirPaths:
        childNode = _buildInterfaceNode(subDirPath)
        if childNode is not None:
            children.append(childNode)

    if not children:
        return None
    leaves = _flattenLeaves(children)
    if len(leaves) == 1:
        return leaves[0]

    children.sort(
        key=lambda node: node.displayName if isinstance(node, InterfaceLeaf) else node.name
    )
    return InterfaceGroup(dirPath.name, children)


def _loadInterfaceTree() -> list["InterfaceLeaf | InterfaceGroup"]:
    """
    Build the interface tree from the platforms directory (interface_*.py in subfolders).

    Returns
    -------
    list of InterfaceLeaf or InterfaceGroup
        Top-level nodes, one per platform folder.
    """
    platformDirPaths = sorted(
        p
        for p in paths.INTERFACES_DIR.iterdir()
        if p.is_dir() and not p.name.startswith((".", "__"))
    )
    nodes = [_buildInterfaceNode(p) for p in platformDirPaths]
    nodes = [node for node in nodes if node is not None]
    nodes.sort(key=lambda node: node.displayName if isinstance(node, InterfaceLeaf) else node.name)
    return nodes


def _buildInterfaceTreeModel(tree: list["InterfaceLeaf | InterfaceGroup"]) -> QStandardItemModel:
    """Turn an interface tree into a QStandardItemModel for the combo box's tree view popup."""
    model = QStandardItemModel()

    def addNode(parentItem: QStandardItem, node: "InterfaceLeaf | InterfaceGroup") -> None:
        if isinstance(node, InterfaceLeaf):
            item = QStandardItem(node.displayName)
            item.setEditable(False)
            item.setData(str(node.path), _INTERFACE_PATH_ROLE)
            parentItem.appendRow(item)
            return

        groupItem = QStandardItem(node.name)
        groupItem.setEditable(False)
        # Group headers are labels, not choices: enabled (so they aren't greyed out) but not
        # selectable, so a click on one cannot become the current interface.
        groupItem.setFlags(Qt.ItemIsEnabled)
        font = groupItem.font()
        font.setBold(True)
        groupItem.setFont(font)
        parentItem.appendRow(groupItem)
        for childNode in node.children:
            addNode(groupItem, childNode)

    for node in tree:
        addNode(model.invisibleRootItem(), node)

    return model


def _findLeafIndex(model: QStandardItemModel, parent: QModelIndex, matches) -> QModelIndex:
    """Recursively search the tree model for the first leaf item for which matches(index) is True."""
    for row in range(model.rowCount(parent)):
        index = model.index(row, 0, parent)
        if index.data(_INTERFACE_PATH_ROLE) is not None and matches(index):
            return index
        found = _findLeafIndex(model, index, matches)
        if found.isValid():
            return found
    return QModelIndex()


def _findLeafIndexByPath(model: QStandardItemModel, interfacePath: Path) -> QModelIndex:
    """Search the tree model for the leaf item matching interfacePath, wherever it is nested."""
    return _findLeafIndex(
        model, QModelIndex(), lambda index: index.data(_INTERFACE_PATH_ROLE) == str(interfacePath)
    )


def _selectComboBoxIndex(comboBox: QComboBox, index: QModelIndex) -> None:
    """Select a (possibly nested) model index as the combo box's current item."""
    if not index.isValid():
        return
    comboBox.setRootModelIndex(index.parent())
    comboBox.setCurrentIndex(index.row())
    comboBox.setRootModelIndex(QModelIndex())


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
        return (
            None,
            "The packet size must be a positive integer or a list of (header, size) tuples with positive sizes.",
        )
    if isinstance(packet_size, int):
        if packet_size <= 0:
            return (
                None,
                "The packet size must be a positive integer or a list of (header, size) tuples with positive sizes.",
            )
    elif isinstance(packet_size, list):
        for header, size in packet_size:
            if not isinstance(header, int) or not isinstance(size, int) or size <= 0:
                return (
                    None,
                    "The packet size must be a positive integer or a list of (header, size) tuples with positive sizes.",
                )

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

        validTypes = ("ultrasound", "time-series")
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

        # Populate the interface combo box from a tree grouped by platform folder: a platform
        # bundling a single interface shows up as a flat entry, one bundling several as an
        # expandable sub-menu (shown via a QTreeView popup instead of the usual flat list).
        interfaceModel = _buildInterfaceTreeModel(_loadInterfaceTree())
        interfaceModel.appendRow(QStandardItem(self._BROWSE_INTERFACE))  # add browse option last

        interfaceTreeView = QTreeView(self.interfaceModuleComboBox)
        interfaceTreeView.setModel(interfaceModel)
        interfaceTreeView.setHeaderHidden(True)
        interfaceTreeView.expandAll()

        self.interfaceModuleComboBox.setModel(interfaceModel)
        self.interfaceModuleComboBox.setView(interfaceTreeView)
        firstLeafIndex = _findLeafIndex(interfaceModel, QModelIndex(), lambda _index: True)
        _selectComboBoxIndex(self.interfaceModuleComboBox, firstLeafIndex)

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
        self.interfaceModuleComboBox.activated.connect(self._onInterfaceModuleSelected)
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

    def _onInterfaceModuleSelected(self, _index: int) -> None:
        """Handle interface module selection from the combo box (and its tree view popup)."""
        # The tree view popup nests items under group headers, so the row-only "index" argument
        # doesn't identify the selected item on its own; read it back via current text/data
        # instead, which Qt resolves against the full (possibly nested) model index.
        itemSelected = self.interfaceModuleComboBox.currentText()
        if itemSelected == self._BROWSE_INTERFACE:
            # Browse interface module in external folder
            interfacePath = self._browseInterfaceModule()
            fromBrowsing = True
        else:
            # Get interface path stashed on the selected leaf item
            pathData = self.interfaceModuleComboBox.currentData(_INTERFACE_PATH_ROLE)
            interfacePath = Path(pathData) if pathData else None
            fromBrowsing = False

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

        model = self.interfaceModuleComboBox.model()
        if _is_bundled_interface_path(interfacePath):
            # Find and select the interface in the tree, wherever it is nested
            _selectComboBoxIndex(
                self.interfaceModuleComboBox, _findLeafIndexByPath(model, interfacePath)
            )
        else:
            browseIndex = model.index(model.rowCount() - 1, 0)  # browse option is always last
            _selectComboBoxIndex(self.interfaceModuleComboBox, browseIndex)
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
