"""Class implementing the data collection worker for dummy generation.


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

import numpy as np
from PySide6.QtCore import QObject, QTimer

from ._abc_data_worker import DataWorker


class DummyDataWorker(DataWorker):
    """Concrete worker that collects data by generating it randomly.

    Parameters
    ----------
    parent : QObject or None, default=None
        Parent QObject.

    Attributes
    ----------
    _mean : float
        Current mean of the generated data.
    _std1 : float
        Standard deviation of the generated data.
    _std2 : float
        Standard deviation characterizing the drifting of the mean.
    _prng : Generator
        Pseudo-random number generator.
    _timer : QTimer
        Timer.

    Class attributes
    ----------------
    dataReadySig : Signal
        Qt Signal emitted when new data is collected.
    commErrorSig : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self._nCh = 0
        self._nSamp = 0
        self._mean = 0.0
        self._std1 = 100.0
        self._std2 = 100.0
        self._prng = np.random.default_rng(seed=42)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._generate)

    @property
    def nCh(self) -> int:
        """int: Property representing the number of channels."""
        return self._nCh

    @nCh.setter
    def nCh(self, nCh: int) -> None:
        self._nCh = nCh

    @property
    def nSamp(self) -> int:
        """int: Property representing the number of samples in each packet."""
        return self._nSamp

    @nSamp.setter
    def nSamp(self, nSamp: int) -> None:
        self._nSamp = nSamp

    def _generate(self) -> None:
        """Generate random data."""
        if self._nCh == 0 or self._nSamp == 0:
            self.commErrorSig.emit()
            logging.error("DataWorker: dummy generation not configured properly.")
            self._timer.stop()

        data = self._prng.normal(
            loc=self._mean, scale=self._std1, size=(self._nSamp, self._nCh)
        ).astype("float32")
        self.dataReadySig.emit(data)
        self._mean += self._prng.normal(scale=self._std2)

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        self._timer.start(1)
        logging.info("DataWorker: data generation started.")

    def stopReading(self) -> None:
        """Stop data collection."""
        self._timer.stop()
        logging.info("DataWorker: data generation stopped.")
