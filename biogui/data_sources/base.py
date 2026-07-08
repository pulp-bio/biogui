# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Abstract base class for data source worker.
"""

from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget


class DataSourceType(Enum):
    """Enum representing the data source type."""

    TCP = "TCP socket"
    SERIAL = "Serial port"
    UNIX_SOCK = "Unix socket"
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

    Parameters
    ----------
    packetSize : int | list[tuple[int, int]]
        List of (header_byte, packet_size) tuples for different packet types, or a single packet size.
    startSeq : list[bytes | float]
        Sequence of commands to start the source.
    stopSeq : list[bytes | float]
        Sequence of commands to stop the source.

    Attributes
    ----------
    _packetSize : int | list[tuple[int, int]]
        Size of each packet read from the serial port, or list of (header_byte, packet_size) tuples.
    _startSeq : list[bytes | float]
        Sequence of commands to start the source.
    _stopSeq : list[bytes | float]
        Sequence of commands to stop the source.
    _trigger : int | None
        Optional trigger value for the data source.

    Class attributes
    ----------------
    dataPacketReady : Signal
        Qt Signal emitted when new data is collected; it's a tuple of data (ndarray), timestamp (float),
        and optional trigger (tuple with integer id and string label, or None).
    errorOccurred : Signal
        Qt Signal emitted when a communication error occurs.
    """

    dataPacketReady = Signal(bytes, float, object)
    errorOccurred = Signal(str)

    def __init__(
        self,
        packetSize: int | list[tuple[int, int]],
        startSeq: list[bytes | float],
        stopSeq: list[bytes | float],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._trigger: tuple[int, str] | None = None

    @property
    def trigger(self) -> tuple[int, str] | None:
        """tuple[int, str] or None: Property representing the (optional) trigger."""
        return self._trigger

    @trigger.setter
    def trigger(self, trigger: tuple[int, str] | None) -> None:
        self._trigger = trigger

    @abstractmethod
    def startCollecting(self) -> None:
        """Collect data from the configured source."""

    @abstractmethod
    def stopCollecting(self) -> None:
        """Stop data collection."""
