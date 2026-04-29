# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Classes for the local socket data source.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QByteArray, QThread
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QWidget

from biogui.ui.ui_unix_socket_data_source_config_widget import (
    Ui_UnixSocketDataSourceConfigWidget,
)

from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)

logger = logging.getLogger(__name__)


class UnixSocketConfigWidget(
    DataSourceConfigWidget, Ui_UnixSocketDataSourceConfigWidget
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
                dataSourceType=DataSourceType.UNIX_SOCK,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "Socket path" field is empty.',
            )

        return DataSourceConfigResult(
            dataSourceType=DataSourceType.UNIX_SOCK,
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


class UnixSocketDataSourceWorker(DataSourceWorker):
    """
    Concrete DataSourceWorker that collects data from Unix sockets.

    Parameters
    ----------
    packetSize : int or list of tuple of int
        List of (header_byte, packet_size) tuples for different packet types, or a single packet size.
    startSeq : list of bytes or float
        Sequence of commands to start the source.
    stopSeq : list of bytes or float
        Sequence of commands to stop the source.
    socketPath : str
        Path to the Unix socket.

    Attributes
    ----------
    _packetSize : int or list of tuple of int
        Size of each packet read from the Unix socket, or list of (header_byte, packet_size) tuples.
    _startSeq : list of bytes or float
        Sequence of commands to start the source.
    _stopSeq : list of bytes or float
        Sequence of commands to stop the source.
    _socketPath : str
        Path to the local socket.
    _localServer : QLocalServer
        Instance of QLocalServer.
    _clientSock : QLocalSocket or None
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
        socketPath: str,
    ) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._socketPath = socketPath

        self._unixSocketServer = QLocalServer(self)
        QLocalServer.removeServer(self._socketPath)
        self._unixSocketServer.newConnection.connect(self._handleConnection)
        self._clientSock: QLocalSocket | None = None
        self._buffer = QByteArray()
        self._guard = False

    def __str__(self):
        return f"Unix socket - {self._socketPath}"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        # Start server
        if not self._unixSocketServer.listen(self._socketPath):
            errMsg = (
                "Cannot start Unix socket server due to the following error:\n"
                f"{self._unixSocketServer.errorString()}."
            )
            self.errorOccurred.emit(errMsg)
            logger.error(errMsg)
            return

        logger.info(
            "Waiting for Unix socket connection on %s",
            self._unixSocketServer.fullServerName(),
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
                    # Make sure the full command is sent
                    while self._clientSock.bytesToWrite() > 0:
                        self._clientSock.waitForBytesWritten(100)
                elif isinstance(c, float):
                    QThread.msleep(int(c * 1000))

            # Close socket
            self._clientSock.close()
            self._clientSock.deleteLater()
            self._clientSock = None

        # Close server
        self._unixSocketServer.close()
        self._buffer = QByteArray()

        logger.info("Unix socket communication stopped.")

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
        self._clientSock = self._unixSocketServer.nextPendingConnection()
        self._clientSock.readyRead.connect(self._collectData)

        logger.info("New connection.")

        # Start command
        for c in self._startSeq:
            if isinstance(c, (bytes, bytearray)):
                self._clientSock.write(c)
                # Make sure the full command is sent
                while self._clientSock.bytesToWrite() > 0:
                    self._clientSock.waitForBytesWritten(100)
            elif isinstance(c, float):
                QThread.msleep(int(c * 1000))

        logger.info("Unix socket communication started.")

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
        if isinstance(self._packetSize, int):
            min_size = self._packetSize
        else:
            packet_sizes = []
            for header, size in self._packetSize:
                packet_sizes.append(size)
            min_size = min(packet_sizes)

        while self._buffer.size() >= min_size:
            buffer_header = int.from_bytes(self._buffer[0])
            packet_size = None
            if isinstance(self._packetSize, list):
                for header, size in self._packetSize:
                    if header == buffer_header:
                        packet_size = size
                        break
            else:
                packet_size = self._packetSize
            if self._buffer.size() >= packet_size:
                data = self._buffer.left(packet_size).data()
                self.dataPacketReady.emit(data)
                self._buffer.remove(0, packet_size)
            else:
                break
