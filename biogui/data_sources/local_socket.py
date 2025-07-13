"""
Classes for the local socket data source.


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

import logging
import time

from PySide6.QtCore import QByteArray
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QWidget

from ..ui.local_socket_data_source_config_widget_ui import (
    Ui_LocalSocketDataSourceConfigWidget,
)
from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)


class LocalSocketConfigWidget(
    DataSourceConfigWidget, Ui_LocalSocketDataSourceConfigWidget
):
    """
    Widget to configure the local socket source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self.destroyed.connect(self.deleteLater)

    def validateConfig(self) -> DataSourceConfigResult:
        """
        Validate the configuration.

        Returns
        -------
        DataSourceConfigResult
            Configuration result.
        """
        if self.socketPathTextField.text() == "":
            return DataSourceConfigResult(
                dataSourceType=DataSourceType.LOCAL_SOCK,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "Socket path" field is empty.',
            )

        return DataSourceConfigResult(
            dataSourceType=DataSourceType.LOCAL_SOCK,
            dataSourceConfig={"socketPath": self.socketPathTextField.text()},
            isValid=True,
            errMessage="",
        )

    def prefill(self, config: dict) -> None:
        """Pre-fill the form with the provided configuration.

        Parameters
        ----------
        config : dict
            Dictionary with the configuration.
        """
        if "socketPath" in config:
            self.socketPathTextField.setText(config["socketPath"])

    def getFieldsInTabOrder(self) -> list[QWidget]:
        """
        Get the list of fields in tab order.

        Returns
        -------
        list of QWidgets
            List of the QWidgets in tab order.
        """
        return [self.socketPathTextField]


class LocalSocketDataSourceWorker(DataSourceWorker):
    """
    Concrete DataSourceWorker that collects data from local sockets.

    Parameters
    ----------
    packetSize : int
        Number of bytes in the packet.
    startSeq : list of bytes
        Sequence of commands to start the source.
    stopSeq : list of bytes
        Sequence of commands to stop the source.
    socketPath : str
        Path to the local socket.

    Attributes
    ----------
    _packetSize : int
        Size of each packet read from the local socket.
    _startSeq : list of bytes
        Sequence of commands to start the source.
    _stopSeq : list of bytes
        Sequence of commands to stop the source.
    _socketPath : str
        Path to the local socket.
    _localServer : QLocalServer
        Instance of QLocalServer.
    _clientSock : QLocalSocket or None
        Client socket.
    _buffer : QByteArray
        Input buffer.

    Class attributes
    ----------------
    dataPacketReady : Signal
        Qt Signal emitted when new data is collected.
    errorOccurred : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(
        self,
        packetSize: int,
        startSeq: list[bytes],
        stopSeq: list[bytes],
        socketPath: str,
    ) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._socketPath = socketPath

        self._localServer = QLocalServer(self)
        self._localServer.newConnection.connect(self._handleConnection)
        self._clientSock: QLocalSocket | None = None
        self._buffer = QByteArray()

        self.destroyed.connect(self.deleteLater)

        self.destroyed.connect(self.deleteLater)

    def __str__(self):
        return f"Local socket - {self._socketPath}"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        # Start server
        if not self._localServer.listen(self._socketPath):
            errMsg = f"Cannot start local server due to the following error:\n{self._localServer.errorString()}."
            self.errorOccurred.emit(errMsg)
            logging.error(f"DataWorker: {errMsg}")
            return

        logging.info(f"DataWorker: waiting for local connection on {self._socketPath}.")
        self._stopReadingFlag = False

        logging.info("DataWorker: data reading started.")

    def stopCollecting(self) -> None:
        """Stop data collection."""
        if self._clientSock is not None:
            # Stop command
            for c in self._stopSeq:
                if type(c) is bytes:
                    self._clientSock.write(c)
                elif type(c) is float:
                    time.sleep(c)
            self._clientSock.flush()

            # Close socket
            self._clientSock.close()
            self._clientSock.deleteLater()
            self._clientSock = None

        # Close server
        self._localServer.close()
        self._buffer = QByteArray()

        logging.info("DataWorker: TCP communication stopped.")

    def _handleConnection(self) -> None:
        """Handle a new TCP connection."""
        self._clientSock = self._localServer.nextPendingConnection()
        self._clientSock.readyRead.connect(self._collectData)

        logging.info("DataWorker: new connection.")

        # Start command
        for c in self._startSeq:
            if type(c) is bytes:
                self._clientSock.write(c)
            elif type(c) is float:
                time.sleep(c)

        logging.info("DataWorker: TCP communication started.")

    def _collectData(self) -> None:
        """Fill input buffer when data is ready."""
        self._buffer.append(self._clientSock.readAll())  # type: ignore
        if self._buffer.size() >= self._packetSize:
            data = self._buffer.mid(0, self._packetSize).data()
            self.dataPacketReady.emit(data)
            self._buffer.remove(0, self._packetSize)
