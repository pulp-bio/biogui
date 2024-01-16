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
import time

import numpy as np
from PySide6.QtWidgets import QWidget

from ._abc_data_source import ConfigResult, ConfigWidget, DataSource, DataSourceType


class DummyConfigWidget(ConfigWidget):
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
            Configuration result.
        """
        return ConfigResult(
            dataSourceType=DataSourceType.DUMMY,
            dataSourceConfig={},
            isValid=True,
            errMessage="",
        )


class DummyDataSource(DataSource):
    """Concrete worker that collects data by generating it randomly.

    Parameters
    ----------
    packetSize : int
        Number of bytes in the packet.

    Attributes
    ----------
    _packetSize : int
        Number of bytes in the packet (for compatibility with other data sources).
    _mean : float
        Current mean of the generated data.
    _std1 : float
        Standard deviation of the generated data.
    _std2 : float
        Standard deviation characterizing the drifting of the mean.
    _prng : Generator
        Pseudo-random number generator.
    _stopGeneratingFlag : bool
        Flag indicating to stop reading data.

    Class attributes
    ----------------
    dataReadySig : Signal
        Qt Signal emitted when new data is collected.
    errorSig : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(self, packetSize: int) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._mean = 0.0
        self._std1 = 100.0
        self._std2 = 20.0
        self._prng = np.random.default_rng(seed=42)

        self._stopGeneratingFlag = False

    def __str__(self):
        return "Dummy"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        self._stopGeneratingFlag = False

        logging.info("DataWorker: data generation started.")

        while not self._stopGeneratingFlag:
            data = self._prng.normal(
                loc=self._mean, scale=self._std1, size=(5, 16)
            ).astype("float32")
            self.dataReadySig.emit(data.tobytes())
            self._mean += self._prng.normal(scale=self._std2)

            time.sleep(5 / 4000)

        logging.info("DataWorker: data generation stopped.")

    def stopCollecting(self) -> None:
        """Stop data collection."""
        self._stopGeneratingFlag = True
