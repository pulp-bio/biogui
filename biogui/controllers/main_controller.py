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

from PySide6.QtCore import QModelIndex, QObject, Signal, Slot
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QMessageBox

from biogui.views import (
    AddDataSourceDialog,
    AddSignalDialog,
    MainWindow,
    SignalPlotWidget,
)

from .streaming_controller import (
    DataPacket,
    DecodeFn,
    InterfaceModule,
    StreamingController,
)


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
    _sigPlotWidgets : dict of (str: SignalPlotWidget)
        Collection of SignalPlotWidget objects, indexed by the name of the corresponding signal.
    _config : dict
        Configuration of the signals.

    Class attributes
    ----------------
    startStreamingSig : Signal
        Qt Signal emitted when streaming starts.
    stopStreamingSig : Signal
        Qt Signal emitted when streaming stops.
    closeSig : Signal
        Qt Signal emitted when the application is closed.
    dataReadySig : Signal
        Qt Signal emitted when new filtered data is available.
    newSourceAddedSig : Signal
        Qt Signal emitted when a new source is added.
    """

    startStreamingSig = Signal()
    stopStreamingSig = Signal()
    closeSig = Signal()
    dataReadySig = Signal(DataPacket)
    newSourceAddedSig = Signal(StreamingController)

    def __init__(self, mainWin: MainWindow) -> None:
        super().__init__()
        self._mainWin = mainWin
        self._streamingControllers: dict[str, StreamingController] = {}
        self._sigPlotWidgets: dict[str, SignalPlotWidget] = {}
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
        self._mainWin.editSignalButton.clicked.connect(self._editSignalHandler)
        self._mainWin.dataSourceTree.clicked.connect(self._enableButtons)

        # Streaming
        self._mainWin.startStreamingButton.clicked.connect(self._startStreaming)
        self._mainWin.stopStreamingButton.clicked.connect(self._stopStreaming)

    def _startStreaming(self) -> None:
        """Start streaming."""
        # Handle UI elements
        self._mainWin.startStreamingButton.setEnabled(False)
        self._mainWin.stopStreamingButton.setEnabled(True)
        self._mainWin.streamConfGroupBox.setEnabled(False)

        # Start all StreamingController objects
        for streamController in self._streamingControllers.values():
            streamController.startStreaming()

        # Emit "start" Qt Signal (for pluggable modules)
        self.startStreamingSig.emit()

    def _stopStreaming(self) -> None:
        """Stop streaming."""
        # Stop all StreamingController objects
        for streamController in self._streamingControllers.values():
            streamController.stopStreaming()

        # Emit "stop" Qt Signal (for pluggable modules)
        self.stopStreamingSig.emit()

        # Handle UI elements
        self._mainWin.streamConfGroupBox.setEnabled(True)
        self._mainWin.startStreamingButton.setEnabled(True)
        self._mainWin.stopStreamingButton.setEnabled(False)

    @Slot(DataPacket)
    def _plotData(self, dataPacket: DataPacket):
        """Plot the given data on the corresponding plot.

        Parameters
        ----------
        dataPacket : DataPacket
            Data to plot.
        """
        self._sigPlotWidgets[dataPacket.id].addData(dataPacket.data)

    @Slot(str)
    def _handleErrors(self, errMessage: str) -> None:
        """When an error occurs, display an alert and stop streaming."""
        self._stopStreaming()
        QMessageBox.critical(
            self._mainWin,
            "Streaming error",
            errMessage,
            buttons=QMessageBox.Retry,  # type: ignore
            defaultButton=QMessageBox.Retry,  # type: ignore
        )

    def _addDataSourceHandler(self) -> None:
        """Handler for adding a new data source."""
        # Open the dialog
        dialogResult = self._getDataSourceConfig()
        if dialogResult is None:
            return
        # Unpack result
        dataSourceConfig, sigsInfo, decodeFn = dialogResult

        # Add signals
        config = {}
        for sigName, sigInfo in sigsInfo.items():
            # Open the dialog
            dialogResult = self._getSignalConfig(sigName, sigInfo["fs"], sigInfo["nCh"])
            if dialogResult is None:
                return
            # Unpack result
            config[sigName] = dialogResult

        # Create streaming controller
        streamingController = StreamingController(
            dataSourceConfig, decodeFn, config, self
        )
        self._streamingControllers[str(streamingController)] = streamingController

        # Create plot widget
        for sigName in config.keys():
            sigPlotWidget = SignalPlotWidget(
                sigName, **config[sigName], parent=self._mainWin
            )
            self.startStreamingSig.connect(sigPlotWidget.startTimers)
            self.stopStreamingSig.connect(sigPlotWidget.stopTimers)
            self._mainWin.plotsLayout.addWidget(sigPlotWidget)

            self._sigPlotWidgets[sigName] = sigPlotWidget

        # Save configuration
        self._config[str(streamingController)] = config

        # Configure Qt Signals
        streamingController.dataReadySig.connect(self._plotData)
        streamingController.errorSig.connect(self._handleErrors)
        streamingController.dataReadySig.connect(
            lambda d: self.dataReadySig.emit(d)
        )  # forward Qt Signal for filtered data

        # Update UI data source tree
        dataSourceNode = QStandardItem(str(streamingController))
        self.dataSourceModel.appendRow(dataSourceNode)
        dataSourceNode.appendRows([QStandardItem(sigName) for sigName in config.keys()])

        # Emit signal to inform pluggable modules that a new source has been added
        self.newSourceAddedSig.emit(streamingController)

        # Enable start button
        self._mainWin.startStreamingButton.setEnabled(True)

    def _getDataSourceConfig(
        self, addDataSourceDialog: AddDataSourceDialog | None = None
    ) -> tuple[dict, dict, DecodeFn] | None:
        """Get the data source configuration from the user."""
        if addDataSourceDialog is None:
            addDataSourceDialog = AddDataSourceDialog(self._mainWin)

        accepted = addDataSourceDialog.exec()
        if not accepted:
            return None

        # Check if input is valid
        if not addDataSourceDialog.isValid:
            QMessageBox.critical(
                self._mainWin,
                "Invalid source",
                addDataSourceDialog.errMessage,
                buttons=QMessageBox.Retry,  # type: ignore
                defaultButton=QMessageBox.Retry,  # type: ignore
            )
            return self._getDataSourceConfig(addDataSourceDialog)  # re-open dialog

        # Read configuration
        dataSourceConfig = addDataSourceDialog.dataSourceConfig
        interfaceModule: InterfaceModule = dataSourceConfig.pop("interfaceModule")
        dataSourceConfig["packetSize"] = interfaceModule.packetSize
        dataSourceConfig["startSeq"] = interfaceModule.startSeq
        dataSourceConfig["stopSeq"] = interfaceModule.stopSeq
        sigsInfo = {}
        for sigName, fs, nCh in zip(
            interfaceModule.sigNames, interfaceModule.fs, interfaceModule.nCh
        ):
            sigsInfo[sigName] = {"fs": fs, "nCh": nCh}

        return dataSourceConfig, sigsInfo, interfaceModule.decodeFn

    def _getSignalConfig(
        self,
        sigName: str,
        fs: float,
        nCh: int,
        addSignalDialog: AddSignalDialog | None = None,
        **kwargs: dict,
    ) -> dict | None:
        """Get the signal configuration from the user."""
        if addSignalDialog is None:
            addSignalDialog = AddSignalDialog(
                sigName,
                fs,
                nCh,
                self._mainWin,
                **kwargs,
            )

        accepted = addSignalDialog.exec()
        if not accepted:
            return None

        # Check if input is valid
        if not addSignalDialog.isValid:
            QMessageBox.critical(
                self._mainWin,
                "Invalid signal",
                addSignalDialog.errMessage,
                buttons=QMessageBox.Retry,  # type: ignore
                defaultButton=QMessageBox.Retry,  # type: ignore
            )
            return self._getSignalConfig(
                sigName,
                fs,
                nCh,
                addSignalDialog,
                **kwargs,
            )  # re-open dialog

        return addSignalDialog.sigConfig

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
            plotWidgetToRemove = self._sigPlotWidgets.pop(sigNameToRemove)
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
            self._mainWin.deleteDataSourceButton.setEnabled(False)

    def _editSignalHandler(self) -> None:
        """Handler for editing the signal configuration."""
        # Get index and corresponding item
        idxToEdit = self._mainWin.dataSourceTree.currentIndex()
        itemToEdit = self.dataSourceModel.itemFromIndex(idxToEdit)
        sigName = itemToEdit.text()
        dataSource = itemToEdit.parent().text()

        # Open the dialog
        dialogResult = self._getSignalConfig(
            sigName, **self._config[dataSource][sigName]
        )
        if dialogResult is None:
            return
        # Unpack result
        sigConfig = dialogResult

        # Update streaming controller settings
        self._streamingControllers[dataSource].editConfig(sigName, sigConfig)

        # Re-create plot widget
        oldPlotWidget = self._sigPlotWidgets.pop(sigName)
        newPlotWidget = SignalPlotWidget(
            sigName,
            **sigConfig,
            parent=self._mainWin,
            dataQueue=oldPlotWidget.dataQueue,  # type: ignore
        )
        self.startStreamingSig.connect(newPlotWidget.startTimers)
        self.stopStreamingSig.connect(newPlotWidget.stopTimers)
        self._mainWin.plotsLayout.replaceWidget(oldPlotWidget, newPlotWidget)
        oldPlotWidget.deleteLater()
        self.startStreamingSig.connect(newPlotWidget.startTimers)
        self.stopStreamingSig.connect(newPlotWidget.stopTimers)

        self._sigPlotWidgets[sigName] = newPlotWidget

        # Save new settings
        self._config[dataSource][sigName] = sigConfig

    @Slot(QModelIndex)
    def _enableButtons(self, idx: QModelIndex):
        """Enable buttons to configure sources or signals."""
        if self.dataSourceModel.hasChildren(idx):  # data source
            self._mainWin.deleteDataSourceButton.setEnabled(True)
            self._mainWin.editSignalButton.setEnabled(False)
        else:  # signal
            self._mainWin.deleteDataSourceButton.setEnabled(False)
            self._mainWin.editSignalButton.setEnabled(True)
