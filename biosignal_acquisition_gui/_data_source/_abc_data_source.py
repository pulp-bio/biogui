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
from collections import namedtuple

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

ConfigResult = namedtuple("Config", ("isValid", "config", "errMessage", "configName"))


class DataConfWidgetMeta(type(QObject), ABCMeta):
    """Metaclass for the data configuration widget interface."""


class DataConfWidget(ABC, QWidget, metaclass=DataConfWidgetMeta):
    """Interface for the configuration widgets of data sources."""

    @abstractmethod
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


class DataWorkerMeta(type(QObject), ABCMeta):
    """Metaclass for the data worker interface."""


class DataWorker(ABC, QObject, metaclass=DataWorkerMeta):
    """Interface for data collection workers.

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
