"""Interfaces for data sources.


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

from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget


class DataSourceType(Enum):
    """Enum representing the data source type."""

    SERIAL = "Serial port"
    SOCKET = "Socket"
    DUMMY = "Dummy"


@dataclass
class ConfigResult:
    """Dataclass representing the result configuration.

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


class ConfigWidgetMeta(type(QObject), ABCMeta):
    """Metaclass for the interface of data source configuration widgets."""


class ConfigWidget(ABC, QWidget, metaclass=ConfigWidgetMeta):
    """Interface for data source configuration widgets."""

    @abstractmethod
    def validateConfig(self) -> ConfigResult:
        """Validate the configuration.

        Returns
        -------
        ConfigResult
            Configuration result.
        """


class DataWorkerMeta(type(QObject), ABCMeta):
    """Metaclass for the interface of data sources."""


class DataSource(ABC, QObject, metaclass=DataWorkerMeta):
    """Interface for data sources.

    Class attributes
    ----------------
    dataReadySig : Signal
        Qt Signal emitted when new data is collected.
    commErrorSig : Signal
        Qt Signal emitted when a communication error occurs.
    """

    dataReadySig = Signal(bytes)
    commErrorSig = Signal()

    @abstractmethod
    def startCollecting(self) -> None:
        """Collect data from the configured source."""

    @abstractmethod
    def stopCollecting(self) -> None:
        """Stop data collection."""
