# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Classes for the serial data source.
"""

from __future__ import annotations

import logging
import time
from sys import platform

from PySide6.QtCore import QByteArray, QIODevice, QLocale, QThread
from PySide6.QtGui import QIcon, QIntValidator
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtWidgets import QWidget

from biogui.ui.ui_serial_data_source_config_widget import (
    Ui_SerialDataSourceConfigWidget,
)
from biogui.utils import detectTheme

from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)

logger = logging.getLogger(__name__)


class SerialConfigWidget(DataSourceConfigWidget, Ui_SerialDataSourceConfigWidget):
    """
    Widget to configure the serial source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Setup UI
        self.setupUi(self)
        theme = detectTheme()
        self.rescanSerialPortsButton.setIcon(
            QIcon.fromTheme("view-refresh", QIcon(f":icons/{theme}/reload"))
        )

        self._rescanSerialPorts()
        self.rescanSerialPortsButton.clicked.connect(self._rescanSerialPorts)

        baudRateValidator = QIntValidator(bottom=1, top=4_000_000)
        self.baudRateTextField.setValidator(baudRateValidator)

    def validateConfig(self) -> DataSourceConfigResult:
        """
        Validate the configuration.

        Returns
        -------
        DataSourceConfigResult
            Configuration result.
        """
        if self.serialPortsComboBox.currentText() == "":
            return DataSourceConfigResult(
                dataSourceType=DataSourceType.SERIAL,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "serial port" field is empty.',
            )

        if not self.baudRateTextField.hasAcceptableInput():
            return DataSourceConfigResult(
                dataSourceType=DataSourceType.SERIAL,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "baud rate" field is invalid.',
            )

        serialPortName = self.serialPortsComboBox.currentText()
        return DataSourceConfigResult(
            dataSourceType=DataSourceType.SERIAL,
            dataSourceConfig={
                "serialPortName": serialPortName,
                "baudRate": QLocale().toInt(self.baudRateTextField.text())[0],
            },
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
        if "serialPortName" in config:
            self.serialPortsComboBox.setCurrentText(config["serialPortName"])
        if "baudRate" in config:
            self.baudRateTextField.setText(QLocale().toString(config["baudRate"]))

    def getFieldsInTabOrder(self) -> list[QWidget]:
        """
        Get the list of fields in tab order.

        Returns
        -------
        list of QWidgets
            List of the QWidgets in tab order.
        """
        return [
            self.serialPortsComboBox,
            self.rescanSerialPortsButton,
            self.baudRateTextField,
        ]

    def _rescanSerialPorts(self) -> None:
        """Rescan the serial ports to update the combo box."""
        self.serialPortsComboBox.clear()
        self.serialPortsComboBox.addItems(
            [portInfo.portName() for portInfo in QSerialPortInfo.availablePorts()]
        )


class SerialDataSourceWorker(DataSourceWorker):
    """
    Concrete DataSourceWorker that collects data from a serial port.

    Parameters
    ----------
    packetSize : int | list[tuple[int, int]]
        List of (header_byte, packet_size) tuples for different packet types, or a single packet size.
    startSeq : list[bytes | float]
        Sequence of commands to start the source.
    stopSeq : list[bytes | float]
        Sequence of commands to stop the source.
    serialPortName : str
        String representing the serial port.
    baudRate : int
        Baud rate.

    Attributes
    ----------
    _packetSize : int | list[tuple[int, int]]
        Size of each packet read from the serial port, or list of (header_byte, packet_size) tuples.
    _startSeq : list[bytes | float]
        Sequence of commands to start the source.
    _stopSeq : list[bytes | float]
        Sequence of commands to stop the source.
    _serialPortName : str
        String representing the serial port.
    _baudRate : int
        Baud rate.
    _serialPort : QSerialPort
        Serial port object.
    _buffer : QByteArray
        Input buffer.
    _guard : bool
        Guard flag to control data emission.
    _headerByte : int or None
        Expected first byte of every packet, when packetSize is a fixed int.
        Used to detect a misaligned stream; without it a single lost byte
        silently misaligns every packet from then on and the decoder rejects
        all of them. Ignored for the (header, size) form, which resyncs on
        its own header table instead.
    _tailerByte : int or None
        Expected last byte of every packet, checked the same way -- a header
        byte can match by coincidence, so the tailer is what confirms
        alignment. Fixed-size packets only.
    _resyncDrops : int
        Bytes dropped while hunting for the next packet boundary; reset and
        logged once alignment is regained.

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
        serialPortName: str,
        baudRate: int,
        headerByte: int | None = None,
        tailerByte: int | None = None,
    ) -> None:
        super().__init__(packetSize, startSeq, stopSeq)

        self._serialPortName = serialPortName
        self._baudRate = baudRate

        # Optional framing markers, used to detect and recover from a misaligned
        # byte stream (see _collectData). Only meaningful for a fixed packetSize;
        # the (header, size) form resyncs on the header table instead. Accepted
        # here so a caller can supply them without another change to this class.
        self._headerByte = headerByte
        self._tailerByte = tailerByte
        self._resyncDrops = 0

        self._serialPort = QSerialPort(self)
        self._serialPort.setPortName(serialPortName)
        self._serialPort.setBaudRate(baudRate)
        if hasattr(self._serialPort, "setSettingsRestoredOnClose"):
            self._serialPort.setSettingsRestoredOnClose(False)
        self._buffer = QByteArray()
        self._guard = False

    def __str__(self):
        return f"Serial port - {self._serialPortName}"

    def _clearInputBuffer(self) -> None:
        """Drain stale RX bytes to start from a clean serial state."""
        self._buffer.clear()
        self._serialPort.clear(QSerialPort.Input)
        self._serialPort.readAll()

        # Also drain bytes that arrive shortly after the clear call, e.g. from
        # a device reset or late reply to the previous command.
        for _ in range(10):
            if not self._serialPort.waitForReadyRead(100):
                break
            self._serialPort.readAll()
            self._serialPort.clear(QSerialPort.Input)

    def _sendSequence(self, seq: list[bytes | float]) -> None:
        """Send a command sequence to the serial port."""
        for c in seq:
            if isinstance(c, (bytes, bytearray)):
                self._serialPort.write(c)
                # Block until Qt hands the whole command to the serial driver.
                while self._serialPort.bytesToWrite() > 0:
                    if not self._serialPort.waitForBytesWritten(100):
                        errMsg = "Timed out while writing command to the serial port."
                        self.errorOccurred.emit(errMsg)
                        logger.error(errMsg)
                        return
            elif isinstance(c, float):
                QThread.msleep(int(c * 1000))

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        # Open port
        if not self._serialPort.open(QIODevice.ReadWrite):  # type: ignore
            errMsg = f"Cannot open serial port due to the following error:\n{self._serialPort.errorString()}."
            self.errorOccurred.emit(errMsg)
            logger.error(errMsg)
            return

        # Set DTR and RTS on Windows
        if platform == "win32":
            self._serialPort.setDataTerminalReady(True)
            self._serialPort.setRequestToSend(True)

        # Reset serial-port input state before starting a new acquisition.
        self._clearInputBuffer()

        # Send start sequence, set guard flag, and connect readyRead signal
        self._sendSequence(self._startSeq)
        logging.info(f"Sent start sequence with len: {len(self._startSeq)}")
        logging.info(f"Start sequence: {self._startSeq}")
        
        self._guard = True
        self._serialPort.readyRead.connect(self._collectData)

        logger.info("Serial communication started.")

    def stopCollecting(self) -> None:
        """Stop data collection."""
        # Un-set guard flag
        self._guard = False

        # Handle double-stop, or stop-before start edge cases
        if not self._serialPort.isOpen():
            self._buffer.clear()
            return

        # Disconnect readyRead signal to stop reacting to incoming data, and send stop sequence
        try:
            self._serialPort.readyRead.disconnect(self._collectData)
        except Exception:
            pass
        self._sendSequence(self._stopSeq)
        self._serialPort.flush()
        self._clearInputBuffer()

        # Close port
        self._serialPort.close()

        logger.info("Serial communication stopped.")

    def _collectData(self) -> None:
        """Fill input buffer when data is ready."""
        # Accumulate new data
        self._buffer.append(self._serialPort.readAll())

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

            if isinstance(self._packetSize, list):
                packet_size = None
                for header, size in self._packetSize:
                    if header == buffer_header:
                        packet_size = size
                        break
                if packet_size is None:
                    # Not aligned on any known packet start. Drop one byte and
                    # look again rather than leaving packet_size unresolved --
                    # without this the stream never realigns, and comparing a
                    # size against None raises inside this slot, which kills
                    # data collection outright.
                    self._buffer.remove(0, 1)
                    self._resyncDrops += 1
                    continue
                # Each packet type has its own trailer byte, so a single
                # _tailerByte cannot describe them all; the header table is
                # what identifies boundaries here.
                expected_tailer = None
            else:
                packet_size = self._packetSize
                expected_tailer = self._tailerByte
                if self._headerByte is not None and buffer_header != self._headerByte:
                    # Fixed stride is only trustworthy while aligned; a single
                    # lost byte otherwise misaligns every packet from then on.
                    self._buffer.remove(0, 1)
                    self._resyncDrops += 1
                    continue

            if self._buffer.size() < packet_size:
                break

            if (
                expected_tailer is not None
                and int.from_bytes(self._buffer[packet_size - 1]) != expected_tailer
            ):
                # A header byte can match by coincidence; the tailer landing
                # where expected is what actually confirms alignment.
                self._buffer.remove(0, 1)
                self._resyncDrops += 1
                continue

            if self._resyncDrops:
                logger.warning(
                    "Serial resynced after dropping %d byte(s) to realign with "
                    "packet framing.",
                    self._resyncDrops,
                )
                self._resyncDrops = 0

            # Generate timestamp
            ts = time.time()

            # Emit data packet together with timestamp and trigger
            data = self._buffer.left(packet_size).data()
            self.dataPacketReady.emit(data, ts, self._trigger)
            self._buffer.remove(0, packet_size)
