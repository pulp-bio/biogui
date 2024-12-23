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


class MainController(QObject):
    """
    Main controller of BioGUI.

    Parameters
    ----------
    mainWin : MainWindow
        Instance of MainWindow.

    Attributes
    ----------
    _mainWin : MainWindow
        Instance of MainWindow.
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
    appClosed : Signal
        Qt Signal emitted when the application is closed.
    signalReady : Signal
        Qt Signal emitted when a signal is ready for visualization.
    newSourceAdded : Signal
        Qt Signal emitted when a new source is added.
    """

    streamingStarted = Signal()
    streamingStopped = Signal()
    appClosed = Signal()
    signalReady = Signal(SigData)
    newSourceAdded = Signal(StreamingController)

    def __init__(self, mainWin: MainWindow) -> None:
        super().__init__()
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
    def streamingControllers(self) -> dict[str, StreamingController]:
        """
        dict of (str: StreamingController): Property representing a collection of
        StreamingController objects, indexed by the name of the corresponding DataSource.
        """
        return self._streamingControllers.copy()

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
        self._mainWin.streamConfGroupBox.setEnabled(True)
        self._mainWin.startStreamingButton.setEnabled(True)
        self._mainWin.stopStreamingButton.setEnabled(False)

    @instanceSlot(list)
    def _plotData(self, dataPacket: list[SigData]):
        """Plot the given data on the corresponding plot.

        Parameters
        ----------
        dataPacket : DataPacket
            Data to plot.
        """
        for sigData in dataPacket:
            if sigData.sigName in self._signalPlotWidgets:
                self._signalPlotWidgets[sigData.sigName].addData(sigData.data)

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
            dataSourceConfig["interfaceModule"].sigInfo, self._mainWin
        )
        completed = signalConfigWizard.exec()
        if not completed:
            return
        sigsConfigs = signalConfigWizard.sigsConfigs

        # Create streaming controller
        dataSourceWorkerArgs = dataSourceConfig.copy()
        del dataSourceWorkerArgs["interfacePath"]
        interfaceModule = dataSourceWorkerArgs.pop("interfaceModule")
        filePath = dataSourceWorkerArgs.pop("filePath", None)
        dataSourceWorkerArgs["packetSize"] = interfaceModule.packetSize
        dataSourceWorkerArgs["startSeq"] = interfaceModule.startSeq
        dataSourceWorkerArgs["stopSeq"] = interfaceModule.stopSeq
        streamingController = StreamingController(
            dataSourceWorkerArgs, interfaceModule.decodeFn, filePath, sigsConfigs, self
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

                self._signalPlotWidgets[iSigName] = signalPlotWidget

        # Save configuration
        dataSourceConfig["sigsConfigs"] = sigsConfigs
        self._config[str(streamingController)] = dataSourceConfig

        # Configure Qt Signals
        streamingController.signalReady.connect(self._plotData)
        streamingController.errorOccurred.connect(self._handleErrors)
        streamingController.signalReady.connect(lambda d: self.signalReady.emit(d))

        # Update UI data source tree
        dataSourceNode = QStandardItem(str(streamingController))
        self.dataSourceModel.appendRow(dataSourceNode)
        dataSourceNode.appendRows([QStandardItem(sigName) for sigName in sigsConfigs])

        # Emit signal to inform pluggable modules that a new source has been added
        self.newSourceAdded.emit(streamingController)

        # Enable start button
        self._mainWin.startStreamingButton.setEnabled(True)

    def _deleteDataSourceHandler(self) -> None:
        """Handler to remove the selected data source."""
        # Get index and corresponding item
        idxToRemove = self._mainWin.dataSourceTree.currentIndex()
        itemToRemove = self.dataSourceModel.itemFromIndex(idxToRemove)
        dataSourceToRemove = itemToRemove.text()

        # Remove every signal associated with the data source
        for row in range(itemToRemove.rowCount()):
            sigNameToRemove = itemToRemove.child(row).text()
            # Remove plot widget
            if sigNameToRemove in self._signalPlotWidgets:
                plotWidgetToRemove = self._signalPlotWidgets.pop(sigNameToRemove)
                self._mainWin.plotsLayout.removeWidget(plotWidgetToRemove)
                plotWidgetToRemove.deleteLater()

        # Delete streaming controller and config
        del self._streamingControllers[dataSourceToRemove]
        del self._config[dataSourceToRemove]

        # Update UI data source tree
        self.dataSourceModel.removeRow(itemToRemove.row())

        # Disable start button, source deletion and signal configuration depending on the number of remaining sources
        if len(self._streamingControllers) == 0:
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
        dataSourceConfig = {
            k: v
            for k, v in self._config[dataSourceToEdit].items()
            if k != "sigsConfigs"
        }
        # print(dataSourceConfig.keys())
        dataSourceConfigDialog = DataSourceConfigDialog(
            **dataSourceConfig, parent=self._mainWin
        )
        accepted = dataSourceConfigDialog.exec()
        if not accepted:
            return
        if dialogResult is None:
            return
        # Unpack result
        newDataSourceConfig, _, _ = dialogResult

        # Update streaming controller settings
        self._streamingControllers[dataSourceToEdit].editDataSourceConfig(
            newDataSourceConfig
        )

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
        if sigName in self._signalPlotWidgets:  # case 1 & 2
            oldSignalPlotWidget = self._signalPlotWidgets.pop(sigName)

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
                self._signalPlotWidgets[sigName] = newSignalPlotWidget

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
            self._signalPlotWidgets[sigName] = newSignalPlotWidget

        # Save new settings
        self._config[dataSource]["sigsConfigs"][sigName] = sigConfig
