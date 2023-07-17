from __future__ import annotations

import numpy as np
from PyQt6.QtCore import QObject, QThread, pyqtSlot

from ._acquisition._abc_acq_controller import AcquisitionController


class _FileWorker(QObject):
    """Worker that writes into a file the data it receives via a Qt signal.

    Parameters
    ----------
    file_path : str
        Path to the file.

    Attributes
    ----------
    _f : BinaryIO
        File object.
    """

    def __init__(self, file_path: str) -> None:
        super(_FileWorker, self).__init__()
        self._f = open(file_path, "wb")

    @pyqtSlot(bytes)
    def write(self, data: bytes) -> None:
        """This method is called automatically when the associated signal is received,
        and it writes to the file the received data.

        Parameters
        ----------
        data : bytes
            Data to write.
        """
        self._f.write(data)

    def close_file(self) -> None:
        """Close the file."""
        self._f.close()
        print("File closed")


class FileController(QObject):
    """Controller for file writing.

    Parameters
    ----------
    file_path : str
        Path to the file.
    acq_controller : AcquisitionController
        Controller for the acquisition.

    Attributes
    ----------
    _file_worker : _FileWorker
        Worker for writing data to a binary file.
    _file_thread : QThread
        QThread associated to the file worker.
    acq_controller : AcquisitionController
        Controller for the acquisition.
    """

    def __init__(
        self,
        file_path: str,
        acq_controller: AcquisitionController,
    ) -> None:
        super(QObject, self).__init__()

        # Create worker and thread
        self._file_worker = _FileWorker(file_path)
        self._file_thread = QThread()
        self._file_worker.moveToThread(self._file_thread)
        # Connect to acquisition controller
        self._acq_controller = acq_controller
        self._acq_controller.connectDataReady(self._file_worker.write)
        self._file_thread.start()

    @pyqtSlot()
    def stop_file_writer(self) -> None:
        """This method is called automatically when the associated signal is received,
        and it stops the file writer worker."""
        self._acq_controller.disconnectDataReady(self._file_worker.write)
        self._file_worker.close_file()
        self._file_thread.quit()
        self._file_thread.wait()
