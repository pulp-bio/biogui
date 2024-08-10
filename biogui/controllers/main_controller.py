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

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QMessageBox, QWidget

from biogui.signal_plot import SignalPlotWidget
from biogui.views import AddDataSourceDialog, AddSignalDialog, MainWindow

from .streaming_controller import DataPacket, StreamingController


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
    _dataSourceConfigs : dict of (str: dict)
        Collection of DataSource configurations, indexed by their name.
    _signalConfigs : dict of (str: dict)
        Collection of signal configurations, indexed by the name of the DataSource to which they belong.
    _streamingControllers : dict of (str: dict)
        Collection of StreamingController objects, indexed by the name of the corresponding DataSource.

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
        self._dataSourceConfigs = {}
        self._signalConfigs = {}
        self._streamingControllers = {}

        self._connectSignals()

    def addConfWidget(self, widget: QWidget) -> None:
        """
        Add a widget to configure pluggable modules.

        Parameters
        ----------
        widget : QWidget
            Widget to display.
        """
        self._mainWin.moduleContainer.layout().addWidget(widget)

    def _connectSignals(self) -> None:
        """Connect Qt signals and slots."""
        # Data source and signal management
        self._mainWin.addDataSourceButton.clicked.connect(self._addDataSourceHandler)
        self._mainWin.deleteDataSourceButton.clicked.connect(self._deleteSourceHandler)
        self._mainWin.dataSourceList.itemClicked.connect(
            lambda: self._mainWin.deleteDataSourceButton.setEnabled(True)
        )
        self._mainWin.sigNameList.itemClicked.connect(self._enableMoveButtons)

        # Streaming
        self._mainWin.startStreamingButton.clicked.connect(self._startStreaming)
        self._mainWin.stopStreamingButton.clicked.connect(self._stopStreaming)

    def _startStreaming(self) -> None:
        """Start streaming."""
        # Validate settings
        if len(self._mainWin.sigPlotWidgets) == 0:
            QMessageBox.critical(
                self._mainWin,
                "Invalid configuration",
                "There are no configured signals.",
                buttons=QMessageBox.Retry,  # type: ignore
                defaultButton=QMessageBox.Retry,  # type: ignore
            )
            return

        # Handle UI elements
        self._mainWin.startStreamingButton.setEnabled(False)
        self._mainWin.stopStreamingButton.setEnabled(True)
        self._mainWin.streamConfGroupBox.setEnabled(False)

        # Start all StreamController objects
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
        self._mainWin.sigPlotWidgets[dataPacket.id].addData(dataPacket.data)

    @Slot(str)
    def _handleErrors(self, errMessage: str) -> None:
        """When an error occurs, display an alert and stop streaming."""
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
        self._openDataSourceDialog()

    def _deleteSourceHandler(self) -> None:
        """Handler to remove the selected source."""
        # Get corresponding index
        idxToRemove = self._mainWin.dataSourceList.currentRow()

        # Update UI list
        sourceToRemove = self._mainWin.dataSourceList.takeItem(idxToRemove).text()

        # Remove every signal associated with the source
        for sigNameToRemove in self._source2sigMap[sourceToRemove]:
            # Remove plot widget
            plotWidgetToRemove = self._sigPlotWidgets.pop(sigNameToRemove)
            self.plotsLayout.removeWidget(plotWidgetToRemove)
            plotWidgetToRemove.deleteLater()

            # Update UI list
            itemToRemove = self.sigNameList.findItems(sigNameToRemove, Qt.MatchExactly)[0]  # type: ignore
            self.sigNameList.takeItem(self.sigNameList.row(itemToRemove))

            # Handle mapping
            del self._sig2sourceMap[sigNameToRemove]

        # Handle mapping
        del self._source2sigMap[sourceToRemove]

        # Delete streaming controller
        del self._streamControllers[sourceToRemove]

        # Disable signal configuration and source deletion depending on the number of remaining sources
        if len(self._streamControllers) == 0:
            self.deleteSourceButton.setEnabled(False)
            self.signalsGroupBox.setEnabled(False)

    def _openDataSourceDialog(
        self, addDataSourceDialog: AddDataSourceDialog | None = None
    ):
        """Open the dialog for adding data sources."""
        if addDataSourceDialog is None:
            addDataSourceDialog = AddDataSourceDialog(self._mainWin)

        accepted = addDataSourceDialog.exec()
        if accepted:
            # Check if input is valid
            if not addDataSourceDialog.isValid:
                QMessageBox.critical(
                    self._mainWin,
                    "Invalid source",
                    addDataSourceDialog.errMessage,
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                self._openDataSourceDialog(addDataSourceDialog)  # re-open dialog
                return

            # Read configuration
            dataSourceConfig = addDataSourceDialog.dataSourceConfig
            interfaceModule = dataSourceConfig.pop("interfaceModule")
            dataSourceConfig["packetSize"] = interfaceModule.packetSize
            dataSourceConfig["startSeq"] = interfaceModule.startSeq
            dataSourceConfig["stopSeq"] = interfaceModule.stopSeq
            # Create streaming controller
            streamingController = StreamingController(
                dataSourceConfig, interfaceModule.decodeFn, self
            )
            self._dataSourceConfigs[str(streamingController)] = dataSourceConfig
            self._signalConfigs[str(streamingController)] = []
            self._streamingControllers[str(streamingController)] = streamingController

            # Configure Qt Signals
            streamingController.dataReadySig.connect(self._plotData)
            streamingController.errorSig.connect(self._handleErrors)
            streamingController.dataReadySig.connect(
                lambda d: self.dataReadySig.emit(d)
            )  # forward Qt Signal for filtered data

            # Update UI list
            self._mainWin.dataSourceList.addItem(str(streamingController))

            # Enable signal configuration
            if not self._mainWin.signalsGroupBox.isEnabled():
                self._mainWin.signalsGroupBox.setEnabled(True)

            # Add signals
            for sigName, nCh, fs in zip(
                interfaceModule.sigNames, interfaceModule.nCh, interfaceModule.fs
            ):
                self._openAddSignalDialog(str(streamingController), sigName, nCh, fs)

            self.newSourceAddedSig.emit(streamingController)

    def _openAddSignalDialog(
        self,
        sourceName: str,
        sigName: str,
        nCh: int,
        fs: float,
        addSignalDialog: AddSignalDialog | None = None,
    ):
        """Open the dialog for adding signals."""
        if addSignalDialog is None:
            addSignalDialog = AddSignalDialog(
                sourceName, sigName, nCh, fs, self._mainWin
            )

        accepted = addSignalDialog.exec()
        if accepted:
            # Check if input is valid
            if not addSignalDialog.isValid:
                QMessageBox.critical(
                    self._mainWin,
                    "Invalid signal",
                    addSignalDialog.errMessage,
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                self._openAddSignalDialog(
                    sourceName, sigName, nCh, fs, addSignalDialog
                )  # re-open dialog
                return

            # Connect to streaming controller
            source = addSignalDialog.signalConfig["source"]
            streamController = self._streamingControllers[source]
            sigName = addSignalDialog.signalConfig["sigName"]
            streamController.addSigName(sigName)

            # Configure filtering
            if "filtType" in addSignalDialog.signalConfig:
                filtSettings = {
                    "filtType": addSignalDialog.signalConfig["filtType"],
                    "freqs": addSignalDialog.signalConfig["freqs"],
                    "filtOrder": addSignalDialog.signalConfig["filtOrder"],
                    "fs": addSignalDialog.signalConfig["fs"],
                    "nCh": addSignalDialog.signalConfig["nCh"],
                }
                streamController.addFiltSettings(sigName, filtSettings)

            # Configure file saving
            if "filePath" in addSignalDialog.signalConfig:
                streamController.addFileSavingSettings(
                    sigName, addSignalDialog.signalConfig["filePath"]
                )

            # Create plot widget
            nCh = addSignalDialog.signalConfig["nCh"]
            fs = addSignalDialog.signalConfig["fs"]
            renderLen = addSignalDialog.signalConfig["renderLen"]
            chSpacing = addSignalDialog.signalConfig["chSpacing"]
            sigPlotWidget = SignalPlotWidget(sigName, nCh, fs, renderLen, chSpacing)
            self._mainWin.sigPlotWidgets[sigName] = sigPlotWidget
            self._mainWin.plotsLayout.addWidget(sigPlotWidget)

            # Handle mappings
            self._signalConfigs[source].append(sigName)

            # Update UI list
            self._mainWin.sigNameList.addItem(sigName)

            # Re-adjust layout
            self._mainWin.adjustLayout()

    def _enableMoveButtons(self) -> None:
        """Enable buttons to move signals up/down."""
        flag = len(self.sigPlotWidgets) >= 2
        self.moveUpButton.setEnabled(flag)
        self.moveDownButton.setEnabled(flag)

    def _moveSignal(self, up: bool) -> None:
        """Move signal up/down."""
        # Get the indexes of the elements to swap
        idxFrom = self.sigNameList.currentRow()
        idxTo = (
            max(0, idxFrom - 1)
            if up
            else min(len(self.sigPlotWidgets) - 1, idxFrom + 1)
        )
        if idxFrom == idxTo:
            return

        # Swap list items and plot widgets
        item = self.sigNameList.takeItem(idxFrom)
        self.sigNameList.insertItem(idxTo, item)
        plotWidget = self.sigPlotWidgets[item.text()]
        self.plotsLayout.removeWidget(plotWidget)
        self.plotsLayout.insertWidget(idxTo, plotWidget)

        # Re-adjust layout
        self._mainWin.adjustLayout()
