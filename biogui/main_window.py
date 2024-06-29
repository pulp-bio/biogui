"""
This module contains the main window of the app.


Copyright 2023 Mattia Orlandi, Pierangelo Maria Rapa

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

import datetime
import importlib.util
import logging
import os

from PySide6.QtCore import QLocale, Qt, Signal, Slot
from PySide6.QtGui import QDoubleValidator, QIcon, QIntValidator, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from . import data_source
from .data_source import DataSourceType
from .signal_plot import SignalPlotWidget
from .stream_controller import DataPacket, InterfaceModule, StreamingController
from .ui.ui_add_signal_dialog import Ui_AddSignalDialog
from .ui.ui_add_source_dialog import Ui_AddSourceDialog
from .ui.ui_main_window import Ui_MainWindow


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


class _AddSourceDialog(QDialog, Ui_AddSourceDialog):
    """
    Dialog for adding a new source.

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
            list(map(lambda sourceType: sourceType.value, DataSourceType))
        )
        self.sourceComboBox.currentTextChanged.connect(self._onSourceChange)

        # Source type (default is serial port)
        self._configWidget = data_source.getConfigWidget(DataSourceType.SERIAL, self)
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
        self._configWidget = data_source.getConfigWidget(
            DataSourceType(self.sourceComboBox.currentText()), self
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


class _AddSignalDialog(QDialog, Ui_AddSignalDialog):
    """
    Dialog for adding a new signal to plot.

    Parameters
    ----------
    sourceName : str
        Name of the source.
    sigName : str
        Name of the signal.
    nCh : int
        Number of channels.
    fs : float
        Sampling frequency.
    parent : QWidget or None, default=None
        Parent widget.
    """

    def __init__(
        self,
        sourceName: str,
        sigName: str,
        nCh: int,
        fs: float,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self.buttonBox.accepted.connect(self._formValidationHandler)
        self.buttonBox.rejected.connect(self.close)
        self.filtTypeComboBox.currentTextChanged.connect(self._onFiltTypeChange)
        self.browseOutDirButton.clicked.connect(self._browseOutDir)

        self.sourceNameLabel.setText(sourceName)
        self.sigNameLabel.setText(sigName)
        self.nChLabel.setText(str(nCh))
        self.freqLabel.setText(str(fs))

        # Validation rules
        nDec = 3
        minFreq, maxFreq = 1 * 10 ** (-nDec), 20_000.0
        minOrd, maxOrd = 1, 20

        self.freq1TextField.setToolTip(
            f"Float between {minFreq:.3f} and {maxFreq / 2:.3f}"
        )
        self.freq2TextField.setToolTip(
            f"Float between {minFreq:.3f} and {maxFreq / 2:.3f}"
        )
        freqValidator = QDoubleValidator(bottom=minFreq, top=maxFreq / 2, decimals=nDec)
        freqValidator.setNotation(QDoubleValidator.StandardNotation)  # type: ignore
        self.freq1TextField.setValidator(freqValidator)
        self.freq2TextField.setValidator(freqValidator)

        self.filtOrderTextField.setToolTip(f"Integer between {minOrd} and {maxOrd}")
        orderValidator = QIntValidator(bottom=minOrd, top=maxOrd)
        self.filtOrderTextField.setValidator(orderValidator)

        chSpacingValidator = QIntValidator(bottom=0, top=2147483647)
        self.chSpacingTextField.setValidator(chSpacingValidator)
        renderLenValidator = QIntValidator(bottom=1, top=8)
        self.renderLenTextField.setValidator(renderLenValidator)

        self._signalConfig = {}
        self._signalConfig["source"] = sourceName
        self._signalConfig["sigName"] = sigName
        self._signalConfig["nCh"] = nCh
        self._signalConfig["fs"] = fs
        self._isValid = False
        self._errMessage = ""

        self.destroyed.connect(self.deleteLater)

    @property
    def signalConfig(self) -> dict:
        """dict: Property for getting the dictionary with the signal configuration."""
        return self._signalConfig

    @property
    def isValid(self) -> bool:
        """bool: Property representing whether the form is valid."""
        return self._isValid

    @property
    def errMessage(self) -> str:
        """str: Property for getting the error message if the form is not valid."""
        return self._errMessage

    def _onFiltTypeChange(self) -> None:
        """Detect if filter type has changed."""
        filtType = self.filtTypeComboBox.currentText()
        # Disable field for second frequency depending on the filter type
        if filtType in ("highpass", "lowpass"):
            self.freq2TextField.setEnabled(False)
            self.freq2TextField.clear()
        else:
            self.freq2TextField.setEnabled(True)

    def _browseOutDir(self) -> None:
        """Browse directory where the data will be saved."""
        outDirPath = QFileDialog.getExistingDirectory(
            self,
            "Select destination directory",
            os.getcwd(),
            QFileDialog.ShowDirsOnly,
        )
        if outDirPath != "":
            self._signalConfig["filePath"] = outDirPath

            displayText = (
                outDirPath
                if len(outDirPath) <= 30
                else outDirPath[:13] + "..." + outDirPath[-14:]
            )
            self.outDirPathLabel.setText(displayText)
            self.outDirPathLabel.setToolTip(outDirPath)

    def _formValidationHandler(self) -> None:
        """Validate user input in the form."""
        lo = QLocale()

        nyq_fs = self._signalConfig["fs"] // 2

        # Check filtering settings
        if self.filteringGroupBox.isChecked():
            self._signalConfig["filtType"] = self.filtTypeComboBox.currentText()

            if not self.freq1TextField.hasAcceptableInput():
                self._isValid = False
                self._errMessage = 'The "Frequency 1" field is invalid.'
                return
            freq1 = lo.toFloat(self.freq1TextField.text())[0]

            if freq1 >= nyq_fs:
                self._isValid = False
                self._errMessage = "The 1st critical frequency cannot be higher than Nyquist frequency."
                return
            self._signalConfig["freqs"] = [freq1]

            if self.freq2TextField.isEnabled():
                if not self.freq2TextField.hasAcceptableInput():
                    self._isValid = False
                    self._errMessage = 'The "Frequency 2" field is invalid.'
                    return
                freq2 = lo.toFloat(self.freq2TextField.text())[0]

                if freq2 >= nyq_fs:
                    self._isValid = False
                    self._errMessage = "The 2nd critical frequency cannot be higher than Nyquist frequency."
                    return
                if freq2 <= freq1:
                    self._isValid = False
                    self._errMessage = "The 2nd critical frequency cannot be lower than the 1st critical frequency."
                    return
                self._signalConfig["freqs"].append(freq2)

            if not self.filtOrderTextField.hasAcceptableInput():
                self._isValid = False
                self._errMessage = 'The "filter order" field is invalid.'
                return
            self._signalConfig["filtOrder"] = lo.toInt(self.filtOrderTextField.text())[
                0
            ]

        # Check file saving settings
        if self.fileSavingGroupBox.isChecked():
            if "filePath" not in self._signalConfig.keys():
                self._isValid = False
                self._errMessage = "Select an output directory."
                return
            outFileName = self.fileNameTextField.text()
            if outFileName == "":
                outFileName = (
                    f"{self._signalConfig["sigName"]}_{datetime.datetime.now()}"
                    .replace(" ", "_")
                    .replace(":", "-")
                    .replace(".", "-")
                )
            outFileName = f"{outFileName}.bin"
            self._signalConfig["filePath"] = os.path.join(
                self._signalConfig["filePath"], outFileName
            )

        # Plot settings
        if not self.chSpacingTextField.hasAcceptableInput():
            self._isValid = False
            self._errMessage = 'The "channel spacing" field is invalid.'
            return
        self._signalConfig["chSpacing"] = lo.toInt(self.chSpacingTextField.text())[0]
        if not self.renderLenTextField.hasAcceptableInput():
            self._isValid = False
            self._errMessage = 'The "render length" field is invalid.'
            return
        self._signalConfig["renderLen"] = lo.toInt(self.renderLenTextField.text())[0]

        self._isValid = True


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Main window.

    Attributes
    ----------
    _streamControllers : dict of str: StreamingController
        Dictionary of StreamingController objects indexed by their string representation.
    _sigPlotWidgets : dict of str: SignalPlotWidget
        List of SignalPlotWidget objects indexed by their names.
    _source2sigMap : dict of str: list of str
        Mapping between source and signal name.
    _sig2sourceMap : dict of str: str
        Mapping between signal and source name.

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
    newSourceAddedSig = Signal(DataPacket)

    def __init__(self) -> None:
        super().__init__()

        # Setup UI
        self.setupUi(self)
        theme = self._detectTheme()
        self.editSourceButton.setIcon(QIcon.fromTheme("edit-entry", QIcon(f":icons/{theme}/edit")))
        self.deleteSourceButton.setIcon(QIcon.fromTheme("user-trash", QIcon(f":icons/{theme}/trash")))
        self.editSignalButton.setIcon(QIcon.fromTheme("edit-entry", QIcon(f":icons/{theme}/edit")))
        self.moveLeftButton.setIcon(QIcon.fromTheme("arrow-left", QIcon(f":icons/{theme}/left-arrow")))
        self.moveUpButton.setIcon(QIcon.fromTheme("arrow-up", QIcon(f":icons/{theme}/up-arrow")))
        self.moveDownButton.setIcon(QIcon.fromTheme("arrow-down", QIcon(f":icons/{theme}/down-arrow")))
        self.moveRightButton.setIcon(QIcon.fromTheme("arrow-right", QIcon(f":icons/{theme}/right-arrow")))

        self._streamControllers: dict[str, StreamingController] = {}
        self._sigPlotWidgets: dict[str, SignalPlotWidget] = {}

        # Mappings
        self._source2sigMap: dict[str, list[str]] = {}
        self._sig2sourceMap: dict[str, str] = {}

        # Source addition/removal
        self.addSourceButton.clicked.connect(self._addSourceHandler)
        self.deleteSourceButton.clicked.connect(self._deleteSourceHandler)
        self.sourceList.itemClicked.connect(
            lambda: self.deleteSourceButton.setEnabled(True)
        )

        # Signal addition/removal/moving
        # self.deleteSignalButton.clicked.connect(self._deleteSignalHandler)
        # self.sigNameList.itemClicked.connect(
        #     lambda: self.deleteSignalButton.setEnabled(True)
        # )
        # self.moveUpButton.clicked.connect(lambda: self._moveSignal(up=True))
        # self.moveDownButton.clicked.connect(lambda: self._moveSignal(up=False))
        self.sigNameList.itemClicked.connect(self._enableMoveButtons)

        # Streaming
        self.startStreamingButton.clicked.connect(self._startStreaming)
        self.stopStreamingButton.clicked.connect(self._stopStreaming)

    def addConfWidget(self, widget: QWidget) -> None:
        """
        Add a widget to configure pluggable modules.

        Parameters
        ----------
        widget : QWidget
            Widget to display.
        """
        self.moduleContainer.layout().addWidget(widget)

    def _detectTheme(self):
        """Determine whether the system theme is light or dark."""
        # Get palette of QApplication
        palette = QApplication.palette()

        # Compare the color of the background and text to infer theme
        textColor = palette.color(QPalette.Text)
        backgroundColor = palette.color(QPalette.Window)

        # Simple heuristic to determine if the theme is light or dark
        isDark = backgroundColor.lightness() < textColor.lightness()
        return "dark" if isDark else "light"

    def _addSourceHandler(self) -> None:
        """Handler to add a new source."""
        # Open the dialog
        self._openAddSourceDialog()

    def _openAddSourceDialog(self, addSourceDialog: _AddSourceDialog | None = None):
        """Open the dialog for adding sources."""
        if addSourceDialog is None:
            addSourceDialog = _AddSourceDialog(self)

        accepted = addSourceDialog.exec()
        if accepted:
            # Check if input is valid
            if not addSourceDialog.isValid:
                QMessageBox.critical(
                    self,
                    "Invalid source",
                    addSourceDialog.errMessage,
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                self._openAddSourceDialog(addSourceDialog)  # re-open dialog
                return

            # Create streaming controller
            dataSourceConfig = addSourceDialog.dataSourceConfig
            interfaceModule = dataSourceConfig.pop("interfaceModule")
            dataSourceConfig["packetSize"] = interfaceModule.packetSize
            dataSourceConfig["startSeq"] = interfaceModule.startSeq
            dataSourceConfig["stopSeq"] = interfaceModule.stopSeq
            streamController = StreamingController(
                dataSourceConfig, interfaceModule.decodeFn, self
            )
            self._streamControllers[str(streamController)] = streamController
            self._source2sigMap[str(streamController)] = []

            # Configure Qt Signals
            streamController.dataReadySig.connect(self._plotData)
            streamController.errorSig.connect(self._handleErrors)
            streamController.dataReadySig.connect(
                lambda d: self.dataReadySig.emit(d)
            )  # forward Qt Signal for filtered data

            # Update UI list
            self.sourceList.addItem(str(streamController))

            # Enable signal configuration
            if not self.signalsGroupBox.isEnabled():
                self.signalsGroupBox.setEnabled(True)

            # Add signals
            for sigName, nCh, fs in zip(
                interfaceModule.sigNames, interfaceModule.nCh, interfaceModule.fs
            ):
                self._openAddSignalDialog(str(streamController), sigName, nCh, fs)

            self.newSourceAddedSig.emit(streamController)

    def _deleteSourceHandler(self) -> None:
        """Handler to remove the selected source."""
        # Get corresponding index
        idxToRemove = self.sourceList.currentRow()

        # Update UI list
        sourceToRemove = self.sourceList.takeItem(idxToRemove).text()

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

    def _addSignalHandler(self) -> None:
        """Handler to add a new signal."""
        # Open the dialog
        self._openAddSignalDialog()

    def _openAddSignalDialog(
        self,
        sourceName: str,
        sigName: str,
        nCh: int,
        fs: float,
        addSignalDialog: _AddSignalDialog | None = None,
    ):
        """Open the dialog for adding signals."""
        if addSignalDialog is None:
            addSignalDialog = _AddSignalDialog(sourceName, sigName, nCh, fs, self)

        accepted = addSignalDialog.exec()
        if accepted:
            # Check if input is valid
            if not addSignalDialog.isValid:
                QMessageBox.critical(
                    self,
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
            streamController = self._streamControllers[source]
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
            self._sigPlotWidgets[sigName] = sigPlotWidget
            self.plotsLayout.addWidget(sigPlotWidget)

            # Handle mappings
            self._source2sigMap[source].append(sigName)
            self._sig2sourceMap[sigName] = source

            # Update UI list
            self.sigNameList.addItem(sigName)

            # Re-adjust layout
            self._adjustLayout()

    def _deleteSignalHandler(self) -> None:
        """Handler to remove the selected signal."""
        # Get corresponding index
        idxToRemove = self.sigNameList.currentRow()

        # Update UI list
        sigNameToRemove = self.sigNameList.takeItem(idxToRemove).text()

        # Handle mappings
        source = self._sig2sourceMap.pop(sigNameToRemove)
        self._source2sigMap[source].remove(sigNameToRemove)

        # Remove plot widget
        plotWidgetToRemove = self._sigPlotWidgets.pop(sigNameToRemove)
        self.plotsLayout.removeWidget(plotWidgetToRemove)
        plotWidgetToRemove.deleteLater()

        # Disconnect from streaming controller
        self._streamControllers[source].removeSigName(sigNameToRemove)

        # Re-adjust layout
        self._adjustLayout()

        # Disable signal deletion and moving, depending on the number of remaining signals
        nSig = len(self._sigPlotWidgets)
        if nSig < 2:
            self.moveUpButton.setEnabled(False)
            self.moveDownButton.setEnabled(False)
            if nSig == 0:
                self.deleteSignalButton.setEnabled(False)

    def _enableMoveButtons(self) -> None:
        """Enable buttons to move signals up/down."""
        flag = len(self._sigPlotWidgets) >= 2
        self.moveUpButton.setEnabled(flag)
        self.moveDownButton.setEnabled(flag)

    def _moveSignal(self, up: bool) -> None:
        """Move signal up/down."""
        # Get the indexes of the elements to swap
        idxFrom = self.sigNameList.currentRow()
        idxTo = (
            max(0, idxFrom - 1)
            if up
            else min(len(self._sigPlotWidgets) - 1, idxFrom + 1)
        )
        if idxFrom == idxTo:
            return

        # Swap list items and plot widgets
        item = self.sigNameList.takeItem(idxFrom)
        self.sigNameList.insertItem(idxTo, item)
        plotWidget = self._sigPlotWidgets[item.text()]
        self.plotsLayout.removeWidget(plotWidget)
        self.plotsLayout.insertWidget(idxTo, plotWidget)

        # Re-adjust layout
        self._adjustLayout()

    def _adjustLayout(self) -> None:
        """Adjust the layout of the plots."""
        stretches = map(
            lambda n: 2**n, list(range(len(self._sigPlotWidgets) - 2, -1, -1)) + [0]
        )
        for i, s in enumerate(stretches):
            self.plotsLayout.setStretch(i, s)

    def _startStreaming(self) -> None:
        """Start streaming."""
        # Validate settings
        if len(self._sigPlotWidgets) == 0:
            QMessageBox.critical(
                self,
                "Invalid configuration",
                "There are no configured signals.",
                buttons=QMessageBox.Retry,  # type: ignore
                defaultButton=QMessageBox.Retry,  # type: ignore
            )
            return

        logging.info("MainWindow: streaming started.")

        # Handle UI elements
        self.startStreamingButton.setEnabled(False)
        self.stopStreamingButton.setEnabled(True)
        self.streamConfGroupBox.setEnabled(False)

        # Start all StreamController objects
        for streamController in self._streamControllers.values():
            streamController.startStreaming()

        # Emit "start" Qt Signal (for pluggable modules)
        self.startStreamingSig.emit()

    def _stopStreaming(self) -> None:
        """Stop streaming."""
        # Stop all StreamingController objects
        for streamController in self._streamControllers.values():
            streamController.stopStreaming()

        # Emit "stop" Qt Signal (for pluggable modules)
        self.stopStreamingSig.emit()

        # Handle UI elements
        self.streamConfGroupBox.setEnabled(True)
        self.startStreamingButton.setEnabled(True)
        self.stopStreamingButton.setEnabled(False)

        logging.info("MainWindow: streaming stopped.")

    @Slot(str)
    def _handleErrors(self, errMessage: str) -> None:
        """When an error occurs, display an alert and stop streaming."""
        QMessageBox.critical(
            self,
            "Streaming error",
            errMessage,
            buttons=QMessageBox.Retry,  # type: ignore
            defaultButton=QMessageBox.Retry,  # type: ignore
        )

    @Slot(DataPacket)
    def _plotData(self, dataPacket: DataPacket):
        """Plot the given data on the corresponding plot.

        Parameters
        ----------
        dataPacket : DataPacket
            Data to plot.
        """
        self._sigPlotWidgets[dataPacket.id].addData(dataPacket.data)
