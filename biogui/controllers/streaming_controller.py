"""
Class implementing the streaming controller.


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

import struct
from collections import namedtuple
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable, TypeAlias

import numpy as np
from PySide6.QtCore import QObject, QThread, Signal, Slot
from scipy import signal

from .. import data_sources

DecodeFn: TypeAlias = Callable[[bytes], Sequence[np.ndarray]]
"""Type representing the decode function that translates the bytes read from the data source to actual signals."""

InterfaceModule = namedtuple(
    "InterfaceModule", "packetSize, startSeq, stopSeq, fs, nCh, sigNames, decodeFn"
)
"""Type representing the interface module to communicate with the data source."""


@dataclass
class DataPacket:
    """
    Dataclass describing a data packet.

    Attributes
    ----------
    id : str
        String identifier.
    data : ndarray
        Data packet with shape (nSamp, nCh).
    """

    id: str
    data: np.ndarray


class _FileWriterWorker(QObject):
    """
    Worker that writes into a file the data it receives via a Qt signal.

    Parameters
    ----------
    filePath : str
        File path.
    targetSignalName : str
        Target signal name.

    Attributes
    ----------
    _filePath : str
        File path.
    _targetSignalName : str
        Target signal name.
    _f : BinaryIO or None
        File object.
    _firstWrite : bool
        Whether it's the first time the worker receives data.
    """

    def __init__(self, filePath: str, targetSignalName: str) -> None:
        super().__init__()

        self._filePath = filePath
        self._targetSignalName = targetSignalName

        self._f = None
        self._firstWrite = True
        self._trigger = None

    @property
    def trigger(self) -> int | None:
        """int or None: Property representing the (optional) trigger, namely the gesture label."""
        return self._trigger

    @trigger.setter
    def trigger(self, trigger: int | None) -> None:
        self._trigger = trigger

    @Slot(DataPacket)
    def write(self, dataPacket: DataPacket) -> None:
        """
        Write to file when new data is received.

        Parameters
        ----------
        dataPacket : DataPacket
            Data to write.
        """
        if dataPacket.id != self._targetSignalName:
            return
        data = dataPacket.data

        if self._firstWrite:  # write number of channels
            nCh = data.shape[1] + 1 if self._trigger is not None else data.shape[1]
            self._f.write(struct.pack("<I", nCh))  # type: ignore
            self._firstWrite = False
            print(self._trigger)

        # Add trigger (optionally)
        if self._trigger is not None:
            data = np.concatenate(
                [
                    data,
                    np.repeat(self._trigger, data.shape[0]).reshape(-1, 1),
                ],
                axis=1,
            ).astype("float32")

        self._f.write(data.tobytes())  # type: ignore

    def openFile(self) -> None:
        """Open the file."""
        self._f = open(self._filePath, "wb")
        self._firstWrite = True

    def closeFile(self) -> None:
        """Close the file."""
        self._f.close()  # type: ignore


class _PreprocessWorker(QObject):
    """
    Worker that preprocess the binary data it receives.

    Parameters
    ----------
    decodeFn : DecodeFn
        Decode function.

    Attributes
    ----------
    _decodeFn : DecodeFn
        Decode function.
    _sigNames : list of str
        List of signal names associated to the source.
    _sos : dict
        Dictionary with filters.
    _zi : dict
        Dictionary with filter states.

    Class attributes
    ----------------
    dataReadyRawSig : Signal
        Qt Signal emitted when new raw data is available.
    dataReadyFltSig : Signal
        Qt Signal emitted when new filtered data is available.
    errorSig : Signal
        Qt Signal emitted when a configuration error occurs.
    """

    dataReadyRawSig = Signal(DataPacket)
    dataReadyFltSig = Signal(DataPacket)
    errorSig = Signal(str)

    def __init__(self, decodeFn: DecodeFn) -> None:
        super().__init__()

        self._decodeFn = decodeFn
        self._sigNames: list[str] = []
        self._sos: dict = {}
        self._zi: dict = {}
        self._errorOccurred = False

    @property
    def errorOccurred(self):
        """bool: Whether an error has occurred or not (useful to limit the number of error signals emitted)."""
        return self._errorOccurred

    @errorOccurred.setter
    def errorOccurred(self, errorOccurred: bool):
        self._errorOccurred = errorOccurred

    def addSigName(self, sigName: str) -> None:
        """
        Add a signal name to the source.

        Parameters
        ----------
        sigName : str
            Signal name to add.
        """
        self._sigNames.append(sigName)

    def removeSigName(self, sigName: str) -> None:
        """
        Remove a signal name from the source.

        Parameters
        ----------
        sigName : str
            Signal name to remove.
        """
        self._sigNames.remove(sigName)

        # Remove filters
        self._sos.pop(sigName, None)
        self._zi.pop(sigName, None)

    def configFilter(self, sigName: str, filtSettings: dict) -> None:
        """
        Configure a per-signal filter from the given settings.

        Parameters
        ----------
        sigName : str
            Signal name.
        filtSettings : dict
            Dictionary with the filter settings.
        """
        freqs = filtSettings["freqs"]
        sos = signal.butter(
            N=filtSettings["filtOrder"],
            Wn=freqs if len(freqs) > 1 else freqs[0],
            fs=filtSettings["fs"],
            btype=filtSettings["filtType"],
            output="sos",
        )
        self._sos[sigName] = sos
        self._zi[sigName] = np.zeros((sos.shape[0], 2, filtSettings["nCh"]))

    @Slot(bytes)
    def preprocess(self, data: bytes) -> None:
        """
        Decode the received packet of bytes and apply filtering.

        Parameters
        ----------
        data : bytes
            New data.
        """
        try:
            dataDecList = self._decodeFn(data)
        except (Exception,) as e:
            if not self._errorOccurred:
                self.errorSig.emit(
                    f"The provided decode function failed with the following exception:\n{e}."
                )
                self._errorOccurred = True
            return

        if len(dataDecList) != len(self._sigNames):
            if not self._errorOccurred:
                self.errorSig.emit(
                    "The provided decode function and configured signals do not match."
                )
                self._errorOccurred = True
            return

        for sigName, dataDec in zip(self._sigNames, dataDecList):
            self.dataReadyRawSig.emit(DataPacket(sigName, dataDec))

            # Filter
            if sigName in self._sos:
                try:
                    dataDec, self._zi[sigName] = signal.sosfilt(
                        self._sos[sigName], dataDec, axis=0, zi=self._zi[sigName]
                    )
                except ValueError:
                    if not self._errorOccurred:
                        self.errorSig.emit(
                            "An error occurred during filtering, check the settings."
                        )
                        self._errorOccurred = True
                    return

            self.dataReadyFltSig.emit(DataPacket(sigName, dataDec))


class StreamingController(QObject):
    """
    Controller for the streaming from the serial port using the ESB protocol.

    Parameters
    ----------
    dataSourceConfig : dict
        Dictionary with the data source configuration.
    decodeFn : DecodeFn
        The decoding function.
    parent : QObject or None, default=None
        Parent QObject.

    Attributes
    ----------
    _dataSourceWorker : DataSource
        Worker for data acquisition.
    _dataSourceThread : QThread
        The QThread associated to the data source worker.
    _preprocessWorker : _PreprocessWorker
        Worker for data pre-processing.
    _preprocessThread : QThread
        The QThread associated to the pre-processing worker.
    _fileWriterWorkers : list of _FileWriterWorker
        List of the (optional) workers for writing data to file.
    _fileWriterThreads : list of QThread
        List of the (optional) QThread associated to the file writer worker.

    Class attributes
    ----------------
    dataReadySig : Signal
        Qt Signal emitted when new filtered data is available.
    errorSig : Signal
        Qt Signal emitted when an error occurs.
    """

    dataReadySig = Signal(DataPacket)
    errorSig = Signal(str)

    def __init__(
        self,
        dataSourceConfig: dict,
        decodeFn: DecodeFn,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        # Create data source worker and thread
        self._dataSourceWorker = data_sources.getDataSource(**dataSourceConfig)
        self._dataSourceThread = QThread(self)
        self._dataSourceWorker.moveToThread(self._dataSourceThread)

        # Create pre-processing worker and thread
        self._preprocessWorker = _PreprocessWorker(decodeFn)
        self._preprocessThread = QThread(self)
        self._preprocessWorker.moveToThread(self._preprocessThread)

        # Handle signals
        self._dataSourceThread.started.connect(self._dataSourceWorker.startCollecting)
        self._dataSourceThread.finished.connect(self._dataSourceWorker.stopCollecting)
        self._dataSourceWorker.dataReadySig.connect(self._preprocessWorker.preprocess)
        self._dataSourceWorker.errorSig.connect(self._handleErrors)
        self._preprocessWorker.dataReadyFltSig.connect(
            lambda d: self.dataReadySig.emit(d)
        )  # forward filtered data
        self._preprocessWorker.errorSig.connect(self._handleErrors)

        # Optionally, create file writer worker and thread
        self._fileWriterWorkers: list[_FileWriterWorker] = []
        self._fileWriterThreads: list[QThread] = []

    def __str__(self) -> str:
        return str(self._dataSourceWorker)

    @Slot(str)
    def _handleErrors(self, errMessage: str) -> None:
        """When error occurs, stop collection and preprocessing and forward the error Qt Signal."""
        self.stopStreaming()
        self.errorSig.emit(f'StreamingController "{self.__str__()}": {errMessage}')

    def addSigName(self, sigName: str) -> None:
        """
        Add a signal name to the source.

        Parameters
        ----------
        sigName : str
            Signal name to add.
        """
        self._preprocessWorker.addSigName(sigName)

    def removeSigName(self, sigName: str) -> None:
        """
        Remove a signal name from the source.

        Parameters
        ----------
        sigName : str
            Signal name to remove.
        """
        self._preprocessWorker.removeSigName(sigName)

    def addFiltSettings(self, sigName: str, filtSettings: dict) -> None:
        """
        Configure a per-signal filter from the given settings.

        Parameters
        ----------
        sigName : str
            Signal name.
        filtSettings : dict
            Dictionary with the filter settings.
        """
        self._preprocessWorker.configFilter(sigName, filtSettings)

    def addFileSavingSettings(self, sigName: str, filePath: str) -> None:
        """
        Configure a per-signal file writer worker and thread.

        Parameters
        ----------
        sigName : str
            Signal name.
        filePath : str
            Path to the output file.
        """
        # Create worker and thread
        fileWriterWorker = _FileWriterWorker(filePath, sigName)
        fileWriterThread = QThread(self)
        fileWriterWorker.moveToThread(fileWriterThread)

        # Handle signals
        fileWriterThread.started.connect(fileWriterWorker.openFile)
        fileWriterThread.finished.connect(fileWriterWorker.closeFile)
        self._preprocessWorker.dataReadyRawSig.connect(fileWriterWorker.write)

        self._fileWriterWorkers.append(fileWriterWorker)
        self._fileWriterThreads.append(fileWriterThread)

    def setTrigger(self, trigger: int) -> None:
        """
        Set the trigger for each file writer worker.

        Parameters
        ----------
        trigger : int
            Trigger value.
        """
        for fileWriterWorker in self._fileWriterWorkers:
            fileWriterWorker.trigger = trigger

    def startStreaming(self) -> None:
        """Start streaming."""
        self._preprocessWorker.errorOccurred = False  # reset flag

        for fileWriterThread in self._fileWriterThreads:
            fileWriterThread.start()

        self._preprocessThread.start()
        self._dataSourceThread.start()

    def stopStreaming(self) -> None:
        """Stop streaming."""
        self._dataSourceWorker.stopCollecting()

        self._dataSourceThread.quit()
        self._dataSourceThread.wait()
        self._preprocessThread.quit()
        self._preprocessThread.wait()

        for fileWriterWorker, fileWriterThread in zip(
            self._fileWriterWorkers, self._fileWriterThreads
        ):
            fileWriterThread.quit()
            fileWriterThread.wait()
            fileWriterWorker.trigger = None
