"""Interface for acquisition controllers.


Copyright 2023 Mattia Orlandi

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
from typing import Any, Callable

import numpy as np
from PyQt6.QtCore import QObject


class AcquisitionControllerMeta(type(QObject), ABCMeta):
    """Meta-class for acquisition controller."""


class AcquisitionController(ABC, QObject, metaclass=AcquisitionControllerMeta):
    """Interface for acquisition controllers."""

    @abstractmethod
    def start_acquisition(self):
        """Start the acquisition."""

    @abstractmethod
    def stop_acquisition(self) -> None:
        """Stop the acquisition."""

    def connect_data_ready(self, fn: Callable[[np.ndarray], Any]):
        """Connect the "data ready" signal with the given function.

        Parameters
        ----------
        fn : Callable
            Function to connect to the "data ready" signal.
        """

    def disconnect_data_ready(self, fn: Callable[[np.ndarray], Any]):
        """Disconnect the "data ready" signal from the given function.

        Parameters
        ----------
        fn : Callable
            Function to disconnect from the "data ready" signal.
        """

    @abstractmethod
    def update_trigger(self, trigger: int) -> None:
        """This method is called automatically when the associated signal is received,
        and it update the trigger value.

        Parameters
        ----------
        trigger : int
            New trigger value.
        """
