# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Classes for the TCP client data source.
"""

from __future__ import annotations

import logging
import socket as pysock
import time
from typing import Optional

from PySide6.QtCore import QByteArray, QLocale, QMetaObject, Qt, QThread, QTimer
from PySide6.QtGui import QIntValidator
from PySide6.QtNetwork import QAbstractSocket, QTcpSocket
from PySide6.QtWidgets import QWidget

from biogui.ui.ui_tcpclient_data_source_config_widget import (
    Ui_TCPClientDataSourceConfigWidget,
)

from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)

logger = logging.getLogger(__name__)


class TCPClientConfigWidget(DataSourceConfigWidget, Ui_TCPClientDataSourceConfigWidget):
    """
    Widget to configure the TCP client source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        # Default host for TCP client (typical ESP32 SoftAP gateway address)
        self.hostTextField.setText("192.168.4.1")

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
    Concrete DataSourceWorker that connects out to a TCP server as a client
    (e.g. an ESP32 shield running in SoftAP mode, where the GUI dials in
    instead of listening - the reverse topology of TCPDataSourceWorker).

    Parameters
    ----------
    packetSize : int or list of tuple of int
        List of (header_byte, packet_size) tuples for different packet types, or a single packet size.
    startSeq : list of bytes or float
        Sequence of commands to start the source.
    stopSeq : list of bytes or float
        Sequence of commands to stop the source.
    host : str
        TCP host name or IP address.
    port : int
        TCP port.
    waitStartToken : bytes or None, default=None
        Optional token to wait for in the incoming stream before parsing packets.
    headerByte : int or None, default=None
        Expected value of each packet's first byte. If provided, a packet whose
        first byte doesn't match is treated as a misalignment: one byte is
        dropped and parsing retries from there instead of accepting a corrupt
        frame. Only meaningful when packetSize is a plain int (the list form
        already validates the header while looking up the packet size).
    tailerByte : int or None, default=None
        Expected value of each packet's last byte. If provided, checked the
        same way as headerByte -- this is what actually detects and recovers
        from a stream that has drifted out of alignment with real packet
        boundaries, which a header check alone cannot catch on its own if a
        data byte happens to collide with the header value.

    Attributes
    ----------
    _host : str
        TCP host name or IP address.
    _port : int
        TCP port.
    _sock : QTcpSocket
        Client socket.
    _buf : QByteArray
        Input buffer.
    _guard : bool
        Guard flag to control data emission.

    Class attributes
    ----------------
    dataPacketReady : Signal
        Qt Signal emitted when new data is collected; it's a tuple of data (ndarray), timestamp (float),
        and optional trigger (tuple with integer id and string label, or None).
    errorOccurred : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(
        self,
        packetSize: int | list[tuple[int, int]],
        startSeq: list[bytes | float],
        stopSeq: list[bytes | float],
        host: str,
        port: int,
        waitStartToken: Optional[bytes] = None,
        headerByte: Optional[int] = None,
        tailerByte: Optional[int] = None,
    ) -> None:
        super().__init__(packetSize, startSeq, stopSeq)

        self._host = host
        self._port = int(port)
        self._start_tok = waitStartToken
        self._header_byte = headerByte
        self._tailer_byte = tailerByte

        # None-safe: formatting None with :#04x raises TypeError, which Qt
        # can silently swallow when raised inside __init__/a slot -- that
        # would explain both of these never printing anything at all rather
        # than printing "None".
        header_str = f"{self._header_byte:#04x}" if self._header_byte is not None else "None"
        tailer_str = f"{self._tailer_byte:#04x}" if self._tailer_byte is not None else "None"
        logging.info(f"[TCPClient] Using header byte: {header_str}, tailer byte: {tailer_str}")
        print(f"[TCPClient] Using header byte: {header_str}, tailer byte: {tailer_str}")
        self._resync_drops = 0

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
        self._resync_drops = 0
        self._waiting_token = bool(self._start_tok)
        self._backoff_s = 0.5
        QMetaObject.invokeMethod(self, "_connect", Qt.QueuedConnection)

    def stopCollecting(self) -> None:
        """Stop data collection."""
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

        logger.info("TCP client communication stopped.")

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

        # Discard anything already sitting in the socket (e.g. a late reply
        # to the previous session's stop sequence, arriving right as we
        # reconnect for a new one), then give a short window for further
        # stragglers to arrive before actually starting -- mirrors
        # SerialDataSourceWorker's _clearInputBuffer(), which exists for the
        # same reason.
        self._buf.clear()
        self._sock.readAll()
        QTimer.singleShot(150, self._start_after_flush)

    def _start_after_flush(self) -> None:
        # Discard anything that arrived during the flush window above, then
        # actually start the session from a guaranteed-clean buffer.
        self._buf.clear()
        self._sock.readAll()

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

        if not self._guard:
            return

        self._process_variable_frames()

    def _process_variable_frames(self) -> None:
        """
        Parse variable-sized packets from the input buffer.

        The first byte is treated as the packet header. The remaining packet size
        is resolved from ``self._packetSize`` and the matching packet is emitted
        once the full payload is available.
        """
        while True:
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
                    self._resync_drops += 1
                    continue
            else:
                packet_size = self._packetSize
                if self._header_byte is not None and buffer_header != self._header_byte:
                    # Not aligned on a real packet start -- drop one byte and
                    # look again rather than blindly trusting a fixed stride.
                    logger.error(f"[TCPClient] Misaligned stream: expected header {self._header_byte:#04x}, got {buffer_header:#04x}. Dropping one byte and retrying.")
                    self._buf.remove(0, 1)
                    self._resync_drops += 1
                    continue

            if self._buf.size() < packet_size:
                logger.info(f"[TCPClient] Waiting for more data: have {self._buf.size()} bytes, need {packet_size} bytes.")
                return

            if self._tailer_byte is not None:
                tail = int.from_bytes(self._buf[packet_size - 1])
                if tail != self._tailer_byte:
                    logger.error(f"[TCPClient] Misaligned stream: expected tailer {self._tailer_byte:#04x}, got {tail:#04x}. Dropping one byte and retrying.")
                    # Header matched (or wasn't checked) but the tailer
                    # didn't land where expected -- this is what actually
                    # catches a misaligned stream, since a coincidental
                    # header-byte match alone can't be ruled out otherwise.
                    # Resync by dropping one byte instead of emitting a
                    # corrupt/misaligned packet.

                    self._buf.remove(0, 1)
                    self._resync_drops += 1
                    continue

            if self._resync_drops:
                logger.error(
                    "TCP client resynced after dropping %d byte(s) to realign with packet framing",
                    self._resync_drops,
                )
                self._resync_drops = 0

            # Generate timestamp
            ts = time.time()

            # Emit data packet together with timestamp and trigger
            data = self._buf.left(packet_size).data()
            self.dataPacketReady.emit(data, ts, self._trigger)
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
