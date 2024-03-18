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
import time

import serial
import serial.tools.list_ports
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QWidget

from ..ui.ui_serial_config_widget import Ui_SerialConfigWidget
from ._abc_data_source import ConfigResult, ConfigWidget, DataSource, DataSourceType


def _serialPorts() -> list[str]:
    """Lists serial port names.

    Returns
    -------
    list of str
        A list of the serial ports available on the system.
    """
    return [info[0] for info in serial.tools.list_ports.comports()]


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

        serialPort = self.serialPortsComboBox.currentText()
        return ConfigResult(
            dataSourceType=DataSourceType.SERIAL,
            dataSourceConfig={
                "serialPort": serialPort,
                "baudRate": int(self.baudRateTextField.text()),
            },
            isValid=True,
            errMessage="",
        )

    def _rescanSerialPorts(self) -> None:
        """Rescan the serial ports to update the combo box."""
        self.serialPortsComboBox.clear()
        self.serialPortsComboBox.addItems(_serialPorts())


class SerialDataSource(DataSource):
    """Concrete worker that collects data from a serial port.

    Parameters
    ----------
    packetSize : int
        Size of each packet read from the serial port.
    serialPort : str
        String representing the serial port.
    baudRate : int
        Baud rate.

    Attributes
    ----------
    _packetSize : int
        Size of each packet read from the serial port.
    _serialPort : str
        String representing the serial port.
    _baudRate : int
        Baud rate.
    _stopReadingFlag : bool
        Flag indicating to stop reading data.

    Class attributes
    ----------------
    dataReadySig : Signal
        Qt Signal emitted when new data is collected.
    errorSig : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(self, packetSize: int, serialPort: str, baudRate: int) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._serialPort = serialPort
        self._baudRate = baudRate
        self._stopReadingFlag = False

    def __str__(self):
        return f"Serial port - {self._serialPort}"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        self._stopReadingFlag = False

        # Open serial port
        ser = serial.Serial(self._serialPort, self._baudRate, timeout=5)

        logging.info("DataWorker: serial communication started.")

        while not self._stopReadingFlag:
            data = ser.read(self._packetSize)

            # Check number of bytes read
            if len(data) != self._packetSize:
                self.errorSig.emit("Serial communication failed.")
                logging.error("DataWorker: serial communication failed.")
                break

            self.dataReadySig.emit(data)

        # Close port
        time.sleep(0.2)
        ser.reset_input_buffer()
        time.sleep(0.2)
        ser.close()

        logging.info("DataWorker: serial communication stopped.")

    def stopCollecting(self) -> None:
        """Stop data collection."""
        self._stopReadingFlag = True
