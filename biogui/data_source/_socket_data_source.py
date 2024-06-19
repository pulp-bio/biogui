"""Classes for the TCP socket data source.


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

import logging

from PySide6.QtCore import QByteArray
from PySide6.QtGui import QIntValidator
from PySide6.QtNetwork import QHostAddress, QTcpServer, QTcpSocket
from PySide6.QtWidgets import QWidget

from ..ui.ui_socket_config_widget import Ui_SocketConfigWidget
from ._abc_data_source import ConfigResult, ConfigWidget, DataSource, DataSourceType


class SocketConfigWidget(ConfigWidget, Ui_SocketConfigWidget):
    """Widget to configure the socket source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        # Validation rules
        minPort, maxPort = 1024, 49151
        self.portTextField.setToolTip(f"Integer between {minPort} and {maxPort}")
        portValidator = QIntValidator(bottom=minPort, top=maxPort)
        self.portTextField.setValidator(portValidator)

    def validateConfig(self) -> ConfigResult:
        """Validate the configuration.

        Returns
        -------
        ConfigResult
            Configuration result.
        """
        if not self.portTextField.hasAcceptableInput():
            return ConfigResult(
                dataSourceType=DataSourceType.SOCKET,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "port" field is invalid.',
            )

        socketPort = int(self.portTextField.text())
        return ConfigResult(
            dataSourceType=DataSourceType.SOCKET,
            dataSourceConfig={"socketPort": socketPort},
            isValid=True,
            errMessage="",
        )


class SocketDataSource(DataSource):
    """Concrete worker that collects data from a TCP socket.

    Parameters
    ----------
    packetSize : int
        Size of each packet read from the socket.
    startSeq : list of bytes
        Sequence of commands to start the source.
    stopSeq : list of bytes
        Sequence of commands to stop the source.
    socketPort: int
        Socket port.

    Attributes
    ----------
    _packetSize : int
        Size of each packet read from the socket.
    _startSeq : list of bytes
        Sequence of commands to start the source.
    _stopSeq : list of bytes
        Sequence of commands to stop the source.
    _tcpServer : QTcpServer
        Instance of QTcpServer.
    _clientSock : QTcpSocket or None
        Client socket.
    _socketPort: int
        Socket port.
    _buffer : QByteArray
        Input buffer.

    Class attributes
    ----------------
    dataReadySig : Signal
        Qt Signal emitted when new data is collected.
    errorSig : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(
        self,
        packetSize: int,
        startSeq: list[bytes],
        stopSeq: list[bytes],
        socketPort: int,
    ) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._tcpServer = QTcpServer(self)
        self._tcpServer.newConnection.connect(self._handleConnection)
        self._clientSock: QTcpSocket | None = None
        self._socketPort = socketPort
        self._buffer = QByteArray()

    def __str__(self):
        return f"TCP socket - port {self._socketPort}"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        # Start server
        if not self._tcpServer.listen(QHostAddress.Any, self._socketPort):
            self.errorSig.emit(
                f"Cannot start TCP server: {self._tcpServer.errorString()}."
            )
            logging.error("DataWorker: cannot start TCP server.")
            return

        logging.info(
            f"DataWorker: waiting for TCP connection on port {self._socketPort}."
        )

    def stopCollecting(self) -> None:
        """Stop data collection."""
        # Stop command
        for c in self._stopSeq:
            self._clientSock.write(c)
        self._clientSock.flush()

        # Reset input buffer and close socket and server
        # while self._clientSock.waitForReadyRead(200):
        #     self._clientSock.readAll()
        self._clientSock.close()
        self._tcpServer.close()
        self._buffer = QByteArray()

    def _handleConnection(self) -> None:
        """Handle a new TCP connection."""
        self._clientSock = self._tcpServer.nextPendingConnection()
        self._clientSock.readyRead.connect(self._collectData)
        self._clientSock.disconnected.connect(self._clientSock.deleteLater)

        logging.info("DataWorker: new TCP connection.")

        # Start command
        for c in self._startSeq:
            self._clientSock.write(c)

    def _collectData(self) -> None:
        """Fill input buffer when data is ready."""
        self._buffer.append(self._clientSock.readAll())
        if len(self._buffer) >= self._packetSize:
            data = self._buffer.mid(0, self._packetSize).data()
            self.dataReadySig.emit(data)
            self._buffer.remove(0, self._packetSize)
