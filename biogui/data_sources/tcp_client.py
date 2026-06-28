"""
Classes for the TCP client data source.
"""
from __future__ import annotations

import logging
import time
import socket as pysock
from typing import Optional

from PySide6.QtCore import QByteArray, QLocale, QThread, QMetaObject, QTimer, Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtNetwork import QAbstractSocket, QTcpSocket
from PySide6.QtWidgets import QWidget

from biogui.ui.ui_tcp_data_source_config_widget import Ui_TCPDataSourceConfigWidget

from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)

logger = logging.getLogger(__name__)


class TCPClientConfigWidget(DataSourceConfigWidget, Ui_TCPDataSourceConfigWidget):
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
        # Default host for TCP client
        try:
            self.hostTextField.setText("192.168.4.1")
        except Exception:
            pass

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
        host = self.hostTextField.text().strip()
        if host == "":
            return DataSourceConfigResult(
                dataSourceType=DataSourceType.TCPCLIENT,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "host" field is empty.',
            )
        if not self.socketPortTextField.hasAcceptableInput():
            return DataSourceConfigResult(
                dataSourceType=DataSourceType.TCPCLIENT,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "port" field is invalid.',
            )
        port = lo.toInt(self.socketPortTextField.text())[0]

        return DataSourceConfigResult(
            dataSourceType=DataSourceType.TCPCLIENT,
            dataSourceConfig={"host": host, "port": port},
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
        if "host" in config:
            self.hostTextField.setText(config["host"])
        if "port" in config:
            self.socketPortTextField.setText(QLocale().toString(config["port"]))

    def getFieldsInTabOrder(self) -> list[QWidget]:
        """
        Get the list of fields in tab order.

        Returns
        -------
        list of QWidgets
            List of the QWidgets in tab order.
        """
        return [self.hostTextField, self.socketPortTextField]
    

class TCPClientDataSourceWorker(DataSourceWorker):
    """
    Concrete DataSourceWorker for TCP Client connections.

    Parameters
    ----------
    packetSize : int or list of tuple of int
        List of (header_byte, packet_size) tuples for different packet types,
        or a single packet size.
    startSeq : list of bytes or float
        Sequence of commands to start the source.
    stopSeq : list of bytes or float
        Sequence of commands to stop the source.
    host : str
        TCP host name or IP address.
    port : int
        TCP port.
    waitStartToken : bytes or None, default=None
        Optional token to wait for before starting packet parsing.
    """

    def __init__(
        self,
        packetSize: int | list[tuple[int, int]],
        startSeq: list[bytes | float],
        stopSeq: list[bytes | float],
        host: str,
        port: int,
        waitStartToken: Optional[bytes] = None,
    ) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._host = host
        self._port = int(port)
        self._start_tok = waitStartToken

        self._sock = QTcpSocket(self)
        self._sock.connected.connect(self._on_connected)
        self._sock.disconnected.connect(self._on_disconnected)
        self._sock.readyRead.connect(self._on_ready_read)
        self._sock.errorOccurred.connect(self._on_error)

        self._buf = QByteArray()
        self._waiting_token = bool(self._start_tok)
        self._manual_close = False
        self._backoff_s = 0.5
        self._retry = QTimer(self, singleShot=True)
        self._retry.timeout.connect(self._connect)

        self._guard = False

    def __str__(self) -> str:
        return f"TCP client - {self._host}:{self._port}"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        self._manual_close = False
        self._guard = False
        self._buf.clear()
        self._waiting_token = bool(self._start_tok)
        self._backoff_s = 0.5
        QMetaObject.invokeMethod(self, "_connect", Qt.QueuedConnection)

    def stopCollecting(self) -> None:
        """Stop collecting data from the configured source."""
        self._guard = False
        self._manual_close = True
        self._retry.stop()

        if self._sock.state() == QAbstractSocket.ConnectedState:
            for c in self._stopSeq:
                if isinstance(c, (bytes, bytearray)):
                    self._sock.write(c)
                    self._sock.flush()
                elif isinstance(c, float):
                    QThread.msleep(int(c * 1000))

        self._sock.abort()
        self._buf.clear()

    def _connect(self) -> None:
        if self._manual_close:
            return

        self._sock.abort()
        self._sock.setSocketOption(QAbstractSocket.LowDelayOption, 1)
        self._sock.setSocketOption(QAbstractSocket.KeepAliveOption, 1)
        self._sock.connectToHost(self._host, self._port)

    def _on_connected(self) -> None:
        self._keepalive_best_effort()
        self._backoff_s = 0.5

        logger.info("TCP client connected to %s:%d", self._host, self._port)

        time.sleep(0.1)

        for c in self._startSeq:
            if isinstance(c, (bytes, bytearray)):
                self._sock.write(c)
                self._sock.flush()
            elif isinstance(c, int):
                self._sock.write(bytes([c]))
                self._sock.flush()
            elif isinstance(c, float):
                QThread.msleep(int(c * 1000))

        self._guard = True

    def _on_disconnected(self) -> None:
        logger.info("TCP client disconnected")
        if self._manual_close:
            return

        self._guard = False
        self._backoff_s = min(self._backoff_s * 2.0, 5.0)
        self._retry.start(int(self._backoff_s * 1000))

    def _on_error(self) -> None:
        errMsg = self._sock.errorString()
        self.errorOccurred.emit(errMsg)
        logger.error(errMsg)

        if self._sock.state() != QAbstractSocket.ConnectedState and not self._manual_close:
            self._backoff_s = min(self._backoff_s * 2.0, 5.0)
            self._retry.start(int(self._backoff_s * 1000))

    def _on_ready_read(self) -> None:
        chunk = self._sock.readAll()
        if chunk.isEmpty():
            return

        self._buf.append(chunk)

        if self._waiting_token and self._start_tok:
            idx = self._buf.indexOf(self._start_tok)
            if idx == -1:
                return
            self._buf.remove(0, idx + len(self._start_tok))
            logger.info("TCP client received start token")
            self._waiting_token = False

        self._process_variable_frames()

    def _process_variable_frames(self) -> None:
        """
        Parse variable-sized packets from the input buffer.

        The first byte is treated as the packet header. The remaining packet size
        is resolved from ``self._packetSize`` and the matching packet is emitted
        once the full payload is available.
        """

        while True:
            if self._buf.size() < 1:
                return

            if isinstance(self._packetSize, int):
                min_size = self._packetSize
            else:
                packet_sizes = [size for _, size in self._packetSize]
                if not packet_sizes:
                    return
                min_size = min(packet_sizes)

            if self._buf.size() < min_size:
                return

            buffer_header = int.from_bytes(self._buf[0])

            if isinstance(self._packetSize, list):
                packet_size = None
                for header, size in self._packetSize:
                    if header == buffer_header:
                        packet_size = size
                        break
                if packet_size is None:
                    self._buf.remove(0, 1)
                    continue
            else:
                packet_size = self._packetSize

            if self._buf.size() < packet_size:
                return

            data = self._buf.left(packet_size).data()
            self.dataPacketReady.emit(data)
            self._buf.remove(0, packet_size)

    def _keepalive_best_effort(self) -> None:
        fd = self._sock.socketDescriptor()
        if fd == -1:
            return

        dup = None
        try:
            dup = pysock.fromfd(fd, pysock.AF_INET, pysock.SOCK_STREAM)
            try:
                dup.setsockopt(pysock.IPPROTO_TCP, 0x10, 30)
                dup.setsockopt(pysock.IPPROTO_TCP, 0x12, 10)
                dup.setsockopt(pysock.IPPROTO_TCP, 0x13, 3)
            except OSError:
                pass
        except OSError:
            pass
        finally:
            if dup is not None:
                try:
                    dup.close()
                except Exception:
                    pass