"""Class implementing the streaming controller.


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

import numpy as np
from PySide6.QtCore import QObject, QThread, Signal, Slot
from scipy import signal

from ._data_source import DataSource, DataWorker, dataSourceMap


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

    Attributes
    ----------
    _nCh : int
        Number of channels.
    _nSamp : int
        Number of samples in each packet.
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
        self._sos = signal.butter(N=4, Wn=20, fs=sampFreq, btype="high", output="sos")
        self._zi = np.zeros((self._sos.shape[0], 2, self._nCh))

    @Slot(np.ndarray)
    def preprocess(self, data: np.ndarray) -> None:
        """This method is called automatically when the associated signal is received,
        it preprocesses the received packet and emits a signal with the preprocessed data.

        Parameters
        ----------
        data : ndarray
            New data.
        """
        self.dataReadySig.emit(data)

        # Filter
        data, self._zi = signal.sosfilt(self._sos, data, axis=0, zi=self._zi)
        data = data.astype("float32")
        self.dataReadyFltSig.emit(data)


class StreamingController(QObject):
    """Controller for the streaming from the serial port using the ESB protocol.

    Parameters
    ----------
    packetSize : int
        Number of bytes in the packet.
    nSamp : int
        Number of samples in each packet.
    parent : QObject or None, default=None
        Parent QObject.

    Attributes
    ----------
    _dataWorker : _DataWorker
        Worker for data collection.
    _preprocessWorker : _PreprocessWorker
        Worker for data pre-processing.
    _dataThread : QThread
        The QThread associated to the data worker.
    _preprocessThread : QThread
        The QThread associated to the preprocess worker.

    Class attributes
    ----------------
    dataReadySig : Signal
        Qt Signal emitted when new data is available.
    dataReadyFltSig : Signal
        Qt Signal emitted when new filtered data is available.
    commErrorSig : Signal
        Qt Signal emitted when a communication error occurs.
    """

    dataReadySig = Signal(bytes)
    dataReadyFltSig = Signal(bytes)
    commErrorSig = Signal()

    def __init__(
        self, packetSize: int, nSamp: int, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)

        self._packetSize = packetSize

        # Create data worker and thread
        self._dataWorker: DataWorker | None = None
        # self._dataThread = QThread(self)
        # self._dataWorker.moveToThread(self._dataThread)
        # self._dataThread.started.connect(self._dataWorker.startCollecting)

        # # Create preprocess worker and thread
        # self._preprocessWorker = _PreprocessWorker(19, 4000, 5)
        # self._preprocessThread = QThread(self)
        # self._preprocessWorker.moveToThread(self._preprocessThread)
        # self._dataWorker.dataReadySig.connect(self._preprocessWorker.preprocess)

        # # Forward relevant signals
        # self._preprocessWorker.dataReadySig.connect(lambda d: self.dataReadySig.emit(d))
        # self._preprocessWorker.dataReadyFltSig.connect(
        #     lambda d: self.dataReadyFltSig.emit(d)
        # )
        # self._dataWorker.commErrorSig.connect(lambda: self.commErrorSig.emit())

        # Create workers and threads
        # self._serialWorker = _SerialWorker(
        #     serialPort, packetSize=243, baudeRate=4_000_000
        # )
        # self._preprocessWorker = _PreprocessWorker(
        #     nCh,
        #     sampFreq,
        #     nSamp=5,
        #     gainScaleFactor=2.38125854276502e-08,
        #     vScaleFactor=1_000_000,
        # )
        # self._serialThread = QThread()
        # self._serialWorker.moveToThread(self._serialThread)
        # self._preprocessThread = QThread()
        # self._preprocessWorker.moveToThread(self._preprocessThread)

        # # Create internal connections
        # self._serialThread.started.connect(self._serialWorker.startReading)
        # self._serialWorker.dataReadySig.connect(self._preprocessWorker.preprocess)

        # # Forward relevant signals
        # self._preprocessWorker.dataReadySig.connect(lambda d: self.dataReadySig.emit(d))
        # self._preprocessWorker.dataReadyFltSig.connect(
        #     lambda d: self.dataReadyFltSig.emit(d)
        # )
        # self._serialWorker.serialErrorSig.connect(lambda: self.commErrorSig.emit())

    def configureDataSource(self, dataWorkerType: DataSource, **kwargs):
        """Configure the data source.

        Parameters
        ----------
        dataWorkerType : DataWorkerType
            Type of data source.
        kwargs : dict
            Keyword arguments for the data worker.
        """
        # Create data worker
        self._dataWorker = dataSourceMap[dataWorkerType](
            packetSize=self._packetSize, **kwargs
        )

    def startStreaming(self) -> None:
        """Start streaming."""
        # self._preprocessThread.start()
        # self._dataThread.start()

        logging.info("StreamingController: threads started.")

    def stopStreaming(self) -> None:
        """Stop streaming."""
        # self._dataWorker.stopCollecting()
        # self._dataThread.quit()
        # self._dataThread.wait()
        # self._preprocessThread.quit()
        # self._preprocessThread.wait()

        logging.info("StreamingController: threads stopped.")
