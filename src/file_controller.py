from __future__ import annotations

from PyQt6.QtCore import QObject, QThread, pyqtSlot

from acq_controller import AcquisitionController


class _FileWorker(QObject):
    """Worker that writes into a binary file the data it receives via a Qt signal.

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
        super(QObject, self).__init__()
        self._f = open(file_path, "w")

    @pyqtSlot(bytearray)
    def write(self, data: bytearray) -> None:
        """This method is called automatically when the associated signal is received,
        and it writes to the file the received data.

        Parameters
        ----------
        data : bytearray
            New binary data.
        """
        self._f.write(" ".join([str(x) for x in data]))

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
    file_worker : _FileWorker
        Worker for writing data to a binary file.
    file_thread : QThread
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
        self.file_worker = _FileWorker(file_path)
        self.file_thread = QThread()
        self.file_worker.moveToThread(self.file_thread)
        # Connect to acquisition controller
        self.acq_controller = acq_controller
        self.acq_controller.preprocess_worker.data_ready_sig.connect(
            self.file_worker.write
        )
        self.file_thread.start()

    @pyqtSlot()
    def stop_file_writer(self) -> None:
        """This method is called automatically when the associated signal is received,
        and it stops the file writer worker."""
        self.acq_controller.preprocess_worker.data_ready_sig.disconnect(
            self.file_worker.write
        )
        self.file_worker.close_file()
        self.file_thread.quit()
        self.file_thread.wait()
