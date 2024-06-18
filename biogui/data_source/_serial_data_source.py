"""Classes for the serial data source.


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

from PySide6.QtCore import QByteArray, QIODevice
from PySide6.QtGui import QIntValidator
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtWidgets import QWidget

from ..ui.ui_serial_config_widget import Ui_SerialConfigWidget
from ._abc_data_source import ConfigResult, ConfigWidget, DataSource, DataSourceType


class SerialConfigWidget(ConfigWidget, Ui_SerialConfigWidget):
    """Widget to configure the serial source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self._rescanSerialPorts()
        self.rescanSerialPortsButton.clicked.connect(self._rescanSerialPorts)

        baudRateValidator = QIntValidator(bottom=1, top=4_000_000)
        self.baudRateTextField.setValidator(baudRateValidator)

    def validateConfig(self) -> ConfigResult:
        """Validate the configuration.

        Returns
        -------
        ConfigResult
            Configuration result.
        """
        if self.serialPortsComboBox.currentText() == "":
            return ConfigResult(
                dataSourceType=DataSourceType.SERIAL,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "serial port" field is empty.',
            )

        if not self.baudRateTextField.hasAcceptableInput():
            return ConfigResult(
                dataSourceType=DataSourceType.SERIAL,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "baud rate" field is invalid.',
            )

        serialPortName = self.serialPortsComboBox.currentText()
        return ConfigResult(
            dataSourceType=DataSourceType.SERIAL,
            dataSourceConfig={
                "serialPortName": serialPortName,
                "baudRate": int(self.baudRateTextField.text()),
            },
            isValid=True,
            errMessage="",
        )

    def _rescanSerialPorts(self) -> None:
        """Rescan the serial ports to update the combo box."""
        self.serialPortsComboBox.clear()
        self.serialPortsComboBox.addItems(
            [portInfo.portName() for portInfo in QSerialPortInfo.availablePorts()]
        )


class SerialDataSource(DataSource):
    """Concrete worker that collects data from a serial port.

    Parameters
    ----------
    packetSize : int
        Size of each packet read from the serial port.
    serialPortName : str
        String representing the serial port.
    baudRate : int
        Baud rate.

    Attributes
    ----------
    _packetSize : int
        Size of each packet read from the serial port.
    _serialPort : QSerialPort
        Serial port object.
    _buffer : bytearray
        Input buffer.

    Class attributes
    ----------------
    dataReadySig : Signal
        Qt Signal emitted when new data is collected.
    errorSig : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(self, packetSize: int, serialPortName: str, baudRate: int) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._serialPort = QSerialPort(self)
        self._serialPort.setPortName(serialPortName)
        self._serialPort.setBaudRate(baudRate)
        self._serialPort.setDataBits(QSerialPort.Data8)
        self._serialPort.setParity(QSerialPort.NoParity)
        self._serialPort.setStopBits(QSerialPort.OneStop)
        self._serialPort.setFlowControl(QSerialPort.NoFlowControl)
        self._serialPort.setRequestToSend(True)
        self._serialPort.setDataTerminalReady(True)
        self._serialPort.readyRead.connect(self._collectData)
        self._buffer = QByteArray()

    def __str__(self):
        return f"Serial port - {self._serialPort.portName()}"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        # Open port
        if not self._serialPort.open(QIODevice.ReadWrite):
            self.errorSig.emit("Cannot open serial port.")
            logging.error("DataWorker: cannot open serial port.")
            return

        # Start command
        self._serialPort.write(b"=")

    def stopCollecting(self) -> None:
        """Stop data collection."""
        # Stop command
        self._serialPort.write(b":")
        self._serialPort.flush()

        # Reset input buffer and close port
        while self._serialPort.waitForReadyRead(200):
            self._serialPort.readAll()
        self._serialPort.close()
        self._buffer = QByteArray()

    def _collectData(self) -> None:
        """Fill input buffer when data is ready."""
        self._buffer.append(self._serialPort.readAll())
        if len(self._buffer) >= self._packetSize:
            data = self._buffer.mid(0, self._packetSize).data()
            self.dataReadySig.emit(data)
            self._buffer.remove(0, self._packetSize)
