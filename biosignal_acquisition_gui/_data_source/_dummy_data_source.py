"""Classes for the dummy data source.


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
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget

from ._abc_data_source import ConfigResult, DataConfWidget, DataWorker


class DummyConfWidget(DataConfWidget):
    """Empty widget for the dummy source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def validateConfig(self) -> ConfigResult:
        """Validate the configuration.

        Returns
        -------
        ConfigResult
            Named tuple containing:
            - whether the configuration is valid;
            - dictionary representing the configuration (if it is valid);
            - error message (if the configuration is not valid);
            - a source name to display (if the configuration is valid).
        """
        return ConfigResult(isValid=True, config={}, errMessage="", configName="Dummy")


class DummyDataWorker(DataWorker):
    """Concrete worker that collects data by generating it randomly.

    Parameters
    ----------


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

    def __init__(self) -> None:
        super().__init__()

        self._nChList = []
        self._nSamp = -1
        self._mean = 0.0
        self._std1 = 100.0
        self._std2 = 20.0
        self._prng = np.random.default_rng(seed=42)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._generate)

    @property
    def nChList(self) -> list[int]:
        """list of int: Property representing the number of channels for each signal."""
        return self._nChList

    @nChList.setter
    def nChList(self, nChList: list[int]) -> None:
        self._nChList = nChList

    @property
    def nSamp(self) -> int:
        """int: Property representing the number of samples in each packet."""
        return self._nSamp

    @nSamp.setter
    def nSamp(self, nSamp: int) -> None:
        self._nSamp = nSamp

    def _generate(self) -> None:
        """Generate random data."""
        if len(self._nChList) == 0 or self._nSamp == 0:
            self.commErrorSig.emit()
            logging.error("DataWorker: dummy generation not configured properly.")
            self._timer.stop()

        data = self._prng.normal(
            loc=self._mean, scale=self._std1, size=(self._nSamp, sum(self._nChList))
        ).astype("float32")
        self.dataReadySig.emit(data)
        self._mean += self._prng.normal(scale=self._std2)

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        self._timer.start(1)
        logging.info("DataWorker: data generation started.")

    def stopCollecting(self) -> None:
        """Stop data collection."""
        self._timer.stop()
        logging.info("DataWorker: data generation stopped.")
