from __future__ import annotations

import serial
import numpy as np
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from scipy import signal


class SerialThread(QThread):
    """Worker that reads data from a serial port indefinitely, and sends it via a Qt signal.
    Having an infinite loop, it must directly subclass QThread.

    Parameters
    ----------
    serial_port : str
        String representing the serial port.
    packet_size : int, default=243
        Size of each packet read from the serial port.
    baude_rate : int, default=4000000
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
    """

    data_ready_sig = pyqtSignal(bytearray)

    def __init__(
        self, serial_port: str, packet_size: int = 243, baude_rate: int = 4000000
    ) -> None:
        super(QThread, self).__init__()
        self._ser = serial.Serial(serial_port, baude_rate)
        self._packet_size = packet_size
        self._trigger = 0

    def run(self) -> None:
        """Read data indefinitely from the serial port, and send it."""
        self._ser.write(b"=")
        while not self.isInterruptionRequested():
            data = self._ser.read(self._packet_size)
            data = bytearray(data)
            data[-1] = self._trigger
            self.data_ready_sig.emit(data)
        self._ser.write(b"=")
        self._ser.close()
        print("Serial stopped")

    def update_trigger(self, trigger: int) -> None:
        """Update the trigger value.

        Parameters
        ----------
        trigger : int
            New trigger value.
        """
        self._trigger = trigger
        print(self._trigger)


class FileWorker(QObject):
    """Worker that writes into a binary file the data it receives via a Qt signal.

    Parameters
    ----------
    file_path : str
        Path to the file.

    Attributes
    ----------
    stop_sig : pyqtSignal
        Signal emitted when terminating.
    _f : BinaryIO
        File object.
    """

    def __init__(self, file_path: str) -> None:
        super(QObject, self).__init__()
        self._f = open(file_path, "wb")

    @pyqtSlot(bytearray)
    def write(self, data: bytearray) -> None:
        """This method is called automatically when the associated signal is received,
        and it writes to the file the received data.

        Parameters
        ----------
        data : bytearray
            New binary data.
        """
        self._f.write(data)

    def close_file(self) -> None:
        """Close the file."""
        self._f.close()
        print("File closed")


class PreprocessWorker(QObject):
    """Worker that preprocess the binary data it receives via a Qt signal.

    Parameters
    ----------
    n_ch : int, default=16
        Number of channels.
    fs : int, default=4000
        Sampling frequency.
    n_samp : int, default=5
        Number of samples in each packet.
    gain_scale_factor : float, default=2.38125854276502e-08
        Gain scaling factor.
    v_scale_factor : int, default=1000000
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
    _counter : int
        Counter of the number of packets processed.
    _b : ndarray
        Numerator polynomials for the filter.
    _a : ndarray
        Denominator polynomials for the filter.
    _zi : list of ndarrays
        Initial state for the filter (one per channel).
    """

    data_ready_sig = pyqtSignal(object)

    def __init__(
        self,
        n_ch: int = 16,
        fs: int = 4000,
        n_samp: int = 5,
        gain_scale_factor: float = 2.38125854276502e-08,
        v_scale_factor: int = 1000000,
    ) -> None:
        super(QObject, self).__init__()
        self._n_ch = n_ch
        self._n_samp = n_samp
        self._gain_scale_factor = gain_scale_factor
        self._v_scale_factor = v_scale_factor
        self._counter = 0
        self._b, self._a = signal.iirfilter(
            2, Wn=20, fs=fs, btype="high", ftype="butter"
        )
        self._zi = [signal.lfilter_zi(self._b, self._a) for _ in range(n_ch)]

    @pyqtSlot(bytearray)
    def preprocess(self, data: bytearray) -> None:
        """This method is called automatically when the associated signal is received,
        it preprocess the received packet and emits a signal with the preprocessed data (downsampled).

        Parameters
        ----------
        data : bytearray
            New binary data.
        """
        data_ref = np.zeros(shape=(self._n_samp, self._n_ch), dtype="uint32")
        data = [x for i, x in enumerate(data) if i not in (0, 1, 242)]
        for k in range(self._n_samp):
            for i in range(self._n_ch):
                data_ref[k, i] = (
                    data[k * 48 + (3 * i)] * 256 * 256 * 256
                    + data[0 * k * 48 + (3 * i) + 1] * 256 * 256
                    + data[0 * k * 48 + (3 * i) + 2] * 256
                )
        data_ref = data_ref.view("int32").astype("float32")
        data_ref = data_ref / 256 * self._gain_scale_factor * self._v_scale_factor
        for i in range(self._n_ch):
            data_ref[:, i], self._zi[i] = signal.lfilter(
                self._b, self._a, data_ref[:, i], zi=self._zi[i]
            )

        if self._counter % 4 == 0:  # emit one in 4 packets
            self.data_ready_sig.emit(data_ref)
        self._counter += 1


class DataController(QObject):
    def __init__(
        self,
        serial_kw: dict | None = None,
        file_kw: dict | None = None,
        preprocess_kw: dict | None = None,
    ) -> None:
        super(QObject, self).__init__()

        # Handle inputs
        if serial_kw is None:
            serial_kw = {}
        if file_kw is None:
            file_kw = {}
        if preprocess_kw is None:
            preprocess_kw = {}

        # Create threads and workers
        self.serial_thread = SerialThread(**serial_kw)
        self.file_worker = FileWorker(**file_kw)
        self.preprocess_worker = PreprocessWorker(**preprocess_kw)
        self.file_thread = QThread()
        self.file_worker.moveToThread(self.file_thread)
        self.preprocess_thread = QThread()
        self.preprocess_worker.moveToThread(self.preprocess_thread)

        # Create connections
        self.serial_thread.data_ready_sig.connect(self.file_worker.write)
        self.serial_thread.data_ready_sig.connect(self.preprocess_worker.preprocess)

    def start_threads(self):
        self.file_thread.start()
        self.preprocess_thread.start()
        self.serial_thread.start()

    @pyqtSlot(int)
    def update_trigger(self, trigger: int) -> None:
        """This method is called automatically when the associated signal is received,
        and it update the trigger value.

        Parameters
        ----------
        trigger : int
            New trigger value.
        """
        self.serial_thread.update_trigger(trigger)

    @pyqtSlot()
    def stop_file_writer(self) -> None:
        self.serial_thread.data_ready_sig.disconnect(self.file_worker.write)
        self.file_worker.close_file()
        self.file_thread.quit()
        self.file_thread.wait()

    @pyqtSlot()
    def stop_acquistion(self) -> None:
        self.serial_thread.requestInterruption()
        self.serial_thread.wait()
        self.preprocess_thread.quit()
        self.preprocess_thread.wait()
