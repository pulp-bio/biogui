"""This package contains the code for managing data sources.


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

from PySide6.QtWidgets import QWidget

from ._abc_data_source import DataSource, DataSourceType, ConfigWidget
from ._dummy_data_source import _DummyConfigWidget, _DummyDataSource
from ._serial_data_source import _SerialConfigWidget, _SerialDataSource
from ._socket_data_source import _SocketConfigWidget, _SocketDataSource


def getConfigWidget(dataSourceType: DataSourceType, parent: QWidget) -> ConfigWidget:
    """Factory function for producing DataConfigWidget objects.

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
        DataSourceType.SERIAL: _SerialConfigWidget,
        DataSourceType.SOCKET: _SocketConfigWidget,
        DataSourceType.DUMMY: _DummyConfigWidget,
    }
    return configWidgetDict[dataSourceType](parent)


def getDataSource(
    dataSourceType: DataSourceType, packetSize: int, **kwargs
) -> DataSource:
    """Factory function for producing DataSource objects.

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
    DataSource
        Corresponding DataSource object.
    """
    dataSourceDict = {
        DataSourceType.SERIAL: _SerialDataSource,
        DataSourceType.SOCKET: _SocketDataSource,
        DataSourceType.DUMMY: _DummyDataSource,
    }
    return dataSourceDict[dataSourceType](packetSize, **kwargs)


__all__ = [
    "DataSourceType",
    "ConfigWidget",
    "DataSource",
    "getConfigWidget",
    "getDataSource",
]
