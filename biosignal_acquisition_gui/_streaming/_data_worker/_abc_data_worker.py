"""Interface for data collection workers.


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

from abc import ABC, ABCMeta, abstractmethod

from PySide6.QtCore import QObject, Signal


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
