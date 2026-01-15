"""
Classes for the TCP socket data source.


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

from PySide6.QtCore import QByteArray, QLocale, QThread
from PySide6.QtGui import QIntValidator
from PySide6.QtNetwork import QHostAddress, QTcpServer, QTcpSocket
from PySide6.QtWidgets import QWidget

from ..ui.tcp_data_source_config_widget_ui import Ui_TCPDataSourceConfigWidget
from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)


class TCPConfigWidget(DataSourceConfigWidget, Ui_TCPDataSourceConfigWidget):
    """
    Widget to configure the socket source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        # Validation rules
        lo = QLocale()
        minPort, maxPort = 1024, 49151
        self.socketPortTextField.setToolTip(
            f"Integer between {lo.toString(minPort)} and {lo.toString(maxPort)}"
        )
        portValidator = QIntValidator(bottom=minPort, top=maxPort)
        self.socketPortTextField.setValidator(portValidator)

    def validateConfig(self) -> DataSourceConfigResult:
        """
        Validate the configuration.

        Returns
        -------
        DataSourceConfigResult
            Configuration result.
        """
        lo = QLocale()
        if not self.socketPortTextField.hasAcceptableInput():
            return DataSourceConfigResult(
                dataSourceType=DataSourceType.TCP,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "port" field is invalid.',
            )
        socketPort = lo.toInt(self.socketPortTextField.text())[0]

        return DataSourceConfigResult(
            dataSourceType=DataSourceType.TCP,
            dataSourceConfig={"socketPort": socketPort},
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
        if "socketPort" in config:
            self.socketPortTextField.setText(QLocale().toString(config["socketPort"]))

    def getFieldsInTabOrder(self) -> list[QWidget]:
        """
        Get the list of fields in tab order.

        Returns
        -------
        list of QWidgets
            List of the QWidgets in tab order.
        """
        return [self.socketPortTextField]


class TCPDataSourceWorker(DataSourceWorker):
    """
    Concrete DataSourceWorker that collects data from a TCP socket.

    Parameters
    ----------
    packetSize : int
        Size of each packet read from the socket.
    startSeq : list of bytes or float
        Sequence of commands to start the source.
    stopSeq : list of bytes or float
        Sequence of commands to stop the source.
    socketPort: int
        Socket port.

    Attributes
    ----------
    _packetSize : int
        Size of each packet read from the socket.
    _startSeq : list of bytes or float
        Sequence of commands to start the source.
    _stopSeq : list of bytes or float
        Sequence of commands to stop the source.
    _socketPort: int
        Socket port.
    _tcpServer : QTcpServer
        Instance of QTcpServer.
    _clientSock : QTcpSocket or None
        Client socket.
    _buffer : QByteArray
        Input buffer.
    _guard : bool
        Guard flag to control data emission.

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
        startSeq: list[bytes | float],
        stopSeq: list[bytes | float],
        socketPort: int,
    ) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._socketPort = socketPort

        self._tcpServer = QTcpServer(self)
        self._tcpServer.newConnection.connect(self._handleConnection)
        self._clientSock: QTcpSocket | None = None
        self._buffer = QByteArray()
        self._guard = False

    def __str__(self):
        return f"TCP socket - port {self._socketPort}"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        # Start server
        if not self._tcpServer.listen(QHostAddress.Any, self._socketPort):  # type: ignore
            errMsg = f"Cannot start TCP server due to the following error:\n{self._tcpServer.errorString()}."
            self.errorOccurred.emit(errMsg)
            logging.error(f"DataWorker: {errMsg}")
            return

        logging.info(
            f"DataWorker: waiting for TCP connection on port {self._socketPort}."
        )

    def stopCollecting(self) -> None:
        """Stop data collection."""
        # Un-set guard flag
        self._guard = False

        if self._clientSock is not None:
            # Stop command
            for c in self._stopSeq:
                if isinstance(c, (bytes, bytearray)):
                    self._clientSock.write(c)
                    self._clientSock.waitForBytesWritten(1000)
                elif isinstance(c, float):
                    QThread.msleep(int(c * 1000))

            # Close socket
            self._clientSock.close()
            self._clientSock.deleteLater()
            self._clientSock = None

        # Close server
        self._tcpServer.close()
        self._buffer = QByteArray()

        logging.info("DataWorker: TCP communication stopped.")

    def _handleConnection(self) -> None:
        """Handle a new TCP connection."""
        # If already connected, drop old client
        if self._clientSock is not None:
            try:
                self._clientSock.readyRead.disconnect(self._collectData)
            except Exception:
                pass

            # Abort and delete old client socket
            self._clientSock.abort()
            self._clientSock.deleteLater()

        # Get new client socket
        self._clientSock = self._tcpServer.nextPendingConnection()
        self._clientSock.readyRead.connect(self._collectData)

        logging.info("DataWorker: new TCP connection.")

        # Start command
        for c in self._startSeq:
            if isinstance(c, (bytes, bytearray)):
                self._clientSock.write(c)
                self._clientSock.waitForBytesWritten(1000)
            elif isinstance(c, float):
                QThread.msleep(int(c * 1000))

        logging.info("DataWorker: TCP communication started.")

        # Set guard flag
        self._guard = True

    def _collectData(self) -> None:
        """Fill input buffer when data is ready."""
        if self._clientSock is None:
            return

        # Accumulate new data
        self._buffer.append(self._clientSock.readAll())

        # Guard check
        if not self._guard:
            self._buffer.clear()
            return

        # Emit all data packets in the buffer
        while self._buffer.size() >= self._packetSize:
            data = self._buffer.left(self._packetSize).data()
            self.dataPacketReady.emit(data)
            self._buffer.remove(0, self._packetSize)
