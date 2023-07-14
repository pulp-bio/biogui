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
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from ._abc_acq_controller import AcquisitionController


class _DataWorker(QObject):
    """Worker that generates random data indefinitely, and sends it via a Qt signal.

    Attributes
    ----------
    data_ready_sig : pyqtSignal
        Signal emitted when a new packet is read.
    _ser : Serial
        Serial port.
    _packet_size : int
        Size of each packet read from the serial port.
    _trigger : int
        Trigger value to add to each packet.
    _stop_acquisition : bool
        Whether to stop the acquisition.
    """

    data_ready_sig = pyqtSignal(bytes)

    def __init__(self, n_ch: int, n_samp: int) -> None:
        super(_DataWorker, self).__init__()

        self._n_ch = n_ch
        self._n_samp = n_samp
        self._trigger = 0
        self._stop_acquisition = False

    @property
    def trigger(self) -> int:
        return self._trigger

    @trigger.setter
    def trigger(self, trigger: int) -> None:
        self._trigger = trigger

    def start_acquisition(self) -> None:
        """Generate random data indefinitely, and send it."""
        while not self._stop_acquisition:
            data = -10 * np.random.randn(self._n_samp, self._n_ch + 1) - 100
            data[:, -1] = np.repeat(self._trigger, self._n_samp)
            data = data.astype("float32")
            self.data_ready_sig.emit(data.tobytes())
            time.sleep(1e-3)
        print("Generator stopped")

    def stop_acquisition(self) -> None:
        """Stop the acquisition."""
        self._stop_acquisition = True


class DummyAcquisitionController(AcquisitionController):
    """Controller for the acquisition from the serial port using the ESB protocol.

    Parameters
    ----------
    n_ch : int
        Number of channels.
    n_samp : int, default=5
        Number of samples in each packet.

    Attributes
    ----------
    _data_worker : _DataWorker
        Worker for generating data.
    _data_thread : QThread
        QThread associated to the data worker.
    """

    def __init__(self, n_ch: int, n_samp: int = 5) -> None:
        super(DummyAcquisitionController, self).__init__()

        # Create worker and thread
        self._data_worker = _DataWorker(n_ch, n_samp)
        self._data_thread = QThread()
        self._data_worker.moveToThread(self._data_thread)

        # Create connections
        self._data_thread.started.connect(self._data_worker.start_acquisition)

    def start_acquisition(self):
        """Start the thread."""
        self._data_thread.start()

    def stop_acquisition(self) -> None:
        """Stop the acquisition."""
        self._data_worker.stop_acquisition()
        self._data_thread.quit()
        self._data_thread.wait()

    def connect_data_ready(self, fn: Callable[[np.ndarray], Any]):
        """Connect the "data ready" signal with the given function.

        Parameters
        ----------
        fn : Callable
            Function to connect to the "data ready" signal.
        """
        self._data_worker.data_ready_sig.connect(fn)

    def disconnect_data_ready(self, fn: Callable[[np.ndarray], Any]):
        """Disconnect the "data ready" signal from the given function.

        Parameters
        ----------
        fn : Callable
            Function to disconnect from the "data ready" signal.
        """
        self._data_worker.data_ready_sig.disconnect(fn)

    @pyqtSlot(int)
    def update_trigger(self, trigger: int) -> None:
        """This method is called automatically when the associated signal is received,
        and it update the trigger value.

        Parameters
        ----------
        trigger : int
            New trigger value.
        """
        self._data_worker.trigger = trigger
