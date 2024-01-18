"""Class implementing the streaming controller.


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
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable, TypeAlias

import numpy as np
from PySide6.QtCore import QObject, QThread, Signal, Slot
from scipy import signal

from . import data_source

DecodeFn: TypeAlias = Callable[[bytes], Sequence[np.ndarray]]


@dataclass
class DataPacket:
    """Dataclass describing a data packet.

    Attributes
    ----------
    id : str
        String identifier.
    data : ndarray
        Data packet with shape (nSamp, nCh).
    """

    id: str
    data: np.ndarray


class _PreprocessWorker(QObject):
    """Worker that preprocess the binary data it receives.

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
        """Add a signal name to the source.

        Parameters
        ----------
        sigName : str
            Signal name to add.
        """
        self._sigNames.append(sigName)

    def removeSigName(self, sigName: str) -> None:
        """Remove a signal name from the source.

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
        """Configure a per-signal filter from the given settings.

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
        """Decode the received packet of bytes and apply filtering.

        Parameters
        ----------
        data : ndarray
            New data.
        """
        try:
            dataDecList = self._decodeFn(data)
        except (Exception,):
            if not self._errorOccurred:
                self.errorSig.emit("The provided decode function failed.")
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
                dataDec, self._zi[sigName] = signal.sosfilt(
                    self._sos[sigName], dataDec, axis=0, zi=self._zi[sigName]
                )

            self.dataReadyFltSig.emit(DataPacket(sigName, dataDec))


class StreamingController(QObject):
    """Controller for the streaming from the serial port using the ESB protocol.

    Parameters
    ----------
    dataSourceConfig : dict
        Dictionary with the data source configuration.
    decodeFn: DecodeFn
        Decode function.
    parent : QObject or None, default=None
        Parent QObject.

    Attributes
    ----------
    _dataSource : _DataWorker
        Worker for data collection.
    _preprocessWorker : _PreprocessWorker
        Worker for data pre-processing.
    _dataThread : QThread
        The QThread associated to the data worker.
    _preprocessThread : QThread
        The QThread associated to the preprocess worker.

    Class attributes
    ----------------
    dataReadyRawSig : Signal
        Qt Signal emitted when new raw data is available.
    dataReadyFltSig : Signal
        Qt Signal emitted when new filtered data is available.
    errorSig : Signal
        Qt Signal emitted when an error occurs.
    """

    dataReadyRawSig = Signal(DataPacket)
    dataReadyFltSig = Signal(DataPacket)
    errorSig = Signal(str)

    def __init__(
        self,
        dataSourceConfig: dict,
        decodeFn: DecodeFn,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        # Create data worker and thread
        self._dataSource = data_source.getDataSource(**dataSourceConfig)
        self._dataThread = QThread(self)
        self._dataSource.moveToThread(self._dataThread)

        # Create preprocess worker and thread
        self._preprocessWorker = _PreprocessWorker(decodeFn)
        self._preprocessThread = QThread(self)
        self._preprocessWorker.moveToThread(self._preprocessThread)

        # Handle signals
        self._dataThread.started.connect(self._dataSource.startCollecting)  # type: ignore
        self._dataSource.dataReadySig.connect(self._preprocessWorker.preprocess)
        self._dataSource.errorSig.connect(self._handleErrors)
        self._preprocessWorker.errorSig.connect(self._handleErrors)
        self._preprocessWorker.dataReadyRawSig.connect(
            lambda d: self.dataReadyRawSig.emit(d)
        )  # forward raw data
        self._preprocessWorker.dataReadyFltSig.connect(
            lambda d: self.dataReadyFltSig.emit(d)
        )  # forward filtered data

    def __str__(self) -> str:
        return str(self._dataSource)

    @Slot(str)
    def _handleErrors(self, errMessage: str) -> None:
        """When error occurs, stop collection and preprocessing and forward the error Qt Signal."""
        self.stopStreaming()
        self.errorSig.emit(f'StreamingController "{self.__str__()}": {errMessage}')

    def addSigName(self, sigName: str) -> None:
        """Add a signal name to the source.

        Parameters
        ----------
        sigName : str
            Signal name to add.
        """
        self._preprocessWorker.addSigName(sigName)

    def removeSigName(self, sigName: str) -> None:
        """Remove a signal name from the source.

        Parameters
        ----------
        sigName : str
            Signal name to remove.
        """
        self._preprocessWorker.removeSigName(sigName)

    def addFiltSettings(self, sigName: str, filtSettings: dict) -> None:
        """Configure a per-signal filter from the given settings.

        Parameters
        ----------
        sigName : str
            Signal name.
        filtSettings : dict
            Dictionary with the filter settings.
        """
        self._preprocessWorker.configFilter(sigName, filtSettings)

    def startStreaming(self) -> None:
        """Start streaming."""
        self._preprocessWorker.errorOccurred = False  # reset flag
        # Start thread
        self._preprocessThread.start()
        self._dataThread.start()

        logging.info("StreamingController: threads started.")

    def stopStreaming(self) -> None:
        """Stop streaming."""
        # Check if threads are running
        if self._dataThread.isRunning() and self._preprocessThread.isRunning():
            self._dataSource.stopCollecting()
            self._dataThread.quit()
            self._dataThread.wait()
            self._preprocessThread.quit()
            self._preprocessThread.wait()

            logging.info("StreamingController: threads stopped.")
