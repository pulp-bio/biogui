from __future__ import annotations

import numpy as np
from PySide6.QtCore import QObject, QThread, Signal, Slot
from scipy import signal

from ._acquisition._abc_acq_controller import AcquisitionController
from ._utils import WaveformLength, majority_voting


class _SVMWorker(QObject):
    """Worker that writes into a file the data it receives via a Qt signal.

    Parameters
    ----------
    model : object
        Trained SVM model

    Attributes
    ----------
    _f : BinaryIO
        File object.
    """

    inferenceSig = Signal(int)

    def __init__(self, model: object) -> None:
        super(_SVMWorker, self).__init__()
        self._model = model
        self._buf_index = 0
        self._nCh = 16
        self._buffer = np.zeros((720, self._nCh))
        self._WL_signal = np.zeros((480, self._nCh))
        # Filtering
        self._sos = signal.butter(N=4, Wn=20, fs=4000, btype="high", output="sos")
        self._zi = [signal.sosfilt_zi(self._sos) for _ in range(self._nCh)]

        self._c = 0

    @Slot(bytes)
    def predict(self, data: bytes) -> None:
        """This method is called automatically when the associated signal is received,
        and it writes to the file the received data.

        Parameters
        ----------
        data : bytes
            Data to write.
        """
        data = np.frombuffer(bytearray(data), dtype="float32").reshape(-1, 16 + 1)
        if self._buf_index < 144:
            self._buffer[
                (5 * (self._buf_index)) : (5 * (self._buf_index + 1)), :
            ] = data[:, : self._nCh]
            self._buf_index += 1
        else:
            for i in range(self._nCh):
                self._buffer[:, i], self._zi[i] = signal.sosfilt(
                    self._sos, self._buffer[:, i], axis=0, zi=self._zi[i]
                )
                self._WL_signal[:, i] = WaveformLength(self._buffer[:, i], 240)

            labels = self._model.predict(self._WL_signal).astype("int32")
            label = majority_voting(labels, 479).item()

            if self._c == 3:
                self.inferenceSig.emit(label)
                self._c = 0
            self._buf_index = 0
            self._c += 1


class SVMController(QObject):
    """Controller for SVM prediction.

    Parameters
    ----------
    filePath : str
        Path to the file.
    acqController : AcquisitionController
        Controller for the acquisition.

    Attributes
    ----------
    _fileWorker : _FileWorker
        Worker for writing data to a binary file.
    _fileThread : QThread
        QThread associated to the file worker.
    _acqController : AcquisitionController
        Controller for the acquisition.
    """

    def __init__(
        self,
        model: object,
        acqController: AcquisitionController,
    ) -> None:
        super(QObject, self).__init__()

        # Create worker and thread
        self._SVMWorker = _SVMWorker(model)
        self._SVMThread = QThread()
        self._SVMWorker.moveToThread(self._SVMThread)
        # Connect to acquisition controller
        self._acqController = acqController
        self._acqController.connectDataReady(self._SVMWorker.predict)

        self._SVMThread.start()

    # @Slot()
    # def stopFileWriter(self) -> None:
    #     """This method is called automatically when the associated signal is received,
    #     and it stops the file writer worker."""
    #     self._acqController.disconnectDataReady(self._SVMWorker.predict)
    #     self._SVMThread.quit()
    #     self._SVMThread.wait()