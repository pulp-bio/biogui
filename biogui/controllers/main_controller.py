# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Main controller of BioGUI.


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

from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from PySide6.QtCore import QEvent, QModelIndex, QObject, QRect, QSize, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QMouseEvent, QPainter, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QMessageBox,
    QStyle,
    QStyleOptionButton,
    QStyleOptionViewItem,
    QStyledItemDelegate,
)

from biogui.views import (
    DataSourceConfigDialog,
    MainWindow,
    SignalConfigDialog,
    SignalConfigWizard,
    SignalPlotWidget,
)

from ..utils import InterfaceModule, PlatformConfig, SigData
from .streaming_controller import StreamingController


def validateFreqSettings(sigConfig, fs):
    """
    Validate the frequency settings given the sampling rate.

    Parameters
    ----------
    sigConfig : dict
        Signal configuration.
    fs : float
        Sampling rate.

    Returns
    -------
    bool
        Whether the frequency settings are compatible with the sampling rate.
    """
    freqSettingsValid = True
    if "freqs" in sigConfig:
        for freq in sigConfig["freqs"]:
            if freq >= fs / 2:
                freqSettingsValid = False
                break
    return freqSettingsValid


def getCheckedDataSources(dataSourceModel: QStandardItemModel) -> list[str]:
    """
    Get the checked data sources given the data source model.

    Parameters
    ----------
    dataSourceModel : QStandardItemModel
        Model representing the data sources.

    Returns
    -------
    list of str
        List containing the IDs of the checked data sources.
    """
    checkedDataSources = []
    root = dataSourceModel.invisibleRootItem()
    sourceIdRole = MainController._DATA_SOURCE_ID_ROLE
    for i in range(dataSourceModel.rowCount()):
        dataSourceItem = root.child(i)
        if dataSourceItem.checkState() == Qt.Checked:  # type: ignore
            dataSourceId = dataSourceItem.data(sourceIdRole)
            checkedDataSources.append(dataSourceId or dataSourceItem.text())
    return checkedDataSources


class DataSourceTreeDelegate(QStyledItemDelegate):
    """Draw an optional inline configure button inside top-level data source rows."""

    _BUTTON_SIZE = 20
    _BUTTON_MARGIN = 6

    def __init__(
        self,
        hasActionRole: int,
        iconRole: int,
        fallbackIcon: QIcon,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._hasActionRole = hasActionRole
        self._iconRole = iconRole
        self._fallbackIcon = fallbackIcon

    @classmethod
    def buttonRectForRowRect(cls, rowRect: QRect) -> QRect:
        x = rowRect.right() - cls._BUTTON_SIZE - cls._BUTTON_MARGIN
        y = rowRect.top() + (rowRect.height() - cls._BUTTON_SIZE) // 2
        return QRect(x, y, cls._BUTTON_SIZE, cls._BUTTON_SIZE)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        isTopLevel = not index.parent().isValid()
        hasInlineAction = bool(index.data(self._hasActionRole))
        if not (index.column() == 0 and isTopLevel and hasInlineAction):
            super().paint(painter, option, index)
            return

        textOption = QStyleOptionViewItem(option)
        textOptionAny = cast(Any, textOption)
        optionAny = cast(Any, option)
        textOptionAny.rect = optionAny.rect.adjusted(
            0,
            0,
            -(self._BUTTON_SIZE + self._BUTTON_MARGIN * 2),
            0,
        )
        super().paint(painter, textOption, index)

        buttonOption = QStyleOptionButton()
        buttonOptionAny = cast(Any, buttonOption)
        buttonOptionAny.rect = self.buttonRectForRowRect(optionAny.rect)
        buttonOptionAny.state = QStyle.StateFlag.State_Enabled
        buttonOptionAny.icon = index.data(self._iconRole) or self._fallbackIcon
        buttonOptionAny.iconSize = QSize(16, 16)

        widget = getattr(optionAny, "widget", None)
        style = widget.style() if widget is not None else None
        if style is not None:
            style.drawControl(QStyle.ControlElement.CE_PushButton, buttonOption, painter)


class MainController(QObject):
    """
    Main controller of BioGUI.

    Parameters
    ----------
    mainWin : MainWindow
        Instance of MainWindow.
    parent : QObject or None, default=None
        Parent QObject.

    Attributes
    ----------
    _mainWin : MainWindow
        Instance of MainWindow.
    _streamingControllers : dict of (str: StreamingController)
        Collection of StreamingController objects, indexed by the name of the corresponding data source.
    _signalPlotWidgets : dict of (str: SignalPlotWidget)
        Collection of SignalPlotWidget objects, indexed by the name of the corresponding signal.
    _config : dict
        Configuration of the signals.

    Class attributes
    ----------------
    streamingStarted : Signal
        Qt Signal emitted when streaming starts.
    streamingStopped : Signal
        Qt Signal emitted when streaming stops.
    signalsReady : Signal
        Qt Signal emitted when all the decoded signals from a data source are ready for visualization.
    streamingControllersChanged : Signal
        Qt Signal emitted when the set of configured streaming controllers change.
    """

    streamingStarted = Signal()
    streamingStopped = Signal()
    signalsReady = Signal(SigData)
    streamingControllersChanged = Signal()

    _DATA_SOURCE_ID_ROLE = Qt.ItemDataRole.UserRole + 1
    _DATA_SOURCE_HAS_INLINE_ACTION_ROLE = Qt.ItemDataRole.UserRole + 2
    _DATA_SOURCE_INLINE_ACTION_ICON_ROLE = Qt.ItemDataRole.UserRole + 3

    def __init__(self, mainWin: MainWindow, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._mainWin = mainWin
        self._streamingControllers: dict[str, StreamingController] = {}
        self._signalPlotWidgets: dict[str, SignalPlotWidget] = {}
        self._config: dict = {}

        # Setup UI data source tree
        self.dataSourceModel = QStandardItemModel(self)
        self.dataSourceModel.setHorizontalHeaderLabels(["Data sources"])
        self._mainWin.dataSourceTree.setModel(self.dataSourceModel)
        inlineActionIcon = QIcon.fromTheme("preferences-system", self._mainWin.editButton.icon())
        self._dataSourceTreeDelegate = DataSourceTreeDelegate(
            self._DATA_SOURCE_HAS_INLINE_ACTION_ROLE,
            self._DATA_SOURCE_INLINE_ACTION_ICON_ROLE,
            inlineActionIcon,
            self._mainWin.dataSourceTree,
        )
        self._mainWin.dataSourceTree.setItemDelegateForColumn(0, self._dataSourceTreeDelegate)
        self._mainWin.dataSourceTree.viewport().installEventFilter(self)
        self.dataSourceModel.itemChanged.connect(self._dataSourceCheckedHandler)

        self._connectSignals()

    @property
    def streamingControllers(self) -> MappingProxyType[str, StreamingController]:
        """MappingProxyType: Property representing a read-only view of the StreamingController dictionary."""
        return MappingProxyType(self._streamingControllers)

    def _connectSignals(self) -> None:
        """Connect Qt signals and slots."""
        # Data source and signal management
        self._mainWin.addDataSourceButton.clicked.connect(self._addDataSourceHandler)
        self._mainWin.deleteDataSourceButton.clicked.connect(self._deleteDataSourceHandler)
        self._mainWin.editButton.clicked.connect(self._editDataSourceHandler)
        self._mainWin.dataSourceTree.clicked.connect(self._selectionHandler)

        # Streaming
        self._mainWin.startStreamingButton.clicked.connect(self.startStreaming)
        self._mainWin.stopStreamingButton.clicked.connect(self.stopStreaming)

    @Slot(QStandardItem)
    def _dataSourceCheckedHandler(self, item: QStandardItem):
        """Handler for when a data source is checked/unchecked."""
        # Enable start button
        if item.checkState() == Qt.Checked:  # type: ignore
            self._mainWin.startStreamingButton.setEnabled(True)
            self._mainWin.editButton.setEnabled(True)
            self._mainWin.deleteDataSourceButton.setEnabled(True)

        # Disable start button
        if not getCheckedDataSources(self.dataSourceModel):
            self._mainWin.startStreamingButton.setEnabled(False)
            self._mainWin.editButton.setEnabled(False)
            self._mainWin.deleteDataSourceButton.setEnabled(False)

    def startStreaming(self) -> None:
        """Start streaming."""
        # Handle UI elements
        self._mainWin.startStreamingButton.setEnabled(False)
        self._mainWin.stopStreamingButton.setEnabled(True)
        self._mainWin.streamConfGroupBox.setEnabled(False)
        self._mainWin.moduleContainer.setEnabled(False)

        # Emit "start" Qt Signal (for pluggable modules)
        self.streamingStarted.emit()

        # Start all StreamingController objects
        checkedDataSources = getCheckedDataSources(self.dataSourceModel)
        for checkedDataSource in checkedDataSources:
            self._streamingControllers[checkedDataSource].startStreaming()

    def stopStreaming(self) -> None:
        """Stop streaming."""
        # Stop all StreamingController objects
        checkedDataSources = getCheckedDataSources(self.dataSourceModel)
        for checkedDataSource in checkedDataSources:
            self._streamingControllers[checkedDataSource].stopStreaming()

        # Emit "stop" Qt Signal (for pluggable modules)
        self.streamingStopped.emit()

        # Handle UI elements
        self._mainWin.startStreamingButton.setEnabled(True)
        self._mainWin.stopStreamingButton.setEnabled(False)
        self._mainWin.streamConfGroupBox.setEnabled(True)
        self._mainWin.moduleContainer.setEnabled(True)

    def _addDataSource(self, dataSourceConfig: dict, sigsConfigs: dict) -> None:
        """Add a data source, given its configuration."""
        # Create streaming controller
        dataSourceWorkerArgs = {
            k: v
            for k, v in dataSourceConfig.items()
            if k not in ("interfacePath", "interfaceModule", "filePath")
        }
        interfaceModule = dataSourceConfig["interfaceModule"]
        filePath = dataSourceConfig.get("filePath", None)
        dataSourceWorkerArgs["packetSize"] = interfaceModule.packetSize
        dataSourceWorkerArgs["startSeq"] = interfaceModule.startSeq
        dataSourceWorkerArgs["stopSeq"] = interfaceModule.stopSeq
        streamingController = StreamingController(
            dataSourceWorkerArgs,
            interfaceModule.decodeFn,
            filePath,
            sigsConfigs,
            parent=self,
        )
        self._streamingControllers[str(streamingController)] = streamingController

        # Create plot widget
        for iSigName, iSigConfig in sigsConfigs.items():
            if "chSpacing" in iSigConfig:
                signalPlotWidget = SignalPlotWidget(
                    iSigName,
                    **iSigConfig,
                    renderLenMs=self._mainWin.renderLenMs,
                    parent=self._mainWin,
                )
                self.streamingStarted.connect(signalPlotWidget.startTimers)
                self.streamingStopped.connect(signalPlotWidget.stopTimers)
                self._mainWin.renderLenChanged.connect(signalPlotWidget.reInitPlot)
                self._mainWin.plotsLayout.addWidget(signalPlotWidget)

                self._signalPlotWidgets[f"{str(streamingController)}%{iSigName}"] = signalPlotWidget

        # Save configuration
        dataSourceConfig["sigsConfigs"] = sigsConfigs
        self._config[str(streamingController)] = dataSourceConfig

        # Configure Qt Signals
        streamingController.signalsReady.connect(self._plotData)
        streamingController.errorOccurred.connect(self._handleErrors)
        streamingController.signalsReady.connect(lambda d: self.signalsReady.emit(d))

        # Update UI data source tree
        dataSourceId = str(streamingController)
        dataSourceNode = QStandardItem(
            self._formatDataSourceDisplayName(dataSourceId, dataSourceConfig)
        )
        dataSourceNode.setData(dataSourceId, self._DATA_SOURCE_ID_ROLE)
        dataSourceNode.setData(
            self._hasInlineConfigAction(dataSourceConfig),
            self._DATA_SOURCE_HAS_INLINE_ACTION_ROLE,
        )
        dataSourceNode.setData(
            self._getInlineConfigIcon(dataSourceConfig),
            self._DATA_SOURCE_INLINE_ACTION_ICON_ROLE,
        )
        dataSourceNode.setFlags(dataSourceNode.flags() | Qt.ItemIsUserCheckable)  # type: ignore
        dataSourceNode.setData(Qt.Checked, Qt.CheckStateRole)  # type: ignore
        self.dataSourceModel.appendRow(dataSourceNode)

        for sigName in sigsConfigs:
            dataSourceNode.appendRow(QStandardItem(sigName))

        # Inform other modules that a new source is available
        self.streamingControllersChanged.emit()

        self._mainWin.dataSourceTree.expandAll()

    def _deleteDataSource(self, dataSourceItem: QStandardItem) -> None:
        """Delete a data source, given data source item."""
        dataSource = self._getDataSourceIdFromItem(dataSourceItem)

        # Remove every signal associated with the data source
        for row in range(dataSourceItem.rowCount()):
            sigName = dataSourceItem.child(row).text()
            # Remove plot widget
            plotId = f"{dataSource}%{sigName}"
            if plotId in self._signalPlotWidgets:
                plotWidgetToRemove = self._signalPlotWidgets.pop(plotId)
                self._mainWin.plotsLayout.removeWidget(plotWidgetToRemove)
                plotWidgetToRemove.deleteLater()

        # Delete streaming controller and config
        self._streamingControllers[dataSource].deleteLater()
        del self._streamingControllers[dataSource]
        del self._config[dataSource]

        # Update UI data source tree
        self.dataSourceModel.removeRow(dataSourceItem.row())

        # Inform other modules that a source was deleted
        self.streamingControllersChanged.emit()

    @Slot(list)
    def _plotData(self, dataPacket: list[SigData]):
        """
        Plot the given data on the corresponding plot.

        Parameters
        ----------
        dataPacket : tuple of (str, list of SigData)
            Data to plot.
        """
        dataSourceId = str(self.sender())
        for sigData in dataPacket:
            plotId = f"{dataSourceId}%{sigData.sigName}"
            if plotId in self._signalPlotWidgets:
                self._signalPlotWidgets[plotId].addData(sigData.data)

    @Slot(str)
    def _handleErrors(self, errMessage: str) -> None:
        """When an error occurs, display an alert and stop streaming."""
        self.stopStreaming()
        QMessageBox.critical(
            self._mainWin,
            "Streaming error",
            errMessage,
            buttons=QMessageBox.Retry,  # type: ignore
            defaultButton=QMessageBox.Retry,  # type: ignore
        )

    @Slot(QModelIndex)
    def _selectionHandler(self, idx: QModelIndex):
        """Enable buttons to configure sources or signals."""
        selectedItem = self.dataSourceModel.itemFromIndex(idx)
        if selectedItem is None:
            return

        # Disconnect handler for editing
        self._mainWin.editButton.clicked.disconnect()
        self._mainWin.editButton.setEnabled(True)

        # Enable buttons and connect handler depending on the selection
        if self.dataSourceModel.hasChildren(idx):  # data source
            self._mainWin.deleteDataSourceButton.setEnabled(True)
            self._mainWin.editButton.clicked.connect(self._editDataSourceHandler)
        else:  # signal
            self._mainWin.deleteDataSourceButton.setEnabled(False)
            self._mainWin.editButton.clicked.connect(self._editSignalHandler)

    def _addDataSourceHandler(self) -> None:
        """Handler for adding a new data source."""
        # Open the dialog to get data source configuration
        dataSourceConfigDialog = DataSourceConfigDialog(parent=self._mainWin)
        accepted = dataSourceConfigDialog.exec()
        if not accepted:
            return
        dataSourceConfig = dataSourceConfigDialog.dataSourceConfig

        if not self._runPlatformConfigStep(dataSourceConfig):
            return

        # Get the configurations of all the signals
        signalConfigWizard = SignalConfigWizard(
            dataSourceConfig["interfaceModule"].sigInfo, parent=self._mainWin
        )
        completed = signalConfigWizard.exec()
        if not completed:
            return
        sigsConfigs = signalConfigWizard.sigsConfigs

        # Add the data source
        self._addDataSource(dataSourceConfig, sigsConfigs)

        # Enable start button
        self._mainWin.startStreamingButton.setEnabled(True)

    def _deleteDataSourceHandler(self) -> None:
        """Handler to remove the selected data source."""
        # Get index and corresponding item
        idxToRemove = self._mainWin.dataSourceTree.currentIndex()
        itemToRemove = self.dataSourceModel.itemFromIndex(idxToRemove)

        if itemToRemove is None:
            return
        if itemToRemove.parent() is not None:
            itemToRemove = itemToRemove.parent()

        # Delete the data source
        self._deleteDataSource(itemToRemove)

        # Disable start button, source deletion and signal configuration depending on the number of remaining sources
        if not self._streamingControllers:
            self._mainWin.startStreamingButton.setEnabled(False)
            self._mainWin.editButton.setEnabled(False)
            self._mainWin.deleteDataSourceButton.setEnabled(False)

    def _editDataSourceHandler(self) -> None:
        """Handler for editing the data source configuration."""
        # Get index and corresponding item
        idxToEdit = self._mainWin.dataSourceTree.currentIndex()
        itemToEdit = self.dataSourceModel.itemFromIndex(idxToEdit)
        if itemToEdit is None:
            return
        if itemToEdit.parent() is not None:
            itemToEdit = itemToEdit.parent()
        dataSourceToEdit = self._getDataSourceIdFromItem(itemToEdit)

        # Open the dialog
        oldDataSourceConfig = self._config[dataSourceToEdit]
        dataSourceConfigDialog = DataSourceConfigDialog(
            **{k: v for k, v in oldDataSourceConfig.items() if k != "sigsConfigs"},
            parent=self._mainWin,
        )
        accepted = dataSourceConfigDialog.exec()
        if not accepted:
            return
        newDataSourceConfig = dataSourceConfigDialog.dataSourceConfig

        if not self._runPlatformConfigStep(
            newDataSourceConfig,
            existingInterfaceModule=oldDataSourceConfig["interfaceModule"],
        ):
            return

        self._applyEditedDataSourceConfig(
            itemToEdit=itemToEdit,
            oldDataSourceConfig=oldDataSourceConfig,
            newDataSourceConfig=newDataSourceConfig,
        )

    def _applyEditedDataSourceConfig(
        self,
        itemToEdit: QStandardItem,
        oldDataSourceConfig: dict,
        newDataSourceConfig: dict,
    ) -> None:
        """Apply updated data source configuration and keep plots/controllers in sync."""
        dataSourceToEdit = self._getDataSourceIdFromItem(itemToEdit)

        if (
            newDataSourceConfig["interfaceModule"].sigInfo.keys()
            != oldDataSourceConfig["interfaceModule"].sigInfo.keys()
        ):  # signals are different -> delete the whole StreamingController and add a new one from scratch
            QMessageBox.warning(
                self._mainWin,
                "Signal configuration reset",
                "The names of the signals are different from the previously "
                "configured ones, the configuration will be reset.",
                buttons=QMessageBox.Ok,  # type: ignore
                defaultButton=QMessageBox.Ok,  # type: ignore
            )

            # Get the configurations of all the signals
            signalConfigWizard = SignalConfigWizard(
                newDataSourceConfig["interfaceModule"].sigInfo, parent=self._mainWin
            )
            completed = signalConfigWizard.exec()
            if not completed:
                return
            sigsConfigs = signalConfigWizard.sigsConfigs

            # Remove old configuration and add the new one
            self._deleteDataSource(itemToEdit)
            self._addDataSource(newDataSourceConfig, sigsConfigs)

            return

        # Update signal configuration with the new info
        sigsConfigs = oldDataSourceConfig["sigsConfigs"]
        sigInfo = newDataSourceConfig["interfaceModule"].sigInfo
        for sigName in sigsConfigs:
            sigsConfigs[sigName]["fs"] = sigInfo[sigName]["fs"]
            sigsConfigs[sigName]["nCh"] = sigInfo[sigName]["nCh"]
            if sigsConfigs[sigName]["nCh"] == 1:
                sigsConfigs[sigName]["chSpacing"] = 0

            # Check if filtering settings are still valid
            if not validateFreqSettings(sigsConfigs[sigName], sigInfo[sigName]["fs"]):
                QMessageBox.warning(
                    self._mainWin,
                    "Signal configuration reset",
                    f"The previous filtering settings of {sigName} are not compatible "
                    "with the new sampling rate, filtering will be disabled.",
                    buttons=QMessageBox.Ok,  # type: ignore
                    defaultButton=QMessageBox.Ok,  # type: ignore
                )
                # Delete settings
                del sigsConfigs[sigName]["filtType"]
                del sigsConfigs[sigName]["freqs"]
                del sigsConfigs[sigName]["filtOrder"]
        newDataSourceConfig["sigsConfigs"] = sigsConfigs

        # Update streaming controller and store new settings
        streamingController = self._streamingControllers.pop(dataSourceToEdit)
        oldDataSourceId = str(streamingController)
        del self._config[oldDataSourceId]
        streamingController.editDataSourceConfig(newDataSourceConfig)
        newDataSourceId = str(streamingController)
        self._streamingControllers[newDataSourceId] = streamingController
        self._config[newDataSourceId] = newDataSourceConfig
        itemToEdit.setData(newDataSourceId, self._DATA_SOURCE_ID_ROLE)
        itemToEdit.setData(
            self._hasInlineConfigAction(newDataSourceConfig),
            self._DATA_SOURCE_HAS_INLINE_ACTION_ROLE,
        )
        itemToEdit.setData(
            self._getInlineConfigIcon(newDataSourceConfig),
            self._DATA_SOURCE_INLINE_ACTION_ICON_ROLE,
        )
        itemToEdit.setText(self._formatDataSourceDisplayName(newDataSourceId, newDataSourceConfig))

        # Update plot widgets
        for sigName, sigConfig in sigsConfigs.items():
            oldPlotId = f"{oldDataSourceId}%{sigName}"
            if oldPlotId not in self._signalPlotWidgets:
                continue
            newPlotId = f"{newDataSourceId}%{sigName}"

            oldSignalPlotWidget = self._signalPlotWidgets.pop(oldPlotId)
            newSignalPlotWidget = SignalPlotWidget(
                sigName,
                **sigConfig,
                renderLenMs=self._mainWin.renderLenMs,
                parent=self._mainWin,
            )
            self.streamingStarted.connect(newSignalPlotWidget.startTimers)
            self.streamingStopped.connect(newSignalPlotWidget.stopTimers)
            self._mainWin.renderLenChanged.connect(newSignalPlotWidget.reInitPlot)
            self._mainWin.plotsLayout.replaceWidget(oldSignalPlotWidget, newSignalPlotWidget)
            self._signalPlotWidgets[newPlotId] = newSignalPlotWidget

            oldSignalPlotWidget.deleteLater()

        # Inform other modules that a source was modified
        self.streamingControllersChanged.emit()

    def _getPlatformConfig(self, interfaceModule: InterfaceModule | None) -> PlatformConfig | None:
        """Return optional curated platform metadata from an interface module."""
        if interfaceModule is None:
            return None
        return interfaceModule.platformConfig

    def _getPlatformConfigFromDataSource(self, dataSourceConfig: dict) -> PlatformConfig | None:
        """Return optional curated platform metadata from a data-source config."""
        interfaceModule = dataSourceConfig.get("interfaceModule")
        if not isinstance(interfaceModule, InterfaceModule):
            return None
        return self._getPlatformConfig(interfaceModule)

    def _hasInlineConfigAction(self, dataSourceConfig: dict) -> bool:
        """Return True when the data source exposes a secondary inline config action."""
        platformConfig = self._getPlatformConfigFromDataSource(dataSourceConfig)
        return bool(platformConfig and platformConfig.hasInlineConfigAction)

    def _getInlineConfigIcon(self, dataSourceConfig: dict) -> QIcon:
        """Resolve the icon used for the inline config action."""
        platformConfig = self._getPlatformConfigFromDataSource(dataSourceConfig)
        iconName = (
            platformConfig.inlineActionIconName
            if platformConfig is not None
            else "preferences-system"
        )
        return QIcon.fromTheme(iconName, self._mainWin.editButton.icon())

    def _runPlatformConfigStep(
        self,
        dataSourceConfig: dict,
        existingInterfaceModule: InterfaceModule | None = None,
    ) -> bool:
        """Run an optional curated platform configuration step and update the interface."""
        currentInterfaceModule = existingInterfaceModule or dataSourceConfig["interfaceModule"]
        platformConfig = self._getPlatformConfig(currentInterfaceModule)
        if platformConfig is None:
            return True

        configuredInterfaceModule = platformConfig.configureInterfaceModule(
            self._mainWin,
            currentInterfaceModule,
        )
        if configuredInterfaceModule is None:
            return False

        dataSourceConfig["interfaceModule"] = configuredInterfaceModule
        return True

    def _openInlineConfigDialogForDataSource(self, dataSourceId: str) -> None:
        """Open the inline platform configuration dialog for an already configured source."""
        if dataSourceId not in self._config:
            return

        oldDataSourceConfig = self._config[dataSourceId]
        if not self._hasInlineConfigAction(oldDataSourceConfig):
            return

        sourceRow = -1
        for row in range(self.dataSourceModel.rowCount()):
            item = self.dataSourceModel.item(row)
            if item and self._getDataSourceIdFromItem(item) == dataSourceId:
                sourceRow = row
                break
        if sourceRow < 0:
            return

        itemToEdit = self.dataSourceModel.item(sourceRow)
        if itemToEdit is None:
            return

        newDataSourceConfig = {k: v for k, v in oldDataSourceConfig.items() if k != "sigsConfigs"}
        if not self._runPlatformConfigStep(
            newDataSourceConfig,
            existingInterfaceModule=oldDataSourceConfig["interfaceModule"],
        ):
            return

        self._applyEditedDataSourceConfig(
            itemToEdit=itemToEdit,
            oldDataSourceConfig=oldDataSourceConfig,
            newDataSourceConfig=newDataSourceConfig,
        )

    def _editSignalHandler(self) -> None:
        """Handler for editing the signal configuration."""
        # Get index and corresponding item
        idxToEdit = self._mainWin.dataSourceTree.currentIndex()
        itemToEdit = self.dataSourceModel.itemFromIndex(idxToEdit)
        if itemToEdit is None:
            return
        sigName = itemToEdit.text()
        dataSourceItem = itemToEdit.parent()
        if dataSourceItem is None:
            return
        dataSource = self._getDataSourceIdFromItem(dataSourceItem)

        if sigName not in self._config[dataSource]["sigsConfigs"]:
            return

        # Open the dialog
        sigConfig = self._config[dataSource]["sigsConfigs"][sigName]
        signalConfigDialog = SignalConfigDialog(sigName, **sigConfig, parent=self._mainWin)
        accepted = signalConfigDialog.exec()
        if not accepted:
            return
        sigConfig = signalConfigDialog.sigConfig

        # Update streaming controller settings
        self._streamingControllers[dataSource].editSigConfig(sigName, sigConfig)

        # Handle plot widget:
        # - case 1: ON -> ON
        # - case 2: ON -> OFF
        # - case 3: OFF -> ON
        # - case 4: OFF -> OFF (no need to be handled)
        plotId = f"{str(self._streamingControllers[dataSource])}%{sigName}"
        if plotId in self._signalPlotWidgets:  # case 1 & 2
            oldSignalPlotWidget = self._signalPlotWidgets.pop(plotId)

            if "chSpacing" in sigConfig:  # case 1
                newSignalPlotWidget = SignalPlotWidget(
                    sigName,
                    **sigConfig,
                    renderLenMs=self._mainWin.renderLenMs,
                    parent=self._mainWin,
                    dataQueue=oldSignalPlotWidget.dataQueue,  # type: ignore
                )
                self.streamingStarted.connect(newSignalPlotWidget.startTimers)
                self.streamingStopped.connect(newSignalPlotWidget.stopTimers)
                self._mainWin.renderLenChanged.connect(newSignalPlotWidget.reInitPlot)
                self._mainWin.plotsLayout.replaceWidget(oldSignalPlotWidget, newSignalPlotWidget)
                self._signalPlotWidgets[plotId] = newSignalPlotWidget

            oldSignalPlotWidget.deleteLater()
        elif "chSpacing" in sigConfig:  # case 3
            newSignalPlotWidget = SignalPlotWidget(
                sigName,
                **sigConfig,
                renderLenMs=self._mainWin.renderLenMs,
                parent=self._mainWin,
            )
            self.streamingStarted.connect(newSignalPlotWidget.startTimers)
            self.streamingStopped.connect(newSignalPlotWidget.stopTimers)
            self._mainWin.renderLenChanged.connect(newSignalPlotWidget.reInitPlot)
            self._mainWin.plotsLayout.addWidget(newSignalPlotWidget)
            self._signalPlotWidgets[plotId] = newSignalPlotWidget

        # Save new settings
        self._config[dataSource]["sigsConfigs"][sigName] = sigConfig

    def _getDataSourceIdFromItem(self, item: QStandardItem) -> str:
        """Return stable internal data-source identifier stored in model item data."""
        return str(item.data(self._DATA_SOURCE_ID_ROLE) or item.text())

    def _formatDataSourceDisplayName(self, dataSourceId: str, dataSourceConfig: dict) -> str:
        """Build a readable label including transport/device and interface module name."""
        interfacePath = dataSourceConfig.get("interfacePath", "")
        interfaceName = Path(str(interfacePath)).stem.replace("interface_", "")
        if interfaceName:
            return f"{dataSourceId} [{interfaceName}]"
        return dataSourceId

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Open inline platform config when the row action button is clicked."""
        if (
            watched is self._mainWin.dataSourceTree.viewport()
            and event.type() == QEvent.Type.MouseButtonRelease
        ):
            mouseEvent = event
            if not isinstance(mouseEvent, QMouseEvent):
                return False

            idx = self._mainWin.dataSourceTree.indexAt(mouseEvent.pos())
            if not idx.isValid() or idx.column() != 0 or idx.parent().isValid():
                return False

            if not bool(idx.data(self._DATA_SOURCE_HAS_INLINE_ACTION_ROLE)):
                return False

            visualRect = self._mainWin.dataSourceTree.visualRect(idx)
            buttonRect = DataSourceTreeDelegate.buttonRectForRowRect(visualRect)
            if not buttonRect.contains(mouseEvent.pos()):
                return False

            item = self.dataSourceModel.itemFromIndex(idx)
            if item is None:
                return False

            self._openInlineConfigDialogForDataSource(self._getDataSourceIdFromItem(item))
            return True

        return super().eventFilter(watched, event)
