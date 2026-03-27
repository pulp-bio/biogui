# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
This package contains the code for handling data sources.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from .base import DataSourceConfigWidget, DataSourceType, DataSourceWorker
from .microphone import MicrophoneConfigWidget, MicrophoneDataSourceWorker
from .serial import SerialConfigWidget, SerialDataSourceWorker
from .tcp import TCPConfigWidget, TCPDataSourceWorker
from .unix_socket import (
    UnixSocketConfigWidget,
    UnixSocketDataSourceWorker,
)


def getConfigWidget(
    dataSourceType: DataSourceType, parent: QWidget
) -> DataSourceConfigWidget:
    """
    Factory function for producing DataSourceConfigWidget objects.

    Parameters
    ----------
    dataSourceType : DataSourceType
        Type of the data source.
    parent : QWidget
        Parent QWidget.

    Returns
    -------
    DataSourceConfigWidget
        The corresponding DataSourceConfigWidget object.
    """
    configWidgetDict = {
        DataSourceType.TCP: TCPConfigWidget,
        DataSourceType.SERIAL: SerialConfigWidget,
        DataSourceType.UNIX_SOCK: UnixSocketConfigWidget,
        DataSourceType.MIC: MicrophoneConfigWidget,
    }
    return configWidgetDict[dataSourceType](parent)


def getDataSourceWorker(
    dataSourceType: DataSourceType,
    packetSize: int,
    startSeq: list[bytes],
    stopSeq: list[bytes],
    **kwargs,
) -> DataSourceWorker:
    """
    Factory function for producing DataSourceWorker objects.

    Parameters
    ----------
    dataSourceType : DataSourceType
        Type of the data source.
    packetSize : int
        Number of bytes in the packet.
    startSeq : list of bytes
        Sequence of commands to start the source.
    stopSeq : list of bytes
        Sequence of commands to stop the source.
    kwargs : dict
        Keyword arguments.

    Returns
    -------
    DataSourceWorker
        Corresponding DataSourceWorker object.
    """
    dataSourceDict = {
        DataSourceType.SERIAL: SerialDataSourceWorker,
        DataSourceType.TCP: TCPDataSourceWorker,
        DataSourceType.UNIX_SOCK: UnixSocketDataSourceWorker,
        DataSourceType.MIC: MicrophoneDataSourceWorker,
    }
    return dataSourceDict[dataSourceType](packetSize, startSeq, stopSeq, **kwargs)


__all__ = [
    "DataSourceType",
    "DataSourceConfigWidget",
    "DataSourceWorker",
    "getConfigWidget",
    "getDataSourceWorker",
]
