"""Class implementing the a dummy acquisition controller.


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
from PySide6.QtCore import QObject, QThread, Signal, Slot

from ._abc_acq_controller import AcquisitionController


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
    data_ready_sig : Signal
        Signal emitted when a new packet is read.
    _nCh : int
        Number of channels.
    _nSamp : int
        Number of samples.
    _trigger : int
        Trigger value to add to each packet.
    _stopAcquisition : bool
        Whether to stop the acquisition.
    """

    dataReadySig = Signal(np.ndarray)

    def __init__(self, nCh: int, nSamp: int) -> None:
        super(_DataWorker, self).__init__()

        self._nCh = nCh
        self._nSamp = nSamp
        self._trigger = 0
        self._stopAcquisition = False

    @property
    def trigger(self) -> int:
        return self._trigger

    @trigger.setter
    def trigger(self, trigger: int) -> None:
        self._trigger = trigger

    def startAcquisition(self) -> None:
        """Generate random data indefinitely, and send it."""
        while not self._stopAcquisition:
            data = -10 * np.random.randn(self._nSamp, self._nCh + 1) - 100
            data[:, -1] = np.repeat(self._trigger, self._nSamp)
            data = data.astype("float32")
            self.dataReadySig.emit(data.tobytes())
            time.sleep(1e-3)
        print("Generator stopped")

    def stopAcquisition(self) -> None:
        """Stop the acquisition."""
        self._stopAcquisition = True


class DummyAcquisitionController(AcquisitionController):
    """Controller for the acquisition from the serial port using the ESB protocol.

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
        QThread associated to the data worker.
    """

    def __init__(self, nCh: int, nSamp: int = 5) -> None:
        super(DummyAcquisitionController, self).__init__()

        # Create worker and thread
        self._dataWorker = _DataWorker(nCh, nSamp)
        self._dataThread = QThread()
        self._dataWorker.moveToThread(self._dataThread)

        # Create connections
        self._dataThread.started.connect(self._dataWorker.startAcquisition)

    def startAcquisition(self):
        """Start the thread."""
        self._dataThread.start()

    def stopAcquisition(self) -> None:
        """Stop the acquisition."""
        self._dataWorker.stopAcquisition()
        self._dataThread.quit()
        self._dataThread.wait()

    def connectDataReady(self, fn: Callable[[np.ndarray], Any]):
        """Connect the "data ready" signal with the given function.

        Parameters
        ----------
        fn : Callable
            Function to connect to the "data ready" signal.
        """
        self._dataWorker.dataReadySig.connect(fn)

    def disconnectDataReady(self, fn: Callable[[np.ndarray], Any]):
        """Disconnect the "data ready" signal from the given function.

        Parameters
        ----------
        fn : Callable
            Function to disconnect from the "data ready" signal.
        """
        self._dataWorker.dataReadySig.disconnect(fn)

    @Slot(int)
    def updateTrigger(self, trigger: int) -> None:
        """This method is called automatically when the associated signal is received,
        and it update the trigger value.

        Parameters
        ----------
        trigger : int
            New trigger value.
        """
        self._dataWorker.trigger = trigger
