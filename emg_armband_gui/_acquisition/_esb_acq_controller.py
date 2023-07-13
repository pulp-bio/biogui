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
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from ._abc_acq_controller import AcquisitionController


class _SerialWorker(QObject):
    """Worker that reads data from a serial port indefinitely, and sends it via a Qt signal.

    Parameters
    ----------
    serial_port : str
        String representing the serial port.
    packet_size : int
        Size of each packet read from the serial port.
    baude_rate : int
        Baude rate.

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

    data_ready_sig = pyqtSignal(bytearray)

    def __init__(self, serial_port: str, packet_size: int, baude_rate: int) -> None:
        super(_SerialWorker, self).__init__()

        self._ser = serial.Serial(serial_port, baude_rate, timeout=0)
        self._packet_size = packet_size
        self._trigger = 0
        self._stop_acquisition = False

    @property
    def trigger(self) -> int:
        return self._trigger

    @trigger.setter
    def trigger(self, trigger: int) -> None:
        self._trigger = trigger

    def start_acquisition(self) -> None:
        """Read data indefinitely from the serial port, and send it."""
        self._ser.write(b"=")
        while not self._stop_acquisition:
            data = self._ser.read(self._packet_size)
            if data:
                data = bytearray(data)
                data[-1] = self._trigger
                self.data_ready_sig.emit(data)
        self._ser.write(b":")
        time.sleep(0.2)
        self._ser.reset_input_buffer()
        time.sleep(0.2)
        self._ser.close()
        print("Serial stopped")

    def stop_acquisition(self) -> None:
        """Stop the acquisition."""
        self._stop_acquisition = True


class _PreprocessWorker(QObject):
    """Worker that preprocess the binary data it receives via a Qt signal.

    Parameters
    ----------
    n_ch : int
        Number of channels.
    n_samp : int
        Number of samples in each packet.
    gain_scale_factor : float
        Gain scaling factor.
    v_scale_factor : int
        Voltage scale factor.

    Attributes
    ----------
    data_ready_sig : pyqtSignal
        Signal emitted when data is ready.
    _n_ch : int
        Number of channels.
    _n_samp : int
        Number of samples in each packet.
    _gain_scale_factor : float
        Gain scaling factor.
    _v_scale_factor : int
        Voltage scale factor.
    """

    data_ready_sig = pyqtSignal(np.ndarray)

    def __init__(
        self,
        n_ch: int,
        n_samp: int,
        gain_scale_factor: float,
        v_scale_factor: int,
    ) -> None:
        super(_PreprocessWorker, self).__init__()

        self._n_ch = n_ch
        self._n_samp = n_samp
        self._gain_scale_factor = gain_scale_factor
        self._v_scale_factor = v_scale_factor

    @pyqtSlot(bytearray)
    def preprocess(self, data: bytearray) -> None:
        """This method is called automatically when the associated signal is received,
        it preprocess the received packet and emits a signal with the preprocessed data (downsampled).

        Parameters
        ----------
        data : bytearray
            New binary data.
        """
        data_ref = np.zeros(shape=(self._n_samp, self._n_ch + 1), dtype="uint32")
        data_ref[:, self._n_ch] = [data[242]] * self._n_samp
        data = [x for i, x in enumerate(data) if i not in (0, 1, 242)]
        for k in range(self._n_samp):
            for i in range(self._n_ch):
                data_ref[k, i] = (
                    data[k * 48 + (3 * i)] * 256 * 256 * 256
                    + data[k * 48 + (3 * i) + 1] * 256 * 256
                    + data[k * 48 + (3 * i) + 2] * 256
                )
        data_ref = data_ref.view("int32").astype("float32")
        data_ref = data_ref / 256 * self._gain_scale_factor * self._v_scale_factor

        self.data_ready_sig.emit(data_ref)


class ESBAcquisitionController(AcquisitionController):
    """Controller for the acquisition from the serial port using the ESB protocol.

    Parameters
    ----------
    serial_port : str
        String representing the serial port.
    n_ch : int
        Number of channels.
    n_samp : int, default=5
        Number of samples in each packet.
    packet_size : int, default=243
        Size of each packet read from the serial port.
    baude_rate : int, default=4000000
        Baude rate.
    gain_scale_factor : float, default=2.38125854276502e-08
        Gain scaling factor.
    v_scale_factor : int, default=1000000
        Voltage scale factor.

    Attributes
    ----------
    _serial_worker : _SerialWorker
        Worker for reading data from a serial port.
    _preprocess_worker : _PreprocessWorker
        Worker for preprocessing the data read by the serial worker.
    _serial_thread : QThread
        QThread associated to the serial worker.
    _preprocess_thread : QThread
        QThread associated to the preprocess worker.
    """

    def __init__(
        self,
        serial_port: str,
        n_ch: int,
        n_samp: int = 5,
        packet_size: int = 243,
        baude_rate: int = 4000000,
        gain_scale_factor: float = 2.38125854276502e-08,
        v_scale_factor: int = 1000000,
    ) -> None:
        super(ESBAcquisitionController, self).__init__()

        # Create workers and threads
        self._serial_worker = _SerialWorker(serial_port, packet_size, baude_rate)
        self._preprocess_worker = _PreprocessWorker(
            n_ch, n_samp, gain_scale_factor, v_scale_factor
        )
        self._serial_thread = QThread()
        self._serial_worker.moveToThread(self._serial_thread)
        self._preprocess_thread = QThread()
        self._preprocess_worker.moveToThread(self._preprocess_thread)

        # Create connections
        self._serial_thread.started.connect(self._serial_worker.start_acquisition)
        self._serial_worker.data_ready_sig.connect(self._preprocess_worker.preprocess)

    def start_acquisition(self):
        """Start the acquisition."""
        self._preprocess_thread.start()
        self._serial_thread.start()

    def stop_acquisition(self) -> None:
        """Stop the acquisition."""
        self._serial_worker.stop_acquisition()
        self._serial_thread.quit()
        self._serial_thread.wait()
        self._preprocess_thread.quit()
        self._preprocess_thread.wait()

    def connect_data_ready(self, fn: Callable[[np.ndarray], Any]):
        """Connect the "data ready" signal with the given function.

        Parameters
        ----------
        fn : Callable
            Function to connect to the "data ready" signal.
        """
        self._preprocess_worker.data_ready_sig.connect(fn)

    def disconnect_data_ready(self, fn: Callable[[np.ndarray], Any]):
        """Disconnect the "data ready" signal from the given function.

        Parameters
        ----------
        fn : Callable
            Function to disconnect from the "data ready" signal.
        """
        self._preprocess_worker.data_ready_sig.disconnect(fn)

    @pyqtSlot(int)
    def update_trigger(self, trigger: int) -> None:
        """This method is called automatically when the associated signal is received,
        and it update the trigger value.

        Parameters
        ----------
        trigger : int
            New trigger value.
        """
        self._serial_worker.trigger = trigger
