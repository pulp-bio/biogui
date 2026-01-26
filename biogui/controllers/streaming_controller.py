"""
Controller for streaming from data sources, preprocessing and saving to file.


Copyright 2024 Mattia Orlandi, Pierangelo Maria Rapa

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

import datetime
import struct
import tempfile
import time
from types import MappingProxyType

import numpy as np
import scipy
from PySide6.QtCore import QObject, QThread, Signal, Slot

from .. import data_sources
from ..utils import DecodeFn, SigData, InterfaceModule


class _FileWriterWorker(QObject):
    """
    Worker that writes into a file the data it receives via a Qt Signal.

    Parameters
    ----------
    filePath : str
        File path.
    sigInfo : dict
        Dictionary containing the signals' information.

    Attributes
    ----------
    _sigInfo : dict
        Dictionary containing the signals' information.
    _tempData : dict
        Dictionary containing, for each signal, a temporary file-like object and the number of samples written.

    Class attributes
    ----------------
    errorOccurred : Signal
        Qt Signal emitted when a configuration error occurs.
    """

    errorOccurred = Signal(str)

    def __init__(self, filePath: str, sigInfo: dict) -> None:
        super().__init__()

        self._filePath = filePath
        self._sigInfo = sigInfo

        self._dtypeMap = {
            np.dtype("bool"): "?",
            np.dtype("int8"): "b",
            np.dtype("uint8"): "B",
            np.dtype("int16"): "h",
            np.dtype("uint16"): "H",
            np.dtype("int32"): "i",
            np.dtype("uint32"): "I",
            np.dtype("int64"): "q",
            np.dtype("uint64"): "Q",
            np.dtype("float32"): "f",
            np.dtype("float64"): "d",
        }
        self._tempData: dict = {}
        self._trigger = None

    @property
    def filePath(self) -> str:
        """str: Property representing the file path."""
        return self._filePath

    @filePath.setter
    def filePath(self, filePath: str) -> None:
        self._filePath = filePath

    @property
    def trigger(self) -> int | None:
        """int or None: Property representing the (optional) trigger, namely the gesture label."""
        return self._trigger

    @trigger.setter
    def trigger(self, trigger: int | None) -> None:
        self._trigger = trigger

    def openFile(self) -> None:
        """Open the file."""
        # Create temporary files
        try:
            self._tempData["acq_ts"] = {"file": tempfile.TemporaryFile(), "nSamp": 0}
            for sigName in self._sigInfo:
                self._tempData[sigName] = {
                    "file": tempfile.TemporaryFile(),
                    "nSamp": 0,
                    "dtype": "",
                }
            if self._trigger is not None:
                self._tempData["trigger"] = {
                    "file": tempfile.TemporaryFile(),
                    "nSamp": 0,
                }
        except (OSError, PermissionError, FileNotFoundError):
            self.errorOccurred.emit("Could not open temporary files.")

    @Slot(list)
    def write(self, rawSignals: list[SigData]) -> None:
        """
        Write to in-memory file when new data is received.

        Parameters
        ----------
        rawSignals : list of SigData
            Raw signals to write.
        """
        try:
            # 1. Timestamp
            self._tempData["acq_ts"]["file"].write(
                struct.pack("<d", rawSignals[0].acq_ts)
            )
            self._tempData["acq_ts"]["nSamp"] += 1

            # 2. Signals data
            for rawSignal in rawSignals:
                self._tempData[rawSignal.sigName]["file"].write(
                    rawSignal.data.tobytes()
                )
                self._tempData[rawSignal.sigName]["nSamp"] += rawSignal.data.shape[0]

                # Save data type
                if self._tempData[rawSignal.sigName]["dtype"] != "":
                    continue
                try:
                    self._tempData[rawSignal.sigName]["dtype"] = self._dtypeMap[
                        rawSignal.data.dtype
                    ]
                except KeyError:
                    self.errorOccurred.emit(
                        f'Type "{rawSignal.data.dtype}" not supported.'
                    )
                    return

            # 3. Trigger (optional)
            if "trigger" in self._tempData:
                self._tempData["trigger"]["file"].write(
                    struct.pack("<I", self._trigger if self._trigger is not None else 0)
                )
                self._tempData["trigger"]["nSamp"] += 1
        except OSError:
            self.errorOccurred.emit("Could not open temporary files.")

    def closeFile(self) -> None:
        """Close the file."""
        # Check if file is empty
        if self._tempData["acq_ts"]["nSamp"] == 0:
            self._resetTempFiles()
            return

        # Add timestamp and extension to filename
        filePath = (
            self._filePath
            + f"_{datetime.datetime.now().replace(microsecond=0)}.bio".replace(
                " ", "_"
            ).replace(":", "-")
        )

        # Dump data to the real file
        try:
            with open(filePath, "wb") as f:
                # 1. Metadata:
                # 1.1. Number of signals
                f.write(struct.pack("<I", len(self._sigInfo)))

                # 1.2. Name, sampling rate, shape and dtype of each signal
                firstTime = True
                for sigName in self._sigInfo:
                    fs = self._sigInfo[sigName]["fs"]
                    nSamp = self._tempData[sigName]["nSamp"]
                    nCh = self._sigInfo[sigName]["nCh"]
                    dtype = self._tempData[sigName]["dtype"]

                    # Compute base sampling rate (useful for timestamp and trigger, if present)
                    if firstTime:
                        nSampBase = self._tempData["acq_ts"]["nSamp"]
                        fsBase = nSampBase * fs / nSamp if nSamp != 0 else fs
                        f.write(struct.pack("<fI", fsBase, nSampBase))
                        firstTime = False

                    f.write(
                        struct.pack(
                            f"<I{len(sigName)}sf2Ic",
                            len(sigName),
                            sigName.encode(),
                            fs,
                            nSamp,
                            nCh,
                            dtype.encode("ascii"),
                        )
                    )

                # 1.3. Trigger (optional)
                f.write(struct.pack("<?", "trigger" in self._tempData))

                # 2. Actual signals
                # 2.1. Timestamp
                self._tempData["acq_ts"]["file"].seek(0)
                f.write(self._tempData["acq_ts"]["file"].read())

                # 2.2. Signals data
                for sigName in self._sigInfo:
                    self._tempData[sigName]["file"].seek(0)
                    f.write(self._tempData[sigName]["file"].read())

                # 3. Trigger (optional)
                if "trigger" in self._tempData:
                    self._tempData["trigger"]["file"].seek(0)
                    f.write(self._tempData["trigger"]["file"].read())
        except FileNotFoundError:
            self.errorOccurred.emit(f'File "{self._filePath}" not found.')
        except PermissionError:
            self.errorOccurred.emit(
                f'Permission denied: unable to create file "{self._filePath}".'
            )
        except IsADirectoryError:
            self.errorOccurred.emit(f'File "{self._filePath}" is a directory.')
        except Exception as e:
            self.errorOccurred.emit(
                f'An error occurred while writing file "{self._filePath}": {e}.'
            )
        finally:
            self._resetTempFiles()

    def _resetTempFiles(self) -> None:
        """Reset the temporary files."""
        # 1. Timestamp
        self._tempData["acq_ts"]["file"].close()
        self._tempData["acq_ts"]["nSamp"] = 0

        # 2. Signals data
        for sigName in self._tempData:
            self._tempData[sigName]["file"].close()
            self._tempData[sigName]["nSamp"] = 0
            self._tempData[sigName]["dtype"] = ""

        # 3. Trigger (optional)
        if self._trigger is not None:
            self._tempData["trigger"]["file"].close()
            self._tempData["trigger"]["nSamp"] = 0


class _Preprocessor(QObject):
    """
    Component to preprocess binary data.

    Parameters
    ----------
    decodeFn : DecodeFn
        Decode function.
    sigsConfigs : dict
        Dictionary with the configuration for each signal, namely:
        - "fs": the sampling frequency;
        - "nCh": the number of channels;
        - "filtType": the filter type (optional);
        - "freqs": list with the cut-off frequencies (optional);
        - "filtOrder" the filter order (optional);
        - "notchFreq": frequency of the notch filter (optional);
        - "qFactor": quality factor of the notch filter (optional).
    parent : QObject or None, default=None
        Parent QObject.

    Attributes
    ----------
    _decodeFn : DecodeFn
        Decode function.
    _fs : dict of (str: float)
        Dictionary with the sampling frequency for each signal.
    _sosButter : dict
        Dictionary with Butterworth filter parameters.
    _ziButter : dict
        Dictionary with Butterworth filter states.
    _baNotch : dict
        Dictionary with powerline noise filter parameters.
    _ziNotch : dict
        Dictionary with powerline noise filter states.

    Class attributes
    ----------------
    rawSignalsReady : Signal
        Qt Signal emitted when all the decoded signals from a data source are ready to be saved.
    signalsReady : Signal
        Qt Signal emitted when all the decoded signals from a data source are ready for visualization.
    errorOccurred : Signal
        Qt Signal emitted when a configuration error occurs.
    """

    rawSignalsReady = Signal(list)
    signalsReady = Signal(list)
    errorOccurred = Signal(str)

    def __init__(
        self, decodeFn: DecodeFn, sigsConfigs: dict, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)

        self._decodeFn = decodeFn
        self._fs = {}
        self._sosButter: dict = {}
        self._ziButter: dict = {}
        self._baNotch: dict = {}
        self._ziNotch: dict = {}

        for iSigName, iSigConfig in sigsConfigs.items():
            self._fs[iSigName] = iSigConfig["fs"]
            # Optionally, configure filtering
            self.configFilter(iSigName, iSigConfig)

    def configFilter(self, sigName: str, sigConfig: dict) -> None:
        """
        Configure a per-signal filter from the given settings.

        Parameters
        ----------
        sigName : str
            Signal name.
        sigConfig : dict
            Dictionary with the signal configuration for filtering, namely:
            - "fs": the sampling frequency;
            - "nCh": the number of channels;
            - "filtType": the filter type (optional);
            - "freqs": list with the cut-off frequencies (optional);
            - "filtOrder": the filter order (optional);
            - "notchFreq": frequency of the notch filter (optional);
            - "qFactor": quality factor of the notch filter (optional).
        """
        # 1. Butterworth filter:
        if "filtType" not in sigConfig:
            # 1.1. If configuration is empty, remove previous filter (if present)
            self._sosButter.pop(sigName, None)
            self._ziButter.pop(sigName, None)
        else:
            # 1.2. Create filter
            freqs = sigConfig["freqs"]
            sosButter = scipy.signal.butter(
                N=sigConfig["filtOrder"],
                Wn=freqs if len(freqs) > 1 else freqs[0],
                fs=sigConfig["fs"],
                btype=sigConfig["filtType"],
                output="sos",
            )
            self._sosButter[sigName] = sosButter
            self._ziButter[sigName] = np.stack(
                [scipy.signal.sosfilt_zi(sosButter) for _ in range(sigConfig["nCh"])],
                axis=-1,
            )

        # 2. Powerline noise filter:
        if "notchFreq" not in sigConfig:
            # 2.1. If configuration is empty, remove previous filter (if present)
            self._baNotch.pop(sigName, None)
            self._ziNotch.pop(sigName, None)
        else:
            # 2.2. Create filter
            b, a = scipy.signal.iirnotch(
                w0=sigConfig["notchFreq"],
                Q=sigConfig["qFactor"],
                fs=sigConfig["fs"],
            )
            self._baNotch[sigName] = (b, a)
            self._ziNotch[sigName] = np.stack(
                [scipy.signal.lfilter_zi(b, a) for _ in range(sigConfig["nCh"])],
                axis=-1,
            )

    @Slot(bytes)
    def preprocess(self, data: bytes) -> None:
        """
        Decode the received packet of bytes and apply filtering.

        Parameters
        ----------
        data : bytes
            New data packet.
        """
        acq_ts = time.time()
        try:
            dataDec = self._decodeFn(data)
        except (Exception,) as e:
            self.errorOccurred.emit(
                f"The provided decode function failed with the following exception:\n{e}."
            )
            return

        if dataDec.keys() != self._fs.keys():
            self.errorOccurred.emit(
                "The provided decode function and configured signals do not match."
            )
            return

        rawSignals = []
        signals = []
        for sigName, sigData in dataDec.items():
            if sigData is None:
                continue
            rawSignals.append(SigData(sigName, sigData, acq_ts))
            dtype = sigData.dtype

            # Filtering
            try:
                if sigName in self._sosButter:
                    sigData, self._ziButter[sigName] = scipy.signal.sosfilt(
                        self._sosButter[sigName],
                        sigData,
                        axis=0,
                        zi=self._ziButter[sigName],
                    )
                if sigName in self._baNotch:
                    sigData, self._ziNotch[sigName] = scipy.signal.lfilter(
                        *self._baNotch[sigName],
                        sigData,
                        axis=0,
                        zi=self._ziNotch[sigName],
                    )
            except ValueError:
                self.errorOccurred.emit(
                    "An error occurred during filtering, check the settings."
                )
                return
            signals.append(SigData(sigName, sigData.astype(dtype), acq_ts))

        # Emit raw and filtered signals
        self.rawSignalsReady.emit(rawSignals)
        self.signalsReady.emit(signals)


class StreamingController(QObject):
    """
    Controller for streaming data from a source.

    Parameters
    ----------
    dataSourceWorkerArgs : dict
        Dictionary with the arguments of the data source worker:
        - "dataSourceType": the data source type;
        - "packetSize": the packet size;
        - "startSeq": the sequence of commands to start the data source;
        - "stopSeq": the sequence of commands to stop the data source;
        - the data source type-specific configuration parameters.
    decodeFn : DecodeFn
        The decoding function.
    filePath : str or None
        The file path where the data will be saved (if specified).
    sigsConfigs : dict
        Dictionary with the configuration for each signal, namely:
        - "fs": the sampling frequency;
        - "nCh": the number of channels;
        - "filtType": the filter type (optional);
        - "freqs": list with the cut-off frequencies (optional);
        - "filtOrder" the filter order (optional);
        - "notchFreq": frequency of the notch filter (optional);
        - "qFactor": quality factor of the notch filter (optional).
    parent : QObject or None, default=None
        Parent QObject.

    Attributes
    ----------
    _dataSourceWorker : DataSourceWorker
        Worker for data acquisition.
    _dataSourceThread : QThread
        The QThread associated to the data source worker.
    _preprocessor : _Preprocessor
        Component for data pre-processing.
    _fileWriterWorker : _FileWriterWorker or None
        Workers for writing data to file.
    _fileWriterThread : QThread or None
        The QThread associated to the file writer worker.

    Class attributes
    ----------------
    signalsReady : Signal
        Qt Signal emitted when all the decoded signals from a data source are ready for visualization.
    errorOccurred : Signal
        Qt Signal emitted when an error occurs.
    """

    signalsReady = Signal(list)
    errorOccurred = Signal(str)

    def __init__(
        self,
        dataSourceWorkerArgs: dict,
        decodeFn: DecodeFn,
        filePath: str | None,
        sigsConfigs: dict,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        # Create data source worker and thread
        self._dataSourceWorker = data_sources.getDataSourceWorker(
            **dataSourceWorkerArgs
        )
        self._dataSourceThread = QThread(self)
        self._dataSourceWorker.moveToThread(self._dataSourceThread)
        self._dataSourceThread.started.connect(self._dataSourceWorker.startCollecting)
        self._dataSourceThread.finished.connect(self._dataSourceWorker.stopCollecting)
        self._dataSourceThread.destroyed.connect(self._dataSourceWorker.deleteLater)

        # Create pre-processor
        self._preprocessor = _Preprocessor(decodeFn, sigsConfigs, parent=self)

        # Store signal specifications
        self._sigInfo = {
            iSigName: {k: v for k, v in iSigInfo.items() if k in ("fs", "nCh")}
            for iSigName, iSigInfo in sigsConfigs.items()
        }

        # Optionally, create file writer worker and thread
        self._fileWriterWorker, self._fileWriterThreads = None, None
        if filePath:
            self._fileWriterWorker = _FileWriterWorker(filePath, self._sigInfo)
            self._fileWriterThread = QThread(self)
            self._fileWriterWorker.moveToThread(self._fileWriterThread)
            self._fileWriterThread.started.connect(self._fileWriterWorker.openFile)
            self._fileWriterThread.finished.connect(self._fileWriterWorker.closeFile)
            self._fileWriterThread.destroyed.connect(self._fileWriterWorker.deleteLater)

    def __str__(self) -> str:
        return str(self._dataSourceWorker)

    @property
    def sigInfo(self) -> MappingProxyType:
        """MappingProxyType: Property representing a read-only view of the signals specification dictionary."""
        return MappingProxyType(self._sigInfo)

    @Slot(list)
    def _forwardData(self, signal: list) -> None:
        """When the signals are ready, forward the data via a Qt Signal."""
        self.signalsReady.emit(signal)

    @Slot(str)
    def _handleErrors(self, errMessage: str) -> None:
        """When error occurs, forward the error via a Qt Signal."""
        self.errorOccurred.emit(
            f'StreamingController "{self.__str__()}" raised the following error:\n\n{errMessage}'
        )

    def editDataSourceConfig(self, dataSourceConfig: dict) -> None:
        """
        Configure the data source from the given settings.

        Parameters
        ----------
        dataSourceConfig : dict
            Dictionary with the data source configuration, namely:
            - "dataSourceType": the data source type;
            - "interfaceModule": the interface module;
            - the data source type-specific configuration parameters;
            - "filePath": the file path (optional);
            - "sigsConfigs": dictionary with signal configuration.
        """
        # Unpack config
        dataSourceWorkerArgs = {
            k: v
            for k, v in dataSourceConfig.items()
            if k not in ("interfacePath", "interfaceModule", "filePath", "sigsConfigs")
        }
        interfaceModule: InterfaceModule = dataSourceConfig["interfaceModule"]
        filePath: str | None = dataSourceConfig.get("filePath", None)
        dataSourceWorkerArgs["packetSize"] = interfaceModule.packetSize
        dataSourceWorkerArgs["startSeq"] = interfaceModule.startSeq
        dataSourceWorkerArgs["stopSeq"] = interfaceModule.stopSeq

        # 1. Data source settings
        self._dataSourceWorker = data_sources.getDataSourceWorker(
            **dataSourceWorkerArgs
        )
        self._dataSourceThread = QThread(self)
        self._dataSourceWorker.moveToThread(self._dataSourceThread)
        self._dataSourceThread.started.connect(self._dataSourceWorker.startCollecting)
        self._dataSourceThread.finished.connect(self._dataSourceWorker.stopCollecting)

        # 2. Pre-processing settings
        self._preprocessor = _Preprocessor(
            interfaceModule.decodeFn, dataSourceConfig["sigsConfigs"]
        )

        # 3. File writer settings:
        # 3.1. If configuration is empty, remove previous worker and thread (if present)
        if filePath is None:
            self._fileWriterWorker = None
            self._fileWriterThread = None
            return

        # 3.2. Otherwise, initialize file writer
        self._fileWriterWorker = _FileWriterWorker(filePath, interfaceModule.sigInfo)
        self._fileWriterThread = QThread(self)
        self._fileWriterWorker.moveToThread(self._fileWriterThread)
        self._fileWriterThread.started.connect(self._fileWriterWorker.openFile)
        self._fileWriterThread.finished.connect(self._fileWriterWorker.closeFile)

    def editSigConfig(self, sigName: str, sigConfig: dict) -> None:
        """
        Configure a per-signal filter from the given settings.

        Parameters
        ----------
        sigName : str
            Signal name.
        sigConfig : dict
            Dictionary with the signal configuration, namely:
            - "fs": the sampling frequency;
            - "nCh": the number of channels;
            - "filtType": the filter type (optional);
            - "freqs": list with the cut-off frequencies (optional);
            - "filtOrder": the filter order (optional);
            - "notchFreq": frequency of the notch filter (optional);
            - "qFactor": quality factor of the notch filter (optional).
        """
        self._preprocessor.configFilter(sigName, sigConfig)

    def setTrigger(self, trigger: int | None) -> None:
        """
        Set the trigger for each file writer worker.

        Parameters
        ----------
        trigger : int or None
            Trigger value.
        """
        if self._fileWriterWorker is not None:
            self._fileWriterWorker.trigger = trigger

    def startStreaming(self) -> None:
        """Start streaming."""
        # Connect Qt Signals
        self._dataSourceWorker.dataPacketReady.connect(self._preprocessor.preprocess)
        self._dataSourceWorker.errorOccurred.connect(self._handleErrors)
        self._preprocessor.signalsReady.connect(self._forwardData)
        self._preprocessor.errorOccurred.connect(self._handleErrors)

        # Start file writer thread
        if self._fileWriterWorker is not None and self._fileWriterThread is not None:
            self._preprocessor.rawSignalsReady.connect(self._fileWriterWorker.write)
            self._fileWriterWorker.errorOccurred.connect(self._handleErrors)
            self._fileWriterThread.start()

        # Start data source thread
        self._dataSourceThread.start()

    def stopStreaming(self) -> None:
        """Stop streaming."""
        if not self._dataSourceThread.isRunning():
            return

        # Stop data source thread
        self._dataSourceThread.quit()
        self._dataSourceThread.wait()

        # Stop file writer thread
        if self._fileWriterWorker is not None and self._fileWriterThread is not None:
            self._fileWriterThread.quit()
            self._fileWriterThread.wait()
            self._fileWriterWorker.trigger = None
            self._preprocessor.rawSignalsReady.disconnect(self._fileWriterWorker.write)

        # Disconnect Qt Signals
        self._dataSourceWorker.dataPacketReady.disconnect(self._preprocessor.preprocess)
        self._dataSourceWorker.errorOccurred.disconnect(self._handleErrors)
        self._preprocessor.signalsReady.disconnect(self._forwardData)
        self._preprocessor.errorOccurred.disconnect(self._handleErrors)
