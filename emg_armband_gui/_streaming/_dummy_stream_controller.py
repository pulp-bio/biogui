"""Class implementing a dummy streaming controller.


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
from PySide6.QtCore import QObject, QThread, Signal, Slot
from scipy import signal

from ._abc_stream_controller import StreamingController


class _DataWorker(QObject):
    """Worker that generates random data indefinitely.

    Parameters
    ----------
    nCh : int
        Number of channels.
    nSamp : int
        Number of samples.

    Attributes
    ----------
    _nCh : int
        Number of channels.
    _nSamp : int
        Number of samples.
    _mean : float
        Current mean of the generated data.
    _stopGenerating : bool
        Whether to stop generating data.

    Class Attributes
    ----------
    dataReadySig : Signal
        Signal emitted when new data is generated.
    """

    dataReadySig = Signal(np.ndarray)

    def __init__(self, nCh: int, nSamp: int) -> None:
        super(_DataWorker, self).__init__()

        self._nCh = nCh
        self._nSamp = nSamp
        self._mean = 0.0
        self._stopGenerating = False
        self._prng = np.random.default_rng(seed=42)

    def startGenerating(self) -> None:
        """Generate random data indefinitely, and send it."""
        logging.info("Generator started.")
        while not self._stopGenerating:
            data = self._prng.normal(
                loc=self._mean, scale=100, size=(self._nSamp, self._nCh)
            ).astype("float32")
            self.dataReadySig.emit(data)
            self._mean += self._prng.normal(scale=20)
            time.sleep(1e-3)
        logging.info("Generator stopped.")

    def stopGenerating(self) -> None:
        """Stop the generation of new data."""
        self._stopGenerating = True


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
    ) -> None:
        super(_PreprocessWorker, self).__init__()

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


class DummyStreamingController(StreamingController):
    """Controller for the streaming of dummy data.

    Parameters
    ----------
    nCh : int
        Number of channels.
    sampFreq : int
        Sampling frequency.

    Attributes
    ----------
    _dataWorker : _DataWorker
        Worker for generating data.
    _preprocessWorker : _PreprocessWorker
        Worker for preprocessing the data read by the serial worker.
    _dataThread : QThread
        The QThread associated to the data worker.
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

    dataReadySig = Signal(np.ndarray)
    dataReadyFltSig = Signal(np.ndarray)
    serialErrorSig = Signal()

    def __init__(self, nCh: int, sampFreq: int) -> None:
        super(DummyStreamingController, self).__init__()

        # Create workers and threads
        self._dataWorker = _DataWorker(nCh, nSamp=5)
        self._preprocessWorker = _PreprocessWorker(nCh, sampFreq, nSamp=5)
        self._dataThread = QThread()
        self._dataWorker.moveToThread(self._dataThread)
        self._preprocessThread = QThread()
        self._preprocessWorker.moveToThread(self._preprocessThread)

        # Create internal connections
        self._dataThread.started.connect(self._dataWorker.startGenerating)
        self._dataWorker.dataReadySig.connect(self._preprocessWorker.preprocess)

        # Forward relevant signals
        self._preprocessWorker.dataReadySig.connect(lambda d: self.dataReadySig.emit(d))
        self._preprocessWorker.dataReadyFltSig.connect(
            lambda d: self.dataReadyFltSig.emit(d)
        )

    def startStreaming(self) -> None:
        """Start streaming."""
        self._preprocessThread.start()
        self._dataThread.start()

    def stopStreaming(self) -> None:
        """Stop streaming."""
        self._dataWorker.stopGenerating()
        self._dataThread.quit()
        self._dataThread.wait()
        self._preprocessThread.quit()
        self._preprocessThread.wait()
