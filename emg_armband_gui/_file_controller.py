from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Slot

from ._acquisition._abc_acq_controller import AcquisitionController


class _FileWorker(QObject):
    """Worker that writes into a file the data it receives via a Qt signal.

    Parameters
    ----------
    filePath : str
        Path to the file.

    Attributes
    ----------
    _f : BinaryIO
        File object.
    """

    def __init__(self, filePath: str) -> None:
        super(_FileWorker, self).__init__()
        self._f = open(filePath, "wb")

    @Slot(bytes)
    def write(self, data: bytes) -> None:
        """This method is called automatically when the associated signal is received,
        and it writes to the file the received data.

        Parameters
        ----------
        data : bytes
            Data to write.
        """
        self._f.write(data)

    def closeFile(self) -> None:
        """Close the file."""
        self._f.close()
        print("File closed")


class FileController(QObject):
    """Controller for file writing.

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
        filePath: str,
        acqController: AcquisitionController,
    ) -> None:
        super(QObject, self).__init__()

        # Create worker and thread
        self._fileWorker = _FileWorker(filePath)
        self._fileThread = QThread()
        self._fileWorker.moveToThread(self._fileThread)
        # Connect to acquisition controller
        self._acqController = acqController
        self._acqController.connectDataReady(self._fileWorker.write)
        self._fileThread.start()

    @Slot()
    def stopFileWriter(self) -> None:
        """This method is called automatically when the associated signal is received,
        and it stops the file writer worker."""
        self._acqController.disconnectDataReady(self._fileWorker.write)
        self._fileWorker.closeFile()
        self._fileThread.quit()
        self._fileThread.wait()
