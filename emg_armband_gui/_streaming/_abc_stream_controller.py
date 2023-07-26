"""Interface for streaming controllers.


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

from PySide6.QtCore import QObject, Signal


class StreamingControllerMeta(type(QObject), ABCMeta):
    """Meta-class for the streaming controller interface."""


class StreamingController(ABC, QObject, metaclass=StreamingControllerMeta):
    """Interface for streaming controllers.

    Class attributes
    ----------------
    dataReadySig : Signal
        Signal emitted when new data is available.
    dataReadyFltSig : Signal
        Signal emitted when new filtered data is available.
    serialErrorSig : Signal
        Signal emitted when an error with the serial transmission occurred.
    """

    dataReadySig: Signal
    dataReadyFltSig: Signal
    serialErrorSig: Signal

    @abstractmethod
    def startStreaming(self) -> None:
        """Start streaming."""

    @abstractmethod
    def stopStreaming(self) -> None:
        """Stop streaming."""
