"""This module contains the controller for SVM inference.


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
from collections import deque

import torch

import numpy as np
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QWidget
from ..main_window import MainWindow
from scipy import signal
from collections import deque
from .TEMPONet_gap import TEMPONet_gap

class _SVMWorker(QObject):
    """Worker that performs inference on the data it receives via a Qt signal.

    Parameters
    ----------
    sampFreq : int
        Sampling frequency.

    Attributes
    ----------
    _sampFreq : int
        Sampling frequency.
    _bufferCount : int
        Counter for the inference buffer.
    _queue : deque
        Buffer for performing inference.

    Class attributes
    ----------------
    inferenceSig : Signal
        Qt signal emitted when inference is performed.
    """

    inferenceSig = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        self._bufferCount = 0
        self._bufferSize = 2 * 60 * 1000
        self._queue = deque()

        self._timeElapsed = 0
        self._tau = 2 * 3600

        self._model = None

    @property
    def model(self) -> torch.nn.Module:
        """SVC: Property representing the SVM model."""
        return self._model

    @model.setter
    def model(self, model: torch.nn.Module) -> None:
        self._model = model

    @Slot(np.ndarray)
    def predict(self, data: np.ndarray) -> None:
        """This method is called automatically when the associated signal is received,
        and it performs the inference on the received data.

        Parameters
        ----------
        data : ndarray
            Data to perform inference on.
        """
        for samples in data:
            self._queue.append(samples[1])  # only PPG_SX
        self._bufferCount += data.shape[0]

        if self._bufferCount >= self._bufferSize:
            data = np.asarray(self._queue)
            # Resample to 20Hz
            for i in [10,5]:
                data = signal.decimate(data,i)

            # Add time channel
            timeElapsed = self._timeElapsed + np.arange(len(data)) / 20.0
            self._timeElapsed += 30 * 20  # increment by 30s
            timeWeight = 1 - np.exp(-timeElapsed / self._tau)
            data = np.vstack([data, timeWeight])

            # Add extra dimension for 2D Convs
            data = np.expand_dims(data, -1)

            # Inference
            with torch.no_grad():
                label = self._model(data).item()

            self.inferenceSig.emit(label)
            logging.info(f"TCNWorker: predicted label {label}.")

            self._bufferCount = 0

            # update buffer
            self._queue.popleft(30000) #remove the first 30 seconds of data


class TCNInferenceController(QObject):
    """Controller for SVM inference.

    Attributes
    ----------
    _svmWorker : _SVMWorker
        Worker for performing SVM inference.
    _svmThread : QThread
        The QThread associated to the SVM worker.

    Class attributes
    ----------------
    _dataReadySig : Signal
        Qt signal emitted when data is received.
    """

    _dataReadySig = Signal(np.ndarray)

    def __init__(self) -> None:
        super().__init__()

        self._modelPath = "gui_semg_acquisition/modules/model.pth"

        # Create worker and thread
        self._svmWorker = _SVMWorker()
        self._svmThread = QThread()
        self._svmWorker.moveToThread(self._svmThread)
        
        self._svmWorker.model = TEMPONet_gap()
        self._svmWorker.model.load_state_dict(torch.load(self._modelPath))
        self._svmWorker.model.eval()
        logging.info("Model loaded!")

    def subscribe(self, mainWin: MainWindow) -> None:
        """Subscribe to instance of MainWindow.

        Parameters
        ----------
        mainWin : MainWindow
            Instance of MainWindow.
        """
        mainWin.startStreamingSig.connect(self._startInference)
        mainWin.stopStreamingSig.connect(self._stopInference)
        mainWin.closeSig.connect(self._stopInference)
        mainWin.dataReadyFltSig.connect(lambda d: self._dataReadySig.emit(d))

    def _startInference(self) -> None:
        """Start the inference."""
        
        logging.info("SVMInferenceController: inference started.")

        self._dataReadySig.connect(self._svmWorker.predict)
        self._svmThread.start()

    def _stopInference(self) -> None:
        """Stop the inference."""
        if self._svmThread.isRunning():
            self._dataReadySig.disconnect(self._svmWorker.predict)
            self._svmThread.quit()
            self._svmThread.wait()

            logging.info("SVMInferenceController: inference stopped.")
