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

from ._abc_data_source import DataSource, DataSourceType
from ._dummy_data_source import DummyConfigWidget, DummyDataWorker
from ._serial_data_source import SerialConfigWidget, SerialDataSource
from ._socket_data_source import SocketConfigWidget, SocketDataSource


dataSourceFactory = {
    DataSourceType.SERIAL: SerialDataSource,
    DataSourceType.SOCKET: SocketDataSource,
    DataSourceType.DUMMY: DummyDataWorker,
}

__all__ = [
    "dataSourceFactory",
    "DataSource",
    "DataSourceType",
    "DummyConfigWidget",
    "DummyDataWorker",
    "SerialConfigWidget",
    "SerialDataSource",
    "SocketConfigWidget",
    "SocketDataSource",
]
