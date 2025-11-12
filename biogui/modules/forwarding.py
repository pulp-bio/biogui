"""
This module contains controller and widgets to configure forwarding.


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

import logging
import socket
from collections import deque
from itertools import islice
from sys import platform
from types import MappingProxyType

import numpy as np
from PySide6.QtCore import Qt, QLocale, QObject, QThread, Signal
from PySide6.QtGui import QIntValidator, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QMessageBox, QWidget

from biogui.controllers import MainController
from biogui.ui.forwarding_config_widget_ui import Ui_ForwardingConfigWidget
from biogui.utils import SigData, Slot
from biogui.views import MainWindow


def getCheckedSignals(dataSourceModel: QStandardItemModel) -> dict[str, list[str]]:
    """
    Get the checked signals given the data source model.

    Parameters
    ----------
    dataSourceModel : QStandardItemModel
        Model representing the data sources.

    Returns
    -------
    dict of (str: list of str)
        Dictionary containing the names of the signals to forward, grouped by data source.
    """
    checkedSigs = {}
    root = dataSourceModel.invisibleRootItem()
    for i in range(dataSourceModel.rowCount()):
        dataSourceItem = root.child(i)
        dataSourceId = dataSourceItem.text()

        for j in range(dataSourceItem.rowCount()):
            sigItem = dataSourceItem.child(j)
            sigName = sigItem.text()

            if sigItem.checkState() == Qt.Checked:  # type: ignore
                if dataSourceId not in checkedSigs:
                    checkedSigs[dataSourceId] = []
                checkedSigs[dataSourceId].append(sigName)
    return checkedSigs


class _ForwardingWorker(QObject):
    """
    Worker that forwards the acquired data.

    Attributes
    ----------
    _socket : _Socket
        Instance of _Socket.
    _buffers : dict
        Dictionary containing one buffer per signal.

    Class attributes
    ----------------
    errorOccurred : Signal
        Qt Signal emitted when an error occurs.
    """

    errorOccurred = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._socketConfig = {}
        self._socket: socket.socket | None = None
        self._connected = False
        self._buffers = {}

    @property
    def socketConfig(self) -> dict:
        """dict: Property representing the socket configuration."""
        return self._socketConfig

    @socketConfig.setter
    def socketConfig(self, socketConfig: dict) -> None:
        self._socketConfig = socketConfig

    def initBuffers(self, buffersConfig: dict) -> None:
        """
        Initialize the internal buffers.

        Parameters
        ----------
        buffersConfig : dict
            Dictionary containing the configuration of the buffers.
        """
        for dataSourceId in buffersConfig:
            self._buffers[dataSourceId] = {}
            for sigName, bufferConfig in buffersConfig[dataSourceId].items():
                self._buffers[dataSourceId][sigName] = {
                    "queue": deque(),
                    "winLen": bufferConfig["winLen"],
                    "stepLen": bufferConfig["stepLen"],
                }

    def connectToServer(self) -> None:
        """Create the socket and connect to the specified server."""
        if not self._socketConfig:  # empty configuration (should never happen)
            return

        try:
            if "socketAddress" in self._socketConfig:  # TCP socket
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.connect(
                    (
                        self._socketConfig["socketAddress"],
                        self._socketConfig["socketPort"],
                    )
                )
            else:  # Unix
                self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self._socket.connect(self._socketConfig["socketPath"])
        except Exception as e:
            self.errorOccurred.emit(f"ForwardingWorker: cannot connect to server: {e}.")
            return

        self._connected = True

    @Slot(list)
    def forward(self, dataPacket: list[SigData]) -> None:
        """
        Forward the given data.

        Parameters
        ----------
        dataPacket : tuple of (str, list of SigData)
            Data to process.
        """
        # If connection is not established, do nothing
        if self._socket is None or not self._connected:
            return

        # Get data source ID
        dataSourceId = str(self.sender())

        # Fill buffer
        for sigData in dataPacket:
            if sigData.sigName not in self._buffers[dataSourceId]:
                continue
            for samples in sigData.data:
                self._buffers[dataSourceId][sigData.sigName]["queue"].append(samples)

        # Check if all buffers are full
        while True:
            bufferFilled = all(
                len(sigBuffers["queue"]) >= sigBuffers["winLen"]
                for dataSourceBuffers in self._buffers.values()
                for sigBuffers in dataSourceBuffers.values()
            )
            if not bufferFilled:
                break

            data = bytearray()
            for dataSourceBuffers in self._buffers.values():
                for sigBuffers in dataSourceBuffers.values():
                    queue = sigBuffers["queue"]
                    winLen = sigBuffers["winLen"]
                    stepLen = sigBuffers["stepLen"]
                    # Convert to bytes
                    data.extend(np.asarray(queue)[:winLen].tobytes())
                    # Shift by step length
                    sigBuffers["queue"] = deque(islice(queue, stepLen, len(queue)))
            self._socket.sendall(data)

    def reset(self) -> None:
        """Reset the worker."""
        self._buffers = {}

        # Disconnect socket
        if self._socket is not None:
            self._socket.close()
            self._socket = None


class _ForwardingConfigWidget(QWidget, Ui_ForwardingConfigWidget):
    """Widget providing configuration options for the forwarding."""

    def __init__(self) -> None:
        super().__init__()

        self.setupUi(self)

        # Validation rules
        lo = QLocale()
        winValidator = QIntValidator(bottom=1, top=10000)
        self.winLenTextField.setValidator(winValidator)
        self.winStrideTextField.setValidator(winValidator)
        minPort, maxPort = 1024, 49151
        self.socketPortTextField.setToolTip(
            f"Integer between {lo.toString(minPort)} and {lo.toString(maxPort)}"
        )
        portValidator = QIntValidator(bottom=minPort, top=maxPort)
        self.socketPortTextField.setValidator(portValidator)

        # By default, TCP is selected -> hide Unix socket option
        self.label6.hide()
        self.socketPathTextField.hide()

        self.socketTypeComboBox.currentTextChanged.connect(self._onComboBoxChange)

        # Disable Unix socket option on Windows
        if platform == "win32":
            index = self.socketTypeComboBox.findText("Unix")
            self.socketTypeComboBox.model().item(index).setEnabled(False)  # type: ignore

    def validateConfig(self) -> tuple[dict | None, str]:
        """
        Validate the configuration.

        Returns
        -------
        dict or None
            Configuration result (or None, if invalid).
        str
            Error message (if relevant)
        """
        lo = QLocale()

        # Read and validate configuration
        config = {}

        # 1. Window settings
        if not self.winLenTextField.hasAcceptableInput():
            return None, 'The "Window length" field is invalid.'
        config["winLenS"] = lo.toFloat(self.winLenTextField.text())[0] / 1000
        if not self.winStrideTextField.hasAcceptableInput():
            return None, 'The "Window stride" field is invalid.'
        config["winStrideS"] = lo.toFloat(self.winStrideTextField.text())[0] / 1000

        # 2. Socket settings
        if self.socketTypeComboBox.currentText() == "TCP":
            if not self.socketPortTextField.hasAcceptableInput():
                return None, "The provided socket port is not valid."
            config["socketAddress"] = self.socketAddressTextField.text()
            config["socketPort"] = lo.toInt(self.socketPortTextField.text())[0]

            return config, ""

        if self.socketTypeComboBox.currentText() == "Unix":
            config["socketPath"] = self.socketPathTextField.text()

            return config, ""

        return None, "Invalid socket type"  # should never happen

    def _onComboBoxChange(self, socketType: str):
        if socketType == "TCP":
            # Show TCP options
            self.label4.show()
            self.socketAddressTextField.show()
            self.label5.show()
            self.socketPortTextField.show()
            # Hide Unix options
            self.label6.hide()
            self.socketPathTextField.hide()
        elif socketType == "Unix":
            # Hide TCP options
            self.label4.hide()
            self.socketAddressTextField.hide()
            self.label5.hide()
            self.socketPortTextField.hide()
            # Show Unix options
            self.label6.show()
            self.socketPathTextField.show()


class ForwardingController(QObject):
    """
    Controller for forwarding.

    Parameters
    ----------
    streamingControllers : MappingProxyType
        Read-only reference to the streaming controller dictionary.
    parent : QObject or None, default=None
        Parent QObject.

    Attributes
    ----------
    _streamingControllers : MappingProxyType
        Read-only reference to the streaming controller dictionary.
    _confWidget : _ForwardingConfigWidget
        Instance of _ForwardingConfigWidget.
    _forwardingWorker : _ForwardingWorker
        Worker for forwarding.
    _forwardingThread : QThread
        The QThread associated to the forwarding worker.
    """

    def __init__(
        self, streamingControllers: MappingProxyType, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)

        self._streamingControllers = streamingControllers
        self._confWidget = _ForwardingConfigWidget()

        # Forwarding worker
        self._forwardingWorker = _ForwardingWorker()
        self._forwardingThread = QThread(self)
        self._forwardingWorker.moveToThread(self._forwardingThread)

        # Connects signals
        self._forwardingThread.started.connect(self._forwardingWorker.connectToServer)
        self._forwardingThread.finished.connect(self._forwardingWorker.reset)
        self._forwardingThread.destroyed.connect(self._forwardingWorker.deleteLater)

        # Error handling
        self._forwardingWorker.errorOccurred.connect(self._handleErrors)
        self._forwardingWorker.errorOccurred.connect(
            lambda: logging.error("ForwardingWorker: cannot connect to server.")
        )

        # Setup UI data source tree
        self.dataSourceModel = QStandardItemModel(self)
        self.dataSourceModel.setHorizontalHeaderLabels(["Signals to forward"])
        self._confWidget.dataSourceTree.setModel(self.dataSourceModel)

        # Populate data sources combo box
        self._rescanDataSources()

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
        # Add configuration widget to main window
        mainWin.moduleContainer.layout().addWidget(self._confWidget)  # type: ignore

        # Make connections with main controller
        mainController.streamingStarted.connect(self._startForwarding)
        mainController.streamingStopped.connect(self._stopForwarding)
        mainController.streamingControllersChanged.connect(self._rescanDataSources)

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
        # Remove configuration widget from main window
        mainWin.moduleContainer.layout().removeWidget(self._confWidget)  # type: ignore
        self._confWidget.deleteLater()

        # Undo connections with main controller
        mainController.streamingStarted.disconnect(self._startForwarding)
        mainController.streamingStopped.disconnect(self._stopForwarding)
        mainController.streamingControllersChanged.disconnect(self._rescanDataSources)

    @Slot(str)
    def _handleErrors(self, errMessage: str) -> None:
        """When an error occurs, display an alert."""
        QMessageBox.critical(
            self._confWidget,
            "Forwarding error",
            errMessage,
            buttons=QMessageBox.Retry,  # type: ignore
            defaultButton=QMessageBox.Retry,  # type: ignore
        )

    def _rescanDataSources(self) -> None:
        """Rescan the configured data sources."""
        self.dataSourceModel.clear()
        self.dataSourceModel.setHorizontalHeaderLabels(["Signals to forward"])

        for streamingController in self._streamingControllers.values():
            # Update UI data source tree
            dataSourceNode = QStandardItem(str(streamingController))
            dataSourceNode.setEditable(False)
            self.dataSourceModel.appendRow(dataSourceNode)

            for sigName in streamingController.sigInfo:
                sigNode = QStandardItem(sigName)
                sigNode.setEditable(False)
                sigNode.setFlags(sigNode.flags() | Qt.ItemIsUserCheckable)  # type: ignore
                sigNode.setData(Qt.Unchecked, Qt.CheckStateRole)  # type: ignore
                dataSourceNode.appendRow(sigNode)

        self._confWidget.dataSourceTree.expandAll()

    def _startForwarding(self) -> None:
        """Start forwarding."""
        sigsToForward = getCheckedSignals(self.dataSourceModel)
        if not sigsToForward:  # empty
            return

        config, errMsg = self._confWidget.validateConfig()
        if config is None:
            self._handleErrors(errMsg)
            return

        # Compute buffer sizes for the signals of interest
        winLenS = config.pop("winLenS")
        winStrideS = config.pop("winStrideS")
        buffersConfig = {}
        for dataSourceId, sigNames in sigsToForward.items():
            buffersConfig[dataSourceId] = {}

            streamingController = self._streamingControllers[dataSourceId]
            for sigName in sigNames:
                fs = streamingController.sigInfo[sigName]["fs"]
                winLen = int(round(winLenS * fs))
                stepLen = int(round(winStrideS * fs))
                buffersConfig[dataSourceId][sigName] = {
                    "winLen": winLen,
                    "stepLen": stepLen,
                }

            # Connect the forwarding worker to the streaming controller
            streamingController.signalsReady.connect(self._forwardingWorker.forward)
        self._forwardingWorker.initBuffers(buffersConfig)

        # Set socket configuration
        self._forwardingWorker.socketConfig = config

        # Start thread
        self._forwardingThread.start()

    def _stopForwarding(self) -> None:
        """Stop forwarding."""
        if not self._forwardingThread.isRunning():
            return

        # Stop thread
        self._forwardingThread.quit()
        self._forwardingThread.wait()

        # Disconnect the forwarding worker from the streaming controller
        sigsToForward = getCheckedSignals(self.dataSourceModel)
        for dataSourceId in sigsToForward:
            self._streamingControllers[dataSourceId].signalsReady.disconnect(
                self._forwardingWorker.forward
            )
