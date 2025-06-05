"""
Abstract base class for data source worker.


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

from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget


class DataSourceType(Enum):
    """Enum representing the data source type."""

    SERIAL = "Serial port"
    TCP = "TCP socket"
    FIFO = "FIFO"
    BLE = "BLE"
    MIC = "Microphone"


@dataclass
class DataSourceConfigResult:
    """
    Dataclass representing the result configuration.

    Attributes
    ----------
    dataSourceType : DataSourceType
        Type of data source.
    dataSourceConfig : dict
        Dictionary representing the data source configuration (if it's valid).
    isValid : bool
        Whether the data source configuration is valid.
    errMessage : str
        Error message (if the data source configuration is not valid).
    """

    dataSourceType: DataSourceType
    dataSourceConfig: dict
    isValid: bool
    errMessage: str


class DataSourceConfigWidgetMeta(type(QObject), ABCMeta):  # type: ignore
    """Interface of data source configuration widgets (metaclass)."""


class DataSourceConfigWidget(ABC, QWidget, metaclass=DataSourceConfigWidgetMeta):
    """Interface for data source configuration widgets."""

    @abstractmethod
    def validateConfig(self) -> DataSourceConfigResult:
        """
        Validate the configuration.

        Returns
        -------
        DataSourceConfigResult
            Configuration result.
        """

    @abstractmethod
    def prefill(self, config: dict) -> None:
        """Pre-fill the form with the provided configuration.

        Parameters
        ----------
        config : dict
            Dictionary with the configuration.
        """

    @abstractmethod
    def getFieldsInTabOrder(self) -> list[QWidget]:
        """
        Get the list of fields in tab order.

        Returns
        -------
        list of QWidgets
            List of the QWidgets in tab order.
        """


class DataSourceWorkerMeta(type(QObject), ABCMeta):  # type: ignore
    """Abstract base class for data source controllers (metaclass)."""


class DataSourceWorker(ABC, QObject, metaclass=DataSourceWorkerMeta):
    """
    Abstract base class for data source workers.

    Class attributes
    ----------------
    dataPacketReady : Signal
        Qt Signal emitted when new data is collected.
    errorOccurred : Signal
        Qt Signal emitted when a communication error occurs.
    """

    dataPacketReady = Signal(bytes)
    errorOccurred = Signal(str)

    @abstractmethod
    def startCollecting(self) -> None:
        """Collect data from the configured source."""

    @abstractmethod
    def stopCollecting(self) -> None:
        """Stop data collection."""
