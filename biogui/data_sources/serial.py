# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Classes for the serial data source.
"""

from __future__ import annotations

import logging
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
    packetSize : int
        Size of each packet read from the serial port.
    startSeq : list of bytes or float
        Sequence of commands to start the source.
    stopSeq : list of bytes or float
        Sequence of commands to stop the source.
    serialPortName : str
        String representing the serial port.
    baudRate : int
        Baud rate.

    Attributes
    ----------
    _packetSize : int
        Size of each packet read from the serial port.
    _startSeq : list of bytes or float
        Sequence of commands to start the source.
    _stopSeq : list of bytes or float
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
        serialPortName: str,
        baudRate: int,
    ) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._serialPortName = serialPortName
        self._baudRate = baudRate

        self._serialPort = QSerialPort(self)
        self._serialPort.setPortName(serialPortName)
        self._serialPort.setBaudRate(baudRate)
        self._buffer = QByteArray()

    def __str__(self):
        return f"Serial port - {self._serialPortName}"

    def _sendSequence(self, seq: list[bytes | float]) -> None:
        """Send a command sequence to the serial port."""
        for c in seq:
            if isinstance(c, (bytes, bytearray)):
                self._serialPort.write(c)
                # Make sure the full command is sent before continuing.
                while self._serialPort.bytesToWrite() > 0:
                    self._serialPort.waitForBytesWritten(100)
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

        # Reset serial-port state before starting a new acquisition.
        self._serialPort.clear()  # type: ignore
        self._buffer.clear()

        self._sendSequence(self._startSeq)
        self._serialPort.readyRead.connect(self._collectData)

        logger.info("Serial communication started.")

    def stopCollecting(self) -> None:
        """Stop data collection."""
        if not self._serialPort.isOpen():
            self._buffer.clear()
            return

        logger.info("Serial communication stopped.")

        # Stop reacting to incoming data while shutting the device down.
        try:
            self._serialPort.readyRead.disconnect(self._collectData)
        except Exception:
            pass

        self._sendSequence(self._stopSeq)

        attempts = 0
        max_attempts = 30  # Safety break to avoid an infinite shutdown loop.
        while self._serialPort.waitForReadyRead(300):
            self._serialPort.clear()  # type: ignore
            attempts += 1
            QThread.msleep(100)

            if attempts % 3 == 0:
                logger.warning("Device still sending data, resending stop command.")
                self._sendSequence(self._stopSeq)

            if attempts >= max_attempts:
                logger.error("Device failed to stop streaming. Forcing port close.")
                break

        self._buffer.clear()
        self._serialPort.clear()  # type: ignore

        # Close port
        self._serialPort.close()

    def _collectData(self) -> None:
        """Fill input buffer when data is ready."""
        # Accumulate new data
        self._buffer.append(self._serialPort.readAll())

        # Emit all data packets in the buffer
        while self._buffer.size() >= self._packetSize:
            data = self._buffer.left(self._packetSize).data()
            self.dataPacketReady.emit(data)
            self._buffer.remove(0, self._packetSize)
