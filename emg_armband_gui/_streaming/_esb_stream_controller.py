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

import numpy as np
import serial
from PySide6.QtCore import QObject, QThread, Signal, Slot
from scipy import signal

from ._abc_stream_controller import StreamingController


class _SerialWorker(QObject):
    """Worker that reads data from a serial port indefinitely.

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
    _stopReading : bool
        Whether to stop reading data.

    Class attributes
    ----------------
    dataReadySig : Signal
        Signal emitted when new data is read.
    serialErrorSig : Signal
        Signal emitted when an error with the serial transmission occurred.
    """

    dataReadySig = Signal(bytes)
    serialErrorSig = Signal()

    def __init__(self, serialPort: str, packetSize: int, baudeRate: int) -> None:
        super(_SerialWorker, self).__init__()

        # Open serial port
        self._ser = serial.Serial(serialPort, baudeRate)  # , timeout=5)
        self._packetSize = packetSize
        self._stopReading = False

    def startReading(self) -> None:
        """Read data indefinitely from the serial port, and send it."""
        logging.info("Serial communication started.")
        self._ser.write(b"=")
        while not self._stopReading:
            data = self._ser.read(self._packetSize)

            # Check number of bytes read
            if len(data) != self._packetSize:
                self.serialErrorSig.emit()
                logging.error("Serial communication failed.")
                break

            self.dataReadySig.emit(data)

        self._ser.write(b":")
        time.sleep(0.2)
        self._ser.reset_input_buffer()
        time.sleep(0.2)
        self._ser.close()
        logging.info("Serial communication stopped.")

    def stopReading(self) -> None:
        """Stop reading data from the serial port."""
        self._stopReading = True


class _PreprocessWorker(QObject):
    """Worker that preprocess the binary data it receives.

    Parameters
    ----------
    nCh : int
        Number of channels.
    sampFreq : int
        Sampling frequency.
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
    _sos : ndarray
        Filter SOS coefficients.
    _zi : list of ndarrays
        Initial state for the filter (one per channel).

    Class attributes
    ----------------
    dataReadySig : Signal
        Signal emitted when new data is available.
    dataReadyFltSig : Signal
        Signal emitted when new filtered data is available.
    """

    dataReadySig = Signal(np.ndarray)
    dataReadyFltSig = Signal(np.ndarray)

    def __init__(
        self,
        nCh: int,
        sampFreq: int,
        nSamp: int,
        gainScaleFactor: float,
        vScaleFactor: int,
    ) -> None:
        super(_PreprocessWorker, self).__init__()

        self._nCh = nCh
        self._nSamp = nSamp
        self._gainScaleFactor = gainScaleFactor
        self._vScaleFactor = vScaleFactor

        # Filtering
        self._sos = signal.butter(N=4, Wn=20, fs=sampFreq, btype="high", output="sos")
        self._zi = np.zeros((self._sos.shape[0], 2, self._nCh))

    @Slot(bytes)
    def preprocess(self, data: bytes) -> None:
        """This method is called automatically when the associated signal is received,
        it preprocesses the received packet and emits a signal with the preprocessed data.

        Parameters
        ----------
        data : bytes
            New binary data.
        """
        # Bytes to floats
        dataRef = np.zeros(shape=(self._nSamp, self._nCh), dtype="uint32")
        data = bytearray(data)
        data = [x for i, x in enumerate(data) if i not in (0, 1, 242)]
        for k in range(self._nSamp):
            for i in range(self._nCh):
                dataRef[k, i] = (
                    data[k * 48 + (3 * i)] * 256**3
                    + data[k * 48 + (3 * i) + 1] * 256**2
                    + data[k * 48 + (3 * i) + 2] * 256
                )
        dataRef = dataRef.view("int32").astype("float32")
        dataRef = dataRef / 256 * self._gainScaleFactor * self._vScaleFactor
        dataRef = dataRef.astype("float32")
        self.dataReadySig.emit(dataRef)

        # Filter
        dataRef, self._zi = signal.sosfilt(self._sos, dataRef, axis=0, zi=self._zi)
        dataRef = dataRef.astype("float32")
        self.dataReadyFltSig.emit(dataRef)


class ESBStreamingController(StreamingController):
    """Controller for the streaming from the serial port using the ESB protocol.

    Parameters
    ----------
    serialPort : str
        String representing the serial port.
    nCh : int
        Number of channels.
    sampFreq : int
        Sampling frequency.

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

    Class attributes
    ----------------
    dataReadySig : Signal
        Signal emitted when new data is available.
    dataReadyFltSig : Signal
        Signal emitted when new filtered data is available.
    serialErrorSig : Signal
        Signal emitted when an error with the serial transmission occurred.
    """

    dataReadySig = Signal(bytes)
    dataReadyFltSig = Signal(bytes)
    serialErrorSig = Signal()

    def __init__(self, serialPort: str, nCh: int, sampFreq: int) -> None:
        super(ESBStreamingController, self).__init__()

        # Create workers and threads
        self._serialWorker = _SerialWorker(
            serialPort, packetSize=243, baudeRate=4000000
        )
        self._preprocessWorker = _PreprocessWorker(
            nCh,
            sampFreq,
            nSamp=5,
            gainScaleFactor=2.38125854276502e-08,
            vScaleFactor=1000000,
        )
        self._serialThread = QThread()
        self._serialWorker.moveToThread(self._serialThread)
        self._preprocessThread = QThread()
        self._preprocessWorker.moveToThread(self._preprocessThread)

        # Create internal connections
        self._serialThread.started.connect(self._serialWorker.startReading)
        self._serialWorker.dataReadySig.connect(self._preprocessWorker.preprocess)

        # Forward relevant signals
        self._preprocessWorker.dataReadySig.connect(lambda d: self.dataReadySig.emit(d))
        self._preprocessWorker.dataReadyFltSig.connect(
            lambda d: self.dataReadyFltSig.emit(d)
        )
        self._serialWorker.serialErrorSig.connect(lambda: self.serialErrorSig.emit())

    def startStreaming(self) -> None:
        """Start streaming."""
        self._preprocessThread.start()
        self._serialThread.start()

    def stopStreaming(self) -> None:
        """Stop streaming."""
        self._serialWorker.stopReading()
        self._serialThread.quit()
        self._serialThread.wait()
        self._preprocessThread.quit()
        self._preprocessThread.wait()
