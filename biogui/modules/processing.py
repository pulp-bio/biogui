"""
This module contains controller and widgets for custom processing configuration.


Copyright 2025 Mattia Orlandi, Pierangelo Maria Rapa

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

import importlib.util
import logging
from collections import deque, namedtuple
from itertools import islice
from typing import Callable, TypeAlias

import numpy as np
from PySide6.QtCore import QLocale, QObject, QThread, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtNetwork import QAbstractSocket, QTcpSocket
from PySide6.QtWidgets import QCheckBox, QFileDialog, QMessageBox, QWidget

from biogui.controllers import MainController
from biogui.ui.processing_config_widget_ui import Ui_ProcessingConfigWidget
from biogui.utils import SigData, instanceSlot
from biogui.views import MainWindow

ProcessFn: TypeAlias = Callable[[dict[str, np.ndarray]], bytes]
"""Type representing a processing callable class."""

ProcessingModule = namedtuple("ProcessingModule", "winLenS, stepLenS, ProcessFn")
"""Type representing the processing module to apply on the acquired data."""


def _loadProcessingScript(filePath: str) -> tuple[ProcessingModule | None, str]:
    """
    Load a processing script from a Python file.

    Parameters
    ----------
    filePath : str
        Path to Python file.

    Returns
    -------
    ProcessingModule or None
        ProcessingModule object, or None if the module is not valid.
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

    if not hasattr(module, "winLenS"):
        return (
            None,
            'The selected Python module does not contain a "winLenS" constant.',
        )
    if not hasattr(module, "stepLenS"):
        return (
            None,
            'The selected Python module does not contain a "stepLenS" variable.',
        )
    if not hasattr(module, "ProcessFn"):
        return (
            None,
            'The selected Python module does not contain a "ProcessFn" callable class.',
        )

    if not isinstance(module.winLenS, float) or module.winLenS <= 0:
        return (
            None,
            "The window length must be a positive float.",
        )
    if not isinstance(module.stepLenS, float) or module.stepLenS <= 0:
        return (
            None,
            "The step length must be a positive float",
        )

    return (
        ProcessingModule(
            winLenS=module.winLenS,
            stepLenS=module.stepLenS,
            ProcessFn=module.ProcessFn,
        ),
        "",
    )


class _ProcessingWorker(QObject):
    """
    Worker that performs custom processing on the acquired data.

    Parameters
    ----------

    Attributes
    ----------
    _buffers : dict
        Dictionary containing one buffer per signal.

    Class attributes
    ----------------
    resultReady : Signal
        Qt Signal emitted when the processed result is ready.
    """

    resultReady = Signal(bytes)

    def __init__(self) -> None:
        super().__init__()

        self._processFn = None
        self._buffers = {}

    @property
    def processFn(self) -> ProcessFn | None:
        """ProcessFn or None: Property representing the processing function."""
        return self._processFn

    @processFn.setter
    def processFn(self, processFn: ProcessFn) -> None:
        self._processFn = processFn

    def initBuffers(self, buffersConfig: dict) -> None:
        """
        Initialize the internal buffers.

        Parameters
        ----------
        buffersConfig : dict
            Dictionary containing the configuration of the buffers.
        """
        for sigName, bufferConfig in buffersConfig.items():
            self._buffers[sigName] = {
                "queue": deque(),
                "winLen": bufferConfig["winLen"],
                "stepLen": bufferConfig["stepLen"],
            }

    @instanceSlot(list)
    def process(self, dataPacket: list[SigData]) -> None:
        """
        Process the given data.

        Parameters
        ----------
        dataPacket : tuple of (str, list of SigData)
            Data to process.
        """
        if self._processFn is None:
            return None  # should never happen

        # Fill buffer
        bufferFilled = True
        for sigData in dataPacket:
            if sigData.sigName not in self._buffers:
                continue
            winLen = self._buffers[sigData.sigName]["winLen"]
            for samples in sigData.data:
                self._buffers[sigData.sigName]["queue"].append(samples)
            if len(self._buffers[sigData.sigName]["queue"]) < winLen:
                bufferFilled = False

        # Check if all buffers are full
        if bufferFilled:
            dataDict = {}
            for sigName in self._buffers:
                queue = self._buffers[sigName]["queue"]
                winLen = self._buffers[sigName]["winLen"]
                stepLen = self._buffers[sigName]["stepLen"]
                dataDict[sigName] = np.asarray(queue)[:winLen]
                # Shift by step length
                self._buffers[sigName]["queue"] = deque(
                    islice(queue, stepLen, len(queue))
                )

            # Process data
            result = self._processFn(dataDict)
            self.resultReady.emit(result)

    def reset(self) -> None:
        """Reset the worker."""
        self._buffers = {}


class _ProcessingConfigWidget(QWidget, Ui_ProcessingConfigWidget):
    """Widget providing configuration options for the custom processing."""

    def __init__(self) -> None:
        super().__init__()

        self.setupUi(self)

        # Validation rules
        lo = QLocale()
        minPort, maxPort = 1024, 49151
        self.socketPortTextField.setToolTip(
            f"Integer between {lo.toString(minPort)} and {lo.toString(maxPort)}"
        )
        portValidator = QIntValidator(bottom=minPort, top=maxPort)
        self.socketPortTextField.setValidator(portValidator)

        self._processingModule = None

        self.browseProcessingModuleButton.clicked.connect(self._browseProcessingModule)
        self.destroyed.connect(self.deleteLater)

    @property
    def processingModule(self) -> ProcessingModule | None:
        """ProcessingModule or None: Property representing the processing module."""
        return self._processingModule

    def _browseProcessingModule(self) -> None:
        """Browse files to select the module containing the processing logic."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Python module containing the processing function",
            filter="*.py",
        )
        if filePath:
            processingModule, errMessage = _loadProcessingScript(filePath)
            if processingModule is None:
                QMessageBox.critical(
                    self,
                    "Invalid Python file",
                    errMessage,
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                return

            self._processingModule = processingModule

            self.processingModulePathLabel.setText(filePath)


class ProcessingController(QObject):
    """
    Controller for custom processing.

    Attributes
    ----------
    _confWidget : _TriggerConfigWidget
        Instance of _TriggerConfigWidget.
    _streamControllers : dict of (str: StreamingController)
        Reference to the streaming controller dictionary.
    _processingWorker : _ProcessingWorker
        Worker for data processing.
    _processingThread : QThread
        The QThread associated to the processing worker.
    _socket : QTcpSocket
        TCP socket object.
    """

    def __init__(self) -> None:
        super().__init__()

        self._confWidget = _ProcessingConfigWidget()
        self._streamingControllers = {}

        self._confWidget.dataSourceComboBox.currentTextChanged.connect(
            self._onDataSourceChange
        )

        # Custom processing
        self._processingWorker = _ProcessingWorker()
        self._processingThread = QThread(self)
        self._processingWorker.moveToThread(self._processingThread)
        self._processingWorker.resultReady.connect(self._sendData)
        self._processingThread.finished.connect(self._processingWorker.reset)

        # TCP socket
        self._socket = QTcpSocket(self)
        self._socket.connected.connect(
            lambda: logging.info("Processing module: connected to server.")
        )
        self._socket.errorOccurred.connect(
            lambda: logging.info("Processing module: an error occurred.")
        )

    def subscribe(self, mainController: MainController, mainWin: MainWindow) -> None:
        """
        Subscribe to the main controller.

        Parameters
        ----------
        mainController : MainController
            Reference to the main controller.
        mainWin : MainWindow
            Reference to the main window.
        """
        # Make connections with MainWindow
        mainWin.moduleContainer.layout().addWidget(self._confWidget)  # type: ignore
        mainController.streamingStarted.connect(self._startProcessing)
        mainController.streamingStopped.connect(self._stopProcessing)
        mainController.appClosed.connect(self._stopProcessing)
        mainController.streamingControllersChanged.connect(self._rescanDataSources)

        # Get reference to StreamingControllers
        self._streamingControllers = mainController.streamingControllers

        # Populate data sources combo box
        self._rescanDataSources()

    def unsubscribe(self, mainController: MainController, mainWin: MainWindow) -> None:
        """
        Unsubscribe from the main controller.

        Parameters
        ----------
        mainController : MainController
            Reference to the main controller.
        mainWin : MainWindow
            Reference to the main window.
        """
        # Undo connections with MainWindow
        mainWin.moduleContainer.layout().removeWidget(self._confWidget)  # type: ignore
        self._confWidget.deleteLater()
        mainController.streamingStarted.disconnect(self._startProcessing)
        mainController.streamingStopped.disconnect(self._stopProcessing)
        mainController.appClosed.disconnect(self._stopProcessing)

    def _onDataSourceChange(self, dataSource: str) -> None:
        """Detect if the selected data source has changed."""
        if dataSource not in self._streamingControllers:
            return

        # Clear layout
        layout = self._confWidget.signalsGroupBox.layout()
        if layout is None:  # should never happen
            return
        while layout.count():
            item = layout.takeAt(0)
            item.widget().deleteLater()

        # Add checkboxes
        for sigName in self._streamingControllers[dataSource].sigInfo.keys():
            checkBox = QCheckBox(sigName, parent=self._confWidget.signalsGroupBox)
            checkBox.setProperty("sigName", sigName)
            checkBox.setChecked(True)
            layout.addWidget(checkBox)

        self._streamingControllers[dataSource].signalsReady.connect(
            self._processingWorker.process
        )

    def _rescanDataSources(self) -> None:
        """Rescan the configured data sources."""
        self._confWidget.dataSourceComboBox.clear()
        self._confWidget.dataSourceComboBox.addItems(
            list(self._streamingControllers.keys())
        )

    def _sendData(self, data: bytes) -> None:
        """Send data via TCP socket."""
        if self._socket.state() == QAbstractSocket.ConnectedState:  # type: ignore
            self._socket.write(data)
            self._socket.flush()

    def _startProcessing(self) -> None:
        """Start the custom processing."""
        self._confWidget.customProcessingGroupBox.setEnabled(False)
        layout = self._confWidget.signalsGroupBox.layout()
        if (
            not self._confWidget.customProcessingGroupBox.isChecked()
            or self._confWidget.processingModule is None
            or layout is None  # should never happen
        ):
            return

        if not self._confWidget.socketPortTextField.hasAcceptableInput():
            QMessageBox.critical(
                self._confWidget,
                "Invalid configuration",
                "The provided socket port is not valid.",
                buttons=QMessageBox.Retry,  # type: ignore
                defaultButton=QMessageBox.Retry,  # type: ignore
            )
            return

        # Compute buffer sizes for the signals of interest
        streamingController = self._streamingControllers[
            self._confWidget.dataSourceComboBox.currentText()
        ]
        winLenS = self._confWidget.processingModule.winLenS
        stepLenS = self._confWidget.processingModule.stepLenS
        buffersConfig = {}
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is None:  # should never happen
                continue
            checkBox: QCheckBox = layout.itemAt(i).widget()  # type: ignore
            if not checkBox.isChecked():
                continue
            sigName = checkBox.property("sigName")
            fs = streamingController.sigInfo[sigName]["fs"]
            winLen = int(round(winLenS * fs))
            stepLen = int(round(stepLenS * fs))
            buffersConfig[sigName] = {"winLen": winLen, "stepLen": stepLen}
        self._processingWorker.processFn = self._confWidget.processingModule.ProcessFn()
        self._processingWorker.initBuffers(buffersConfig)

        # Connect to TCP server
        socketPort = QLocale().toInt(self._confWidget.socketPortTextField.text())[0]
        self._socket.connectToHost(
            self._confWidget.socketAddressTextField.text(), socketPort
        )

        # Start thread
        self._processingThread.start()

    def _stopProcessing(self) -> None:
        """Stop custom processing."""
        self._confWidget.customProcessingGroupBox.setEnabled(True)
        # Stop thread
        self._processingThread.quit()
        self._processingThread.wait()
        if self._socket.state() == QAbstractSocket.ConnectedState:  # type: ignore
            self._socket.disconnectFromHost()
