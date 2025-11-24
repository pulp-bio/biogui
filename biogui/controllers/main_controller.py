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

import math
from types import MappingProxyType

from PySide6.QtCore import QModelIndex, QObject, Qt, Signal, Slot
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QMessageBox

from biogui.views import (
    DataSourceConfigDialog,
    MainWindow,
    SignalConfigDialog,
    SignalConfigWizard,
    SignalPlotWidget,
)

from ..utils import SigData
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
        True if validation is successful, False otherwise.
    """
    # Validate filter settings
    if sigConfig.get("filterEnabled", False):
        freq1 = sigConfig.get("freq1", 0)
        freq2 = sigConfig.get("freq2", None)
        if freq2 is not None and freq1 >= freq2:
            return False
        if freq1 >= fs / 2 or (freq2 is not None and freq2 >= fs / 2):
            return False
    return True


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
        List of checked data sources.
    """
    checkedDataSources = []
    root = dataSourceModel.invisibleRootItem()
    for i in range(dataSourceModel.rowCount()):
        dataSourceItem = root.child(i)
        if dataSourceItem.checkState() == Qt.Checked:  # type: ignore
            checkedDataSources.append(dataSourceItem.text())
    return checkedDataSources


class MainController(QObject):
    """
    Main controller of the application.

    It manages data sources, signal plots, and coordinates streaming.

    Parameters
    ----------
    mainWin : MainWindow
        Main window of the application.
    parent : QObject, optional
        Parent object.

    Attributes
    ----------
    dataSourceModel : QStandardItemModel
        Model representing the data sources and their signals.
    _mainWin : MainWindow
        Reference to the main window.
    _streamingControllers : dict of (str: StreamingController)
        Collection of StreamingController objects, indexed by the name of the corresponding data source.
    _signalPlotWidgets : dict of (str: SignalPlotWidget)
        Collection of SignalPlotWidget objects, indexed by the name of the corresponding signal.
    _config : dict
        Configuration of the signals.
    _isStreaming : bool
        Flag indicating if streaming is active.

    Class attributes
    ----------------
    signalsReady : Signal
        Qt Signal emitted when signals are ready.
    streamingStarted : Signal
        Qt Signal emitted when streaming starts.
    streamingStopped : Signal
        Qt Signal emitted when streaming stops.
    streamingControllersChanged : Signal
        Qt Signal emitted when streaming controllers are added/removed.
    """

    signalsReady = Signal(list)
    streamingStarted = Signal()
    streamingStopped = Signal()
    streamingControllersChanged = Signal()

    def __init__(self, mainWin: MainWindow, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._mainWin = mainWin
        self._streamingControllers: dict[str, StreamingController] = {}
        self._signalPlotWidgets: dict[str, SignalPlotWidget] = {}
        self._config: dict = {}
        self._isStreaming = False

        # Setup UI data source tree
        self.dataSourceModel = QStandardItemModel(self)
        self.dataSourceModel.setHorizontalHeaderLabels(["Data sources"])
        self._mainWin.dataSourceTree.setModel(self.dataSourceModel)
        self.dataSourceModel.itemChanged.connect(self._signalCheckedHandler)

        self._connectSignals()

    @property
    def streamingControllers(self) -> MappingProxyType[str, StreamingController]:
        """MappingProxyType: Property representing a read-only view of the StreamingController dictionary."""
        return MappingProxyType(self._streamingControllers)

    def _connectSignals(self) -> None:
        """Connect Qt signals and slots."""
        # Data source and signal management
        self._mainWin.addDataSourceButton.clicked.connect(self._addDataSourceHandler)
        self._mainWin.deleteDataSourceButton.clicked.connect(
            self._deleteDataSourceHandler
        )
        self._mainWin.editButton.clicked.connect(self._editDataSourceHandler)
        self._mainWin.dataSourceTree.clicked.connect(self._selectionHandler)

        # Streaming
        self._mainWin.startStreamingButton.clicked.connect(self.startStreaming)
        self._mainWin.stopStreamingButton.clicked.connect(self.stopStreaming)

    @Slot(QStandardItem)
    def _signalCheckedHandler(self, item: QStandardItem):
        """Handler for when a checkbox is checked/unchecked."""
        parent = item.parent()

        # If this is a data source item (has no parent)
        if parent is None:
            # This is a data source - handle start button state
            # Enable start button if any data sources are checked
            checkedDataSources = getCheckedDataSources(self.dataSourceModel)
            self._mainWin.startStreamingButton.setEnabled(len(checkedDataSources) > 0)
        else:
            # This is a signal item - show/hide plot
            dataSource = parent.text()
            sigName = item.text()
            plotId = f"{dataSource}%{sigName}"

            if item.checkState() == Qt.Checked:  # type: ignore
                # Show plot - create if not exists
                if plotId not in self._signalPlotWidgets:
                    self._createPlot(dataSource, sigName)
                else:
                    # Plot exists but was hidden, show it
                    self._signalPlotWidgets[plotId].show()
                self._relayoutPlots()
            else:
                # Hide plot - remove from layout
                if plotId in self._signalPlotWidgets:
                    self._removePlotFromLayout(plotId)

    def _createPlot(self, dataSource: str, sigName: str):
        """Create a plot widget for a signal."""
        sigConfig = self._config[dataSource]["sigsConfigs"][sigName]

        # Only create plot if chSpacing is in config (indicates plotting is enabled)
        if "chSpacing" not in sigConfig:
            return

        plotId = f"{dataSource}%{sigName}"

        # Don't recreate if already exists
        if plotId in self._signalPlotWidgets:
            return

        signalPlotWidget = SignalPlotWidget(
            sigName,
            **sigConfig,
            renderLenMs=self._mainWin.renderLenMs,
            parent=self._mainWin,
        )
        self.streamingStarted.connect(signalPlotWidget.startTimers)
        self.streamingStopped.connect(signalPlotWidget.stopTimers)
        self._mainWin.renderLenChanged.connect(signalPlotWidget.reInitPlot)

        self._signalPlotWidgets[plotId] = signalPlotWidget

        # If streaming is active, start timers immediately
        if self._isStreaming:
            signalPlotWidget.startTimers()

    def _removePlotFromLayout(self, plotId: str):
        """Remove a plot from the grid layout."""
        if plotId in self._signalPlotWidgets:
            widget = self._signalPlotWidgets[plotId]
            self._mainWin.plotsGridLayout.removeWidget(widget)
            widget.setParent(None)
            widget.hide()
            self._relayoutPlots()

    def _relayoutPlots(self):
        """Reorganize plots in a grid layout."""
        # Get all visible plots (those that are checked)
        visiblePlots = []
        root = self.dataSourceModel.invisibleRootItem()

        for i in range(self.dataSourceModel.rowCount()):
            dataSourceItem = root.child(i)
            dataSource = dataSourceItem.text()

            for j in range(dataSourceItem.rowCount()):
                sigItem = dataSourceItem.child(j)
                if sigItem.checkState() == Qt.Checked:  # type: ignore
                    sigName = sigItem.text()
                    plotId = f"{dataSource}%{sigName}"
                    if plotId in self._signalPlotWidgets:
                        visiblePlots.append(self._signalPlotWidgets[plotId])

        # Clear the grid layout
        while self._mainWin.plotsGridLayout.count():
            item = self._mainWin.plotsGridLayout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # Calculate grid dimensions
        numPlots = len(visiblePlots)
        if numPlots == 0:
            return

        # Grid layout logic:
        # 1-2 plots: 1 column
        # 3-4 plots: 2 columns
        # 5+ plots: 2 columns (can be extended to 3 if needed)
        if numPlots <= 2:
            numCols = 1
        else:
            numCols = 2

        numRows = math.ceil(numPlots / numCols)

        # Add plots to grid
        for idx, plotWidget in enumerate(visiblePlots):
            row = idx // numCols
            col = idx % numCols
            plotWidget.show()
            self._mainWin.plotsGridLayout.addWidget(plotWidget, row, col)

    def startStreaming(self) -> None:
        """Start streaming."""
        # Handle UI elements
        self._mainWin.startStreamingButton.setEnabled(False)
        self._mainWin.stopStreamingButton.setEnabled(True)
        self._isStreaming = True

        # Disable edit button if a data source is currently selected
        currentIdx = self._mainWin.dataSourceTree.currentIndex()
        if currentIdx.isValid() and self.dataSourceModel.hasChildren(currentIdx):
            self._mainWin.editButton.setEnabled(False)

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
        self._isStreaming = False

        # Re-enable edit button if something is selected
        currentIdx = self._mainWin.dataSourceTree.currentIndex()
        if currentIdx.isValid():
            self._mainWin.editButton.setEnabled(True)

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

        # Save configuration
        dataSourceConfig["sigsConfigs"] = sigsConfigs
        self._config[str(streamingController)] = dataSourceConfig

        # Configure Qt Signals
        streamingController.signalsReady.connect(self._plotData)
        streamingController.errorOccurred.connect(self._handleErrors)
        streamingController.signalsReady.connect(lambda d: self.signalsReady.emit(d))

        # Temporarily disconnect itemChanged to avoid triggering during setup
        self.dataSourceModel.itemChanged.disconnect(self._signalCheckedHandler)

        # Update UI data source tree
        dataSourceNode = QStandardItem(str(streamingController))
        dataSourceNode.setFlags(dataSourceNode.flags() | Qt.ItemIsUserCheckable)  # type: ignore
        dataSourceNode.setData(Qt.Checked, Qt.CheckStateRole)  # type: ignore
        self.dataSourceModel.appendRow(dataSourceNode)

        # Add signal items with checkboxes
        for sigName, sigConfig in sigsConfigs.items():
            sigItem = QStandardItem(sigName)
            sigItem.setEditable(False)
            sigItem.setFlags(sigItem.flags() | Qt.ItemIsUserCheckable)  # type: ignore
            # Check by default if plot is configured
            if "chSpacing" in sigConfig:
                sigItem.setData(Qt.Checked, Qt.CheckStateRole)  # type: ignore
                # Create the plot
                self._createPlot(str(streamingController), sigName)
            else:
                sigItem.setData(Qt.Unchecked, Qt.CheckStateRole)  # type: ignore
            dataSourceNode.appendRow(sigItem)

        # Reconnect itemChanged handler
        self.dataSourceModel.itemChanged.connect(self._signalCheckedHandler)

        # Relayout plots
        self._relayoutPlots()

        # Enable start button since we just added a checked data source
        self._mainWin.startStreamingButton.setEnabled(True)

        # Inform other modules that a new source is available
        self.streamingControllersChanged.emit()

        self._mainWin.dataSourceTree.expandAll()

    def _deleteDataSource(self, dataSourceItem: QStandardItem) -> None:
        """Delete a data source, given data source item."""
        dataSource = dataSourceItem.text()

        # Remove every signal associated with the data source
        for row in range(dataSourceItem.rowCount()):
            sigName = dataSourceItem.child(row).text()
            # Remove plot widget
            plotId = f"{dataSource}%{sigName}"
            if plotId in self._signalPlotWidgets:
                plotWidgetToRemove = self._signalPlotWidgets.pop(plotId)
                self._mainWin.plotsGridLayout.removeWidget(plotWidgetToRemove)
                plotWidgetToRemove.deleteLater()

        # Relayout remaining plots
        self._relayoutPlots()

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
        dataPacket : list of SigData
            Data to plot.
        """
        dataSourceId = str(self.sender())
        for sigData in dataPacket:
            plotId = f"{dataSourceId}%{sigData.sigName}"
            if plotId in self._signalPlotWidgets:
                # Only plot if widget is visible (checked)
                widget = self._signalPlotWidgets[plotId]
                if widget.isVisible():
                    widget.addData(sigData.data)

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
        # Disconnect handler for editing
        self._mainWin.editButton.clicked.disconnect()
        self._mainWin.editButton.setEnabled(True)

        # Enable buttons and connect handler depending on the selection
        if self.dataSourceModel.hasChildren(idx):  # data source
            self._mainWin.deleteDataSourceButton.setEnabled(True)
            self._mainWin.editButton.clicked.connect(self._editDataSourceHandler)
            # Disable edit button if streaming is active
            if self._isStreaming:
                self._mainWin.editButton.setEnabled(False)
        else:  # signal
            self._mainWin.deleteDataSourceButton.setEnabled(False)
            self._mainWin.editButton.clicked.connect(self._editSignalHandler)

    @Slot()
    def _addDataSourceHandler(self):
        """Handler for adding a new data source."""
        # Ask for data source type
        dataSourceConfigDialog = DataSourceConfigDialog(parent=self._mainWin)
        outcome = dataSourceConfigDialog.exec()

        if outcome:
            # Request signal configuration
            dataSourceConfig = dataSourceConfigDialog.dataSourceConfig
            interfaceModule = dataSourceConfig["interfaceModule"]
            signalConfigWizard = SignalConfigWizard(
                interfaceModule.sigInfo, parent=self._mainWin
            )
            outcome = signalConfigWizard.exec()

            if outcome:
                # Get signal configuration
                sigsConfigs = signalConfigWizard.sigsConfigs
                self._addDataSource(dataSourceConfig, sigsConfigs)

    @Slot()
    def _deleteDataSourceHandler(self):
        """Handler to remove the selected data source."""
        # Get index and corresponding item
        idxToRemove = self._mainWin.dataSourceTree.currentIndex()
        itemToRemove = self.dataSourceModel.itemFromIndex(idxToRemove)

        # Delete the data source
        self._deleteDataSource(itemToRemove)

        # Disable start button, source deletion and signal configuration depending on the number of remaining sources
        if not self._streamingControllers:
            self._mainWin.startStreamingButton.setEnabled(False)
            self._mainWin.deleteDataSourceButton.setEnabled(False)
            self._mainWin.editButton.setEnabled(False)

    @Slot()
    def _editDataSourceHandler(self):
        """Handler for editing the data source configuration."""
        # Get index and corresponding item
        idxToEdit = self._mainWin.dataSourceTree.currentIndex()
        itemToEdit = self.dataSourceModel.itemFromIndex(idxToEdit)
        dataSourceToEdit = itemToEdit.text()

        # Open the dialog
        oldDataSourceConfig = self._config[dataSourceToEdit]
        dataSourceConfigDialog = DataSourceConfigDialog(
            **{k: v for k, v in oldDataSourceConfig.items() if k != "sigsConfigs"},
            parent=self._mainWin,
        )
        outcome = dataSourceConfigDialog.exec()

        if not outcome:
            return

        # Get new config
        newDataSourceConfig = dataSourceConfigDialog.dataSourceConfig

        # Check if signal names have changed
        oldSigNames = set(oldDataSourceConfig["interfaceModule"].sigInfo.keys())
        newSigNames = set(newDataSourceConfig["interfaceModule"].sigInfo.keys())
        if oldSigNames != newSigNames:
            # Signal names changed - delete old source and create new one
            QMessageBox.warning(
                self._mainWin,
                "Signal configuration reset",
                "The names of the signals are different from the previously "
                "configured ones, the configuration will be reset.",
                buttons=QMessageBox.Ok,  # type: ignore
                defaultButton=QMessageBox.Ok,  # type: ignore
            )

            # Delete old data source
            self._deleteDataSource(itemToEdit)

            # Request new signal configuration
            interfaceModule = newDataSourceConfig["interfaceModule"]
            signalConfigWizard = SignalConfigWizard(
                interfaceModule.sigInfo, parent=self._mainWin
            )
            outcome = signalConfigWizard.exec()

            if outcome:
                sigsConfigs = signalConfigWizard.sigsConfigs
                self._addDataSource(newDataSourceConfig, sigsConfigs)

            return

        # Update signal configuration with the new info
        sigsConfigs = oldDataSourceConfig["sigsConfigs"]
        sigInfo = newDataSourceConfig["interfaceModule"].sigInfo

        for sigName, sigConfig in sigsConfigs.items():
            sigConfig["nCh"] = sigInfo[sigName]["nCh"]
            sigConfig["fs"] = sigInfo[sigName]["fs"]

            # Validate filter settings
            if not validateFreqSettings(sigConfig, sigConfig["fs"]):
                sigConfig["filterEnabled"] = False
                QMessageBox.warning(
                    self._mainWin,
                    "Signal configuration reset",
                    f"The previous filtering settings of {sigName} are not compatible "
                    "with the new sampling rate, filtering will be disabled.",
                    buttons=QMessageBox.Ok,  # type: ignore
                    defaultButton=QMessageBox.Ok,  # type: ignore
                )

        # Update streaming controller
        oldDataSourceId = str(self._streamingControllers[dataSourceToEdit])
        self._streamingControllers[dataSourceToEdit].editDataSourceConfig(
            newDataSourceConfig, sigsConfigs
        )
        newDataSourceId = str(self._streamingControllers[dataSourceToEdit])

        # Update configuration
        newDataSourceConfig["sigsConfigs"] = sigsConfigs
        self._config[dataSourceToEdit] = newDataSourceConfig

        # Update tree
        itemToEdit.setText(newDataSourceId)

        # If the ID changed, update plot widgets keys
        if oldDataSourceId != newDataSourceId:
            for row in range(itemToEdit.rowCount()):
                sigName = itemToEdit.child(row).text()
                sigConfig = sigsConfigs[sigName]

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

                # Replace in the layout
                self._signalPlotWidgets[newPlotId] = newSignalPlotWidget
                self._relayoutPlots()

                oldSignalPlotWidget.deleteLater()

        # Inform other modules that a source was modified
        self.streamingControllersChanged.emit()

    @Slot()
    def _editSignalHandler(self):
        """Handler for editing the signal configuration."""
        # Get index and corresponding item
        idxToEdit = self._mainWin.dataSourceTree.currentIndex()
        itemToEdit = self.dataSourceModel.itemFromIndex(idxToEdit)
        sigName = itemToEdit.text()
        dataSource = itemToEdit.parent().text()

        # Open the dialog
        sigConfig = self._config[dataSource]["sigsConfigs"][sigName]
        signalConfigDialog = SignalConfigDialog(
            sigName, **sigConfig, parent=self._mainWin
        )
        outcome = signalConfigDialog.exec()

        if not outcome:
            return

        # Update signal configuration
        newSigConfig = signalConfigDialog.sigConfig
        self._config[dataSource]["sigsConfigs"][sigName] = newSigConfig

        # Update streaming controller
        isStreaming = self._isStreaming
        if isStreaming:
            self.stopStreaming()

        self._streamingControllers[dataSource].editSigConfig(sigName, newSigConfig)

        if isStreaming:
            self.startStreaming()

        # Handle plot widget:
        # - case 1: ON -> ON (need to replace the widget)
        # - case 2: ON -> OFF (need to remove the widget)
        # - case 3: OFF -> ON (need to create the widget)
        # - case 4: OFF -> OFF (no need to be handled)
        plotId = f"{str(self._streamingControllers[dataSource])}%{sigName}"
        wasPlotting = plotId in self._signalPlotWidgets
        shouldPlot = "chSpacing" in newSigConfig

        if wasPlotting and shouldPlot:  # case 1
            oldSignalPlotWidget = self._signalPlotWidgets.pop(plotId)
            newSignalPlotWidget = SignalPlotWidget(
                sigName,
                **newSigConfig,
                renderLenMs=self._mainWin.renderLenMs,
                parent=self._mainWin,
                dataQueue=oldSignalPlotWidget.dataQueue,  # type: ignore
            )
            self.streamingStarted.connect(newSignalPlotWidget.startTimers)
            self.streamingStopped.connect(newSignalPlotWidget.stopTimers)
            self._mainWin.renderLenChanged.connect(newSignalPlotWidget.reInitPlot)
            self._signalPlotWidgets[plotId] = newSignalPlotWidget

            # If streaming is active, start the timers immediately
            if isStreaming:
                newSignalPlotWidget.startTimers()

            oldSignalPlotWidget.deleteLater()

            # Update checkbox state
            itemToEdit.setData(Qt.Checked, Qt.CheckStateRole)  # type: ignore

        elif wasPlotting and not shouldPlot:  # case 2
            oldSignalPlotWidget = self._signalPlotWidgets.pop(plotId)
            oldSignalPlotWidget.deleteLater()

            # Update checkbox state
            itemToEdit.setData(Qt.Unchecked, Qt.CheckStateRole)  # type: ignore

        elif not wasPlotting and shouldPlot:  # case 3
            self._createPlot(dataSource, sigName)

            # If streaming is active, start timers
            if isStreaming:
                self._signalPlotWidgets[plotId].startTimers()

            # Update checkbox state
            itemToEdit.setData(Qt.Checked, Qt.CheckStateRole)  # type: ignore

        # Relayout plots
        self._relayoutPlots()
