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
from typing import Any, Callable

import numpy as np
from PySide6.QtCore import QObject, QThread, Signal, Slot

from ._abc_stream_controller import StreamingController


class _DataWorker(QObject):
    """Worker that generates random data indefinitely, and sends it via a Qt signal.

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
    _stopAcquisition : bool
        Whether to stop the acquisition.

    Class Attributes
    ----------
    dataReadySig : Signal
        Signal emitted when a new packet is generated.
    """

    dataReadySig = Signal(np.ndarray)

    def __init__(self, nCh: int, nSamp: int) -> None:
        super(_DataWorker, self).__init__()

        self._nCh = nCh
        self._nSamp = nSamp
        self._mean = 0.0
        self._stopAcquisition = False

    def startStreaming(self) -> None:
        """Generate random data indefinitely, and send it."""
        while not self._stopAcquisition:
            data = self._mean + 100 * np.random.randn(self._nSamp, self._nCh)
            data = data.astype("float32")
            self.dataReadySig.emit(data.tobytes())
            self._mean += 20 * np.random.randn()
            time.sleep(1e-3)
        logging.info("Generator stopped")

    def stopStreaming(self) -> None:
        """Stop the generation of new data."""
        self._stopAcquisition = True


class DummyStreamingController(StreamingController):
    """Controller for the streaming of dummy data.

    Parameters
    ----------
    nCh : int
        Number of channels.
    nSamp : int, default=5
        Number of samples in each packet.

    Attributes
    ----------
    _dataWorker : _DataWorker
        Worker for generating data.
    _dataThread : QThread
        The QThread associated to the data worker.
    """

    def __init__(self, nCh: int, nSamp: int = 5) -> None:
        super(DummyStreamingController, self).__init__()

        # Create worker and thread
        self._dataWorker = _DataWorker(nCh, nSamp)
        self._dataThread = QThread()
        self._dataWorker.moveToThread(self._dataThread)

        # Create connections
        self._dataThread.started.connect(self._dataWorker.startStreaming)

    def startStreaming(self) -> None:
        """Start streaming."""
        self._dataThread.start()

    def stopStreaming(self) -> None:
        """Stop streaming."""
        self._dataWorker.stopStreaming()
        self._dataThread.quit()
        self._dataThread.wait()

    def connectDataReady(self, fn: Callable[[bytes], Any]) -> None:
        """Connect the "data ready" signal with the given function.

        Parameters
        ----------
        fn : Callable
            Function to connect to the "data ready" signal.
        """
        self._dataWorker.dataReadySig.connect(fn)

    def disconnectDataReady(self, fn: Callable[[bytes], Any]) -> None:
        """Disconnect the "data ready" signal from the given function.

        Parameters
        ----------
        fn : Callable
            Function to disconnect from the "data ready" signal.
        """
        self._dataWorker.dataReadySig.disconnect(fn)

    def connectSerialError(self, fn: Callable[[], Any]) -> None:
        """Connect the "serial error" signal with the given function.

        Parameters
        ----------
        fn : Callable
            Function to connect to the "serial error" signal.
        """
