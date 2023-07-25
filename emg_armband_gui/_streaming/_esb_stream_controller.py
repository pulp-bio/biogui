"""Class implementing the ESB streaming controller.


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
from typing import Any, Callable

import numpy as np
import serial
from PySide6.QtCore import QObject, QThread, Signal, Slot

from ._abc_stream_controller import StreamingController


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
    _ser : Serial
        The serial port.
    _packetSize : int
        Size of each packet read from the serial port.
    _trigger : int
        Trigger value to add to each packet.
    _stopAcquisition : bool
        Whether to stop the acquisition.

    Class Attributes
    ----------
    dataReadySig : Signal
        Signal emitted when a new packet is generated.
    """

    dataReadySig = Signal(bytes)
    serialErrorSig = Signal()

    def __init__(self, serialPort: str, packetSize: int, baudeRate: int) -> None:
        super(_SerialWorker, self).__init__()

        # Open serial port
        self._ser = serial.Serial(serialPort, baudeRate, timeout=5)
        self._packetSize = packetSize
        self._trigger = 0
        self._stopAcquisition = False

    @property
    def trigger(self) -> int:
        return self._trigger

    @trigger.setter
    def trigger(self, trigger: int) -> None:
        self._trigger = trigger

    def startStreaming(self) -> None:
        """Read data indefinitely from the serial port, and send it."""
        self._ser.write(b"=")
        while not self._stopAcquisition:
            data = self._ser.read(self._packetSize)

            # Check number of bytes read
            if len(data) != self._packetSize:
                self._closePort()
                self.serialErrorSig.emit()
                break

            data = bytearray(data)
            data[-1] = self._trigger
            self.dataReadySig.emit(bytes(data))
        self._ser.write(b":")
        self._closePort()
        logging.info("Serial stopped")

    def stopStreaming(self) -> None:
        """Stop reading data from the serial port."""
        self._stopAcquisition = True

    def _closePort(self) -> None:
        time.sleep(0.2)
        self._ser.reset_input_buffer()
        time.sleep(0.2)
        self._ser.close()


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
    _nCh : int
        Number of channels.
    _nSamp : int
        Number of samples in each packet.
    _gainScaleFactor : float
        Gain scaling factor.
    _vScaleFactor : int
        Voltage scale factor.

    Class Attributes
    ----------
    dataReadySig : Signal
        Signal emitted when a new packet is generated.
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
        it preprocesses the received packet and emits a signal with the preprocessed data.

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


class ESBStreamingController(StreamingController):
    """Controller for the streaming from the serial port using the ESB protocol.

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
        The QThread associated to the serial worker.
    _preprocessThread : QThread
        The QThread associated to the preprocess worker.
    """

    def __init__(self, serialPort: str, nCh: int) -> None:
        super(ESBStreamingController, self).__init__()

        # Create workers and threads
        self._serialWorker = _SerialWorker(
            serialPort, packetSize=243, baudeRate=4000000
        )
        self._preprocessWorker = _PreprocessWorker(
            nCh, nSamp=5, gainScaleFactor=2.38125854276502e-08, vScaleFactor=1000000
        )
        self._serialThread = QThread()
        self._serialWorker.moveToThread(self._serialThread)
        self._preprocessThread = QThread()
        self._preprocessWorker.moveToThread(self._preprocessThread)

        # Create connections
        self._serialThread.started.connect(self._serialWorker.startStreaming)
        self._serialWorker.dataReadySig.connect(self._preprocessWorker.preprocess)

    def startStreaming(self) -> None:
        """Start streaming."""
        self._preprocessThread.start()
        self._serialThread.start()

    def stopStreaming(self) -> None:
        """Stop streaming."""
        self._serialWorker.stopStreaming()
        self._serialThread.quit()
        self._serialThread.wait()
        self._preprocessThread.quit()
        self._preprocessThread.wait()

    def connectDataReady(self, fn: Callable[[bytes], Any]):
        """Connect the "data ready" signal with the given function.

        Parameters
        ----------
        fn : Callable
            Function to connect to the "data ready" signal.
        """
        self._preprocessWorker.dataReadySig.connect(fn)

    def disconnectDataReady(self, fn: Callable[[bytes], Any]):
        """Disconnect the "data ready" signal from the given function.

        Parameters
        ----------
        fn : Callable
            Function to disconnect from the "data ready" signal.
        """
        self._preprocessWorker.dataReadySig.disconnect(fn)

    def connectSerialError(self, fn: Callable[[], Any]):
        """Connect the "serial error" signal with the given function.

        Parameters
        ----------
        fn : Callable
            Function to connect to the "serial error" signal.
        """
        self._serialWorker.serialErrorSig.connect(fn)

    @Slot(int)
    def updateTrigger(self, trigger: int) -> None:
        """This method is called automatically when the associated signal is received,
        and it updates the trigger value.

        Parameters
        ----------
        trigger : int
            New trigger value.
        """
        self._serialWorker.trigger = trigger
