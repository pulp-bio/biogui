"""
This package contains the code for handling data sources.


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

from PySide6.QtWidgets import QWidget

from .base import ConfigWidget, DataSourceWorker, DataSourceType
from .dummy import DummyConfigWidget, DummyDataSourceWorker
from .fifo import FIFOConfigWidget, FIFODataSourceWorker
from .serial import SerialConfigWidget, SerialDataSourceWorker
from .tcp import TCPConfigWidget, TCPDataSourceWorker


def getConfigWidget(dataSourceType: DataSourceType, parent: QWidget) -> ConfigWidget:
    """
    Factory function for producing DataConfigWidget objects.

    Parameters
    ----------
    dataSourceType : DataSourceType
        Type of the data source.
    parent : QWidget
        Parent QWidget.

    Returns
    -------
    ConfigWidget
        The corresponding DataSourceConfigWidget object.
    """
    configWidgetDict = {
        DataSourceType.SERIAL: SerialConfigWidget,
        DataSourceType.TCP: TCPConfigWidget,
        DataSourceType.DUMMY: DummyConfigWidget,
        DataSourceType.FIFO: FIFOConfigWidget,
    }
    return configWidgetDict[dataSourceType](parent)


def getDataSourceWorker(
    dataSourceType: DataSourceType, packetSize: int, **kwargs
) -> DataSourceWorker:
    """
    Factory function for producing DataSourceWorker objects.

    Parameters
    ----------
    dataSourceType : DataSourceType
        Type of the data source.
    packetSize : int
        Number of bytes in the packet.
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
        DataSourceType.DUMMY: DummyDataSourceWorker,
        DataSourceType.FIFO: FIFODataSourceWorker,
    }
    return dataSourceDict[dataSourceType](packetSize, **kwargs)


__all__ = [
    "DataSourceType",
    "ConfigWidget",
    "DataSourceWorker",
    "getConfigWidget",
    "getDataSourceWorker",
]