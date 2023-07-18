"""Class implementing the ESB acquisition controller.


Copyright 2023 Mattia Orlandi

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

import time
from typing import Any, Callable

import numpy as np
import serial
from PySide6.QtCore import QObject, QThread, Signal, Slot

from ._abc_acq_controller import AcquisitionController


class _SerialWorker(QObject):
    """Worker that reads data from a serial port indefinitely, and sends it via a Qt signal.

    Parameters
    ----------
    serialPort : str
        String representing the serial port.
    packetSize : int
        Size of each packet read from the serial port.
    baudeRate : int
        Baude rate.

    Attributes
    ----------
    dataReadySig : Signal
        Signal emitted when a new packet is read.
    _ser : Serial
        Serial port.
    _packetSize : int
        Size of each packet read from the serial port.
    _trigger : int
        Trigger value to add to each packet.
    _stopAcquisition : bool
        Whether to stop the acquisition.
    """

    dataReadySig = Signal(bytes)

    def __init__(self, serialPort: str, packetSize: int, baudeRate: int) -> None:
        super(_SerialWorker, self).__init__()

        self._ser = serial.Serial(serialPort, baudeRate, timeout=0)
        self._packetSize = packetSize
        self._trigger = 0
        self._stopAcquisition = False

    @property
    def trigger(self) -> int:
        return self._trigger

    @trigger.setter
    def trigger(self, trigger: int) -> None:
        self._trigger = trigger

    def startAcquisition(self) -> None:
        """Read data indefinitely from the serial port, and send it."""
        self._ser.write(b"=")
        while not self._stopAcquisition:
            data = self._ser.read(self._packetSize)
            if data:
                data = bytearray(data)
                data[-1] = self._trigger
                self.dataReadySig.emit(bytes(data))
        self._ser.write(b":")
        time.sleep(0.2)
        self._ser.reset_input_buffer()
        time.sleep(0.2)
        self._ser.close()
        print("Serial stopped")

    def stopAcquisition(self) -> None:
        """Stop the acquisition."""
        self._stopAcquisition = True


class _PreprocessWorker(QObject):
    """Worker that preprocess the binary data it receives via a Qt signal.

    Parameters
    ----------
    nCh : int
        Number of channels.
    nSamp : int
        Number of samples in each packet.
    gainScaleFactor : float
        Gain scaling factor.
    vScaleFactor : int
        Voltage scale factor.

    Attributes
    ----------
    data_ready_sig : Signal
        Signal emitted when data is ready.
    _nCh : int
        Number of channels.
    _nSamp : int
        Number of samples in each packet.
    _gainScaleFactor : float
        Gain scaling factor.
    _vScaleFactor : int
        Voltage scale factor.
    """

    dataReadySig = Signal(bytes)

    def __init__(
        self,
        nCh: int,
        nSamp: int,
        gainScaleFactor: float,
        vScaleFactor: int,
    ) -> None:
        super(_PreprocessWorker, self).__init__()

        self._nCh = nCh
        self._nSamp = nSamp
        self._gainScaleFactor = gainScaleFactor
        self._vScaleFactor = vScaleFactor

    @Slot(bytes)
    def preprocess(self, data: bytes) -> None:
        """This method is called automatically when the associated signal is received,
        it preprocess the received packet and emits a signal with the preprocessed data (downsampled).

        Parameters
        ----------
        data : bytes
            New binary data.
        """
        dataRef = np.zeros(shape=(self._nSamp, self._nCh + 1), dtype="uint32")
        trigger = data[242]
        data = bytearray(data)
        data = [x for i, x in enumerate(data) if i not in (0, 1, 242)]
        for k in range(self._nSamp):
            for i in range(self._nCh):
                dataRef[k, i] = (
                    data[k * 48 + (3 * i)] * 256 * 256 * 256
                    + data[k * 48 + (3 * i) + 1] * 256 * 256
                    + data[k * 48 + (3 * i) + 2] * 256
                )
        dataRef = dataRef.view("int32").astype("float32")
        dataRef = dataRef / 256 * self._gainScaleFactor * self._vScaleFactor
        dataRef[:, self._nCh] = [trigger] * self._nSamp
        dataRef = dataRef.astype("float32")

        self.dataReadySig.emit(dataRef.tobytes())


class ESBAcquisitionController(AcquisitionController):
    """Controller for the acquisition from the serial port using the ESB protocol.

    Parameters
    ----------
    serialPort : str
        String representing the serial port.
    nCh : int
        Number of channels.
    nSamp : int, default=5
        Number of samples in each packet.
    packetSize : int, default=243
        Size of each packet read from the serial port.
    baudeRate : int, default=4000000
        Baude rate.
    gainScaleFactor : float, default=2.38125854276502e-08
        Gain scaling factor.
    vScaleFactor : int, default=1000000
        Voltage scale factor.

    Attributes
    ----------
    _serialWorker : _SerialWorker
        Worker for reading data from a serial port.
    _preprocessWorker : _PreprocessWorker
        Worker for preprocessing the data read by the serial worker.
    _serialThread : QThread
        QThread associated to the serial worker.
    _preprocessThread : QThread
        QThread associated to the preprocess worker.
    """

    def __init__(
        self,
        serialPort: str,
        nCh: int,
        nSamp: int = 5,
        packetSize: int = 243,
        baudeRate: int = 4000000,
        gainScaleFactor: float = 2.38125854276502e-08,
        vScaleFactor: int = 1000000,
    ) -> None:
        super(ESBAcquisitionController, self).__init__()

        # Create workers and threads
        self._serialWorker = _SerialWorker(serialPort, packetSize, baudeRate)
        self._preprocessWorker = _PreprocessWorker(
            nCh, nSamp, gainScaleFactor, vScaleFactor
        )
        self._serialThread = QThread()
        self._serialWorker.moveToThread(self._serialThread)
        self._preprocessThread = QThread()
        self._preprocessWorker.moveToThread(self._preprocessThread)

        # Create connections
        self._serialThread.started.connect(self._serialWorker.startAcquisition)
        self._serialWorker.dataReadySig.connect(self._preprocessWorker.preprocess)

    def startAcquisition(self):
        """Start the acquisition."""
        self._preprocessThread.start()
        self._serialThread.start()

    def stopAcquisition(self) -> None:
        """Stop the acquisition."""
        self._serialWorker.stopAcquisition()
        self._serialThread.quit()
        self._serialThread.wait()
        self._preprocessThread.quit()
        self._preprocessThread.wait()

    def connectDataReady(self, fn: Callable[[np.ndarray], Any]):
        """Connect the "data ready" signal with the given function.

        Parameters
        ----------
        fn : Callable
            Function to connect to the "data ready" signal.
        """
        self._preprocessWorker.dataReadySig.connect(fn)

    def disconnectDataReady(self, fn: Callable[[np.ndarray], Any]):
        """Disconnect the "data ready" signal from the given function.

        Parameters
        ----------
        fn : Callable
            Function to disconnect from the "data ready" signal.
        """
        self._preprocessWorker.dataReadySig.disconnect(fn)

    @Slot(int)
    def updateTrigger(self, trigger: int) -> None:
        """This method is called automatically when the associated signal is received,
        and it update the trigger value.

        Parameters
        ----------
        trigger : int
            New trigger value.
        """
        self._serialWorker.trigger = trigger
