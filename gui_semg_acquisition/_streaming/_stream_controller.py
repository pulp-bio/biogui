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
import struct
import time

import numpy as np
import serial
from PySide6.QtCore import QObject, QThread, Signal, Slot
from scipy import signal


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
        Qt signal emitted when new data is read.
    serialErrorSig : Signal
        Qt signal emitted when an error with the serial transmission occurred.
    """

    dataReadySig = Signal(bytes)
    serialErrorSig = Signal()

    def __init__(self, serialPort: str, packetSize: int, baudeRate: int) -> None:
        super().__init__()

        # Open serial port
        self._ser = serial.Serial(serialPort, baudeRate, timeout=5)
        self._packetSize = packetSize
        self._stopReading = False

    def startReading(self) -> None:
        """Read data indefinitely from the serial port, and send it."""
        logging.info("Worker: serial communication started.")

        ampere = [20] * 16
        fattoreV0 = 7.26
        fattoreV1 = 2
        resistenza = 33

        buff = bytearray(10)

        # Set fs = 1kHz
        buff[0] = ord("C")
        buff[1] = ord("M")
        buff[2] = ord("D")
        buff[3] = ord("8")
        self._ser.write(buff)

        # Set DAC
        buff[0] = ord("C")
        buff[1] = ord("M")
        buff[2] = ord("D")
        buff[3] = ord("D")
        buff[4] = ord("1")
        for i in range(16):
            buff[5] = i

            if i % 4 == 0:
                tensioneDAC = fattoreV0 * resistenza * ampere[i] / 1000
            else:
                tensioneDAC = fattoreV1 * resistenza * ampere[i] / 1000

            if i < 8:
                tensioneDACfin = int(tensioneDAC * 4096 / 5)
            else:
                tensioneDACfin = int(tensioneDAC * 4096 / 5)

            buff[6] = tensioneDACfin // 256
            buff[7] = tensioneDACfin % 256

            self._ser.write(buff)
            time.sleep(0.025)

        # Start
        buff = bytearray(10)
        buff[0] = ord("C")
        buff[1] = ord("M")
        buff[2] = ord("D")
        buff[3] = ord("1")
        self._ser.write(buff)

        # Read loop
        while not self._stopReading:
            data = self._ser.read(self._packetSize)

            # Check number of bytes read
            if len(data) != self._packetSize:
                self.serialErrorSig.emit()
                logging.error("Worker: serial communication failed.")
                break

            self.dataReadySig.emit(data)

        # Stop
        buff[0] = ord("C")
        buff[1] = ord("M")
        buff[2] = ord("D")
        buff[3] = ord("2")
        self._ser.write(buff)

        # DAC
        # buff[0] = ord("C")
        # buff[1] = ord("M")
        # buff[2] = ord("D")
        # buff[3] = ord("D")
        # buff[4] = ord("0")
        # self._ser.write(buff)
        
        time.sleep(0.2)
        self._ser.reset_input_buffer()
        time.sleep(0.2)
        self._ser.close()

        logging.info("Worker: serial communication stopped.")

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
        Qt signal emitted when new data is available.
    dataReadyFltSig : Signal
        Qt signal emitted when new filtered data is available.
    """

    dataReadySig = Signal(np.ndarray)
    dataReadyFltSig = Signal(np.ndarray)

    def __init__(
        self,
        nCh: int,
        sampFreq: int,
        nSamp: int,
    ) -> None:
        super().__init__()

        self._nCh = nCh
        self._nSamp = nSamp

        # Filtering
        self._sos_PPG = signal.butter(N=6, Wn=(0.5, 10), fs=sampFreq, btype="bandpass", output="sos")
        self._zi_PPG = np.zeros((self._sos_PPG.shape[0], 2, 2))
        self._sos_EDA = signal.butter(N=6, Wn=10, fs=sampFreq, btype="lowpass", output="sos")
        self._zi_EDA = np.zeros((self._sos_EDA.shape[0], 2, 2))
        self._sos_FORCE = signal.butter(N=6, Wn=10, fs=sampFreq, btype="lowpass", output="sos")
        self._zi_FORCE = np.zeros((self._sos_FORCE.shape[0], 2, 2))
        self._sos_ACC = signal.butter(N=6, Wn=10, fs=sampFreq, btype="lowpass", output="sos")
        self._zi_ACC = np.zeros((self._sos_ACC.shape[0], 2, 3))
        #self._zi_ACC_S = np.zeros((self._sos_ACC.shape[0],))

    @Slot(bytes)
    def preprocess(self, data: bytes) -> None:
        """This method is called automatically when the associated signal is received,
        it preprocesses the received packet and emits a signal with the preprocessed data.

        Parameters
        ----------
        data : bytes
            New binary data.
        """
        # # ADC parameters
        # vRefADC = 5.0
        # gainADC = 1.0

        # dataTmp = bytearray(data)
        # # Convert 24-bit to 32-bit integer
        # pos = 0
        # for _ in range(len(dataTmp) // 3):
        #     preFix = 255 if dataTmp[pos] > 127 else 0
        #     dataTmp.insert(pos, preFix)
        #     pos += 4
        # dataRef = np.asarray(struct.unpack(f">{self._nSamp * self._nCh}i", dataTmp), dtype=np.int32)

        # # Reshape and convert ADC readings to V
        # dataRef = dataRef.reshape(self._nSamp, self._nCh)
        # dataRef = dataRef * (vRefADC / gainADC / 2**24)  # V
        # dataRef = dataRef.astype("float32")
        # self.dataReadySig.emit(dataRef)

        dataRef = np.asarray(struct.unpack(f"<{15 * 256}i", data[:-4]), dtype="int32").reshape(-1, 15)
        #conversion
        dataRef = dataRef * 4.5/2**23
        self.dataReadySig.emit(dataRef)
        
        # Filter
        dataFlt = np.zeros(shape=(256, 9), dtype="float32")
        dataFlt[:, 0] = dataRef[:, 1]
        dataFlt[:, 1] = dataRef[:, 2]
        dataFlt[:, 2] = dataRef[:, 3]
        dataFlt[:, 3] = dataRef[:, 4]
        dataFlt[:, 4] = dataRef[:, 5]
        dataFlt[:, 5] = dataRef[:, 6]
        dataFlt[:, 0:2], self._zi_PPG = signal.sosfilt(self._sos_PPG, dataRef[:, 1:3], axis=0, zi=self._zi_PPG)
        dataFlt[:, 4:6], self._zi_FORCE = signal.sosfilt(self._sos_FORCE, dataRef[:, 3:5], axis=0, zi=self._zi_FORCE)
        dataFlt[:, 2:4], self._zi_EDA = signal.sosfilt(self._sos_EDA, dataRef[:, 5:7], axis=0, zi=self._zi_EDA)
        dataFlt[:, 6:9], self._zi_ACC = signal.sosfilt(self._sos_ACC, dataRef[:,[9,11,12]], axis=0, zi=self._zi_ACC)
        #dataFlt[:,6] = dataRef[:,9]
        #dataFlt[:, 7:9], self._zi_ACC = signal.sosfilt(self._sos_ACC, dataRef[:, 11:13], axis=0, zi=self._zi_ACC)
        #dataFlt[:, 7] =  dataRef[:, 11]
        #dataFlt[:, 8] =  dataRef[:, 12]

        dataFlt[:, 0] = - dataFlt[:, 0]
        dataFlt[:, 2] = - dataFlt[:, 3] + dataFlt[:, 2]*10
        #dataFlt[:, 3] = dataFlt[:, 3]
        #dataFlt[:, 5] = - dataFlt[:, 5]
        #dataFlt[:,6] = dataFlt[:,6]

        dataFlt = dataFlt.astype("float32")
        self.dataReadyFltSig.emit(dataFlt)


class StreamingController(QObject):
    """Controller for the streaming from the serial port using the ESB protocol.

    Parameters
    ----------
    serialPort : str
        String representing the serial port.
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
        Qt signal emitted when new data is available.
    dataReadyFltSig : Signal
        Qt signal emitted when new filtered data is available.
    serialErrorSig : Signal
        Qt signal emitted when an error with the serial transmission occurred.
    """

    dataReadySig = Signal(bytes)
    dataReadyFltSig = Signal(bytes)
    serialErrorSig = Signal()

    def __init__(self, serialPort: str, sampFreq: int) -> None:
        super().__init__()

        # Create workers and threads
        self._serialWorker = _SerialWorker(
            serialPort,
            packetSize=15_364,  # 3_844,
            baudeRate=115_200,
        )
        self._preprocessWorker = _PreprocessWorker(
            nCh=15,
            sampFreq=sampFreq,
            nSamp=256,
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

        logging.info("StreamingController: threads started.")

    def stopStreaming(self) -> None:
        """Stop streaming."""
        self._serialWorker.stopReading()
        self._serialThread.quit()
        self._serialThread.wait()
        self._preprocessThread.quit()
        self._preprocessThread.wait()

        logging.info("StreamingController: threads stopped.")
