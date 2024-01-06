"""Class implementing the data collection worker for serial ports.


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

from ._abc_data_worker import DataWorker


class SerialDataWorker(DataWorker):
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
    _stopReadingFlag : bool
        Flag indicating to stop reading data.
    _ser : Serial
        Object representing the serial port.

    Class attributes
    ----------------
    dataReadySig : Signal
        Qt Signal emitted when new data is collected.
    commErrorSig : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(self, packetSize: int, serialPort: str, baudRate: int) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._stopReadingFlag = False

        # Open serial port
        self._ser = serial.Serial(serialPort, baudRate, timeout=5)

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        logging.info("DataWorker: serial communication started.")

        self._ser.write(b"=")  # start code
        while not self._stopReadingFlag:
            data = self._ser.read(self._packetSize)

            # Check number of bytes read
            if len(data) != self._packetSize:
                self.commErrorSig.emit()
                logging.error("DataWorker: serial communication failed.")
                break

            self.dataReadySig.emit(data)
        self._ser.write(b":")  # stop code

        # Close port
        time.sleep(0.2)
        self._ser.reset_input_buffer()
        time.sleep(0.2)
        self._ser.close()

        logging.info("DataWorker: serial communication stopped.")

    def stopCollecting(self) -> None:
        """Stop data collection."""
        self._stopReadingFlag = True
