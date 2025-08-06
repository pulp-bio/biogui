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

from types import MappingProxyType

from PySide6.QtCore import QModelIndex, QObject, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QMessageBox

from biogui.views import (
    DataSourceConfigDialog,
    MainWindow,
    SignalConfigDialog,
    SignalConfigWizard,
    SignalPlotWidget,
)

from ..utils import SigData, instanceSlot
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

    def startStreaming(self) -> None:
        """Start streaming."""
        # Handle UI elements
        self._mainWin.startStreamingButton.setEnabled(False)
        self._mainWin.stopStreamingButton.setEnabled(True)
        self._mainWin.streamConfGroupBox.setEnabled(False)
        self._mainWin.moduleContainer.setEnabled(False)

        # Start all StreamingController objects
        for streamController in self._streamingControllers.values():
            streamController.startStreaming()

        # Emit "start" Qt Signal (for pluggable modules)
        self.streamingStarted.emit()

    def stopStreaming(self) -> None:
        """Stop streaming."""
        # Stop all StreamingController objects
        for streamController in self._streamingControllers.values():
            streamController.stopStreaming()

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

                self._signalPlotWidgets[f"{str(streamingController)}%{iSigName}"] = (
                    signalPlotWidget
                )

        # Save configuration
        dataSourceConfig["sigsConfigs"] = sigsConfigs
        self._config[str(streamingController)] = dataSourceConfig

        # Configure Qt Signals
        streamingController.signalsReady.connect(self._plotData)
        streamingController.errorOccurred.connect(self._handleErrors)
        streamingController.signalsReady.connect(lambda d: self.signalsReady.emit(d))

        # Update UI data source tree
        dataSourceNode = QStandardItem(str(streamingController))
        self.dataSourceModel.appendRow(dataSourceNode)
        dataSourceNode.appendRows([QStandardItem(sigName) for sigName in sigsConfigs])

        # Inform other modules that a new source is available
        self.streamingControllersChanged.emit()

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

    @instanceSlot(list)
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

    @instanceSlot(str)
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

    @instanceSlot(QModelIndex)
    def _selectionHandler(self, idx: QModelIndex):
        """Enable buttons to configure sources or signals."""
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
        dataSourceToEdit = itemToEdit.text()

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
        itemToEdit.setText(newDataSourceId)

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
            self._mainWin.plotsLayout.replaceWidget(
                oldSignalPlotWidget, newSignalPlotWidget
            )
            self._signalPlotWidgets[newPlotId] = newSignalPlotWidget

            oldSignalPlotWidget.deleteLater()

        # Inform other modules that a source was modified
        self.streamingControllersChanged.emit()

    def _editSignalHandler(self) -> None:
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
                self._mainWin.plotsLayout.replaceWidget(
                    oldSignalPlotWidget, newSignalPlotWidget
                )
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
