"""
Classes for the dummy data source.


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

import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget

from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)


class DummyConfigWidget(DataSourceConfigWidget):
    """
    Empty widget for the dummy source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.destroyed.connect(self.deleteLater)

    def validateConfig(self) -> DataSourceConfigResult:
        """
        Validate the configuration.

        Returns
        -------
        DataSourceConfigResult
            Configuration result.
        """
        return DataSourceConfigResult(
            dataSourceType=DataSourceType.DUMMY,
            dataSourceConfig={},
            isValid=True,
            errMessage="",
        )

    def prefill(self, config: dict) -> None:
        """Pre-fill the form with the provided configuration.

        Parameters
        ----------
        config : dict
            Dictionary with the configuration.
        """

    def getFieldsInTabOrder(self) -> list[QWidget]:
        """
        Get the list of fields in tab order.

        Returns
        -------
        list of QWidgets
            List of the QWidgets in tab order.
        """
        return []


class DummyDataSourceWorker(DataSourceWorker):
    """
    Concrete DataSourceWorker that collects data by generating it randomly.

    Parameters
    ----------
    packetSize : int
        Number of bytes in the packet.
    startSeq : list of bytes
        Sequence of commands to start the source.
    stopSeq : list of bytes
        Sequence of commands to stop the source.

    Attributes
    ----------
    _packetSize : int
        Number of bytes in the packet (for compatibility with other data sources).
    _startSeq : list of bytes
        Sequence of commands to start the source (for compatibility with other data sources).
    _stopSeq : list of bytes
        Sequence of commands to stop the source (for compatibility with other data sources).
    _prng : Generator
        Pseudo-random number generator.
    _mean : float
        Mean of the generated data.
    _timer : QTimer
        Instance of QTimer.

    Class attributes
    ----------------
    dataPacketReady : Signal
        Qt Signal emitted when new data is collected.
    errorOccurred : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(
        self, packetSize: int, startSeq: list[bytes], stopSeq: list[bytes]
    ) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._prng = np.random.default_rng(seed=42)
        self._mean = 0.0

        self._timer = QTimer(self)
        # Fastest signal: 128 sps, 10 samples generated at once
        # -> set timer interval corresponding to one tenth of 128 sps, i.e., 78 ms
        self._timer.setInterval(78)
        self._timer.timeout.connect(self._generateData)

    def __str__(self):
        return "Dummy"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        self._timer.start()

    def stopCollecting(self) -> None:
        """Stop data collection."""
        self._timer.stop()

    def _generateData(self) -> None:
        """Generate dummy data when the QTimer ticks."""
        # 1st signal: 4 channels, 10 samples, 128sps
        data1 = self._prng.normal(loc=self._mean, scale=100.0, size=(10, 4)).astype(
            np.float32
        )
        # 2nd signal: 2 channel, 4 samples, 51.2sps
        data2 = self._prng.normal(loc=self._mean, scale=100.0, size=(4, 2)).astype(
            np.float32
        )

        # Concatenate and emit bytes
        data = np.concatenate((data1.flatten(), data2.flatten()))
        self.dataPacketReady.emit(data.tobytes())

        # Update mean
        self._mean += self._prng.normal(scale=50.0)
