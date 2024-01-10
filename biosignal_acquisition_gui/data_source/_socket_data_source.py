"""Classes for the TCP socket data source.


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

import logging
import socket

from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QWidget

from .._ui.ui_socket_config_widget import Ui_SocketConfigWidget
from ._abc_data_source import ConfigResult, DataConfigWidget, DataSource, DataSourceType


class SocketConfigWidget(DataConfigWidget, Ui_SocketConfigWidget):
    """Widget to configure the socket source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        # Validation rules
        minPort, maxPort = 1024, 49151
        self.portTextField.setToolTip(f"Integer between {minPort} and {maxPort}")
        portValidator = QIntValidator(bottom=minPort, top=maxPort)
        self.portTextField.setValidator(portValidator)

    def validateConfig(self) -> ConfigResult:
        """Validate the configuration.

        Returns
        -------
        ConfigResult
            Configuration result.
        """
        if not self.portTextField.hasAcceptableInput():
            return ConfigResult(
                dataSourceType=DataSourceType.SOCKET,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "port" field is invalid.',
            )

        socketPort = int(self.portTextField.text())
        return ConfigResult(
            dataSourceType=DataSourceType.SOCKET,
            dataSourceConfig={"socketPort": socketPort},
            isValid=True,
            errMessage="",
        )


class SocketDataSource(DataSource):
    """Concrete worker that collects data from a TCP socket.

    Parameters
    ----------
    packetSize : int
        Size of each packet read from the socket.
    socketPort: int
        Socket port.

    Attributes
    ----------
    _packetSize : int
        Size of each packet read from the socket.
    _socketPort: int
        Socket port.
    _stopReadingFlag : bool
        Flag indicating to stop reading data.
    _exitAcceptLoopFlag : bool
        Flag indicating to exit the non-blocking accept loop.
    _socket : socket or None
        TCP socket.
    _conn : socket or None
        Connection object.

    Class attributes
    ----------------
    dataReadySig : Signal
        Qt Signal emitted when new data is collected.
    commErrorSig : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(self, packetSize: int, socketPort: int) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._socketPort = socketPort
        self._stopReadingFlag = False
        self._exitAcceptLoopFlag = False
        self._socket = None
        self._conn = None

    def __str__(self):
        return f"TCP socket - port {self._socketPort}"

    def _openSocket(self):
        self._exitAcceptLoopFlag = False

        # Open socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.settimeout(1.0)
        self._socket.bind(("", self._socketPort))
        self._socket.listen(1)

        logging.info(
            f"DataWorker: waiting for TCP connection on port {self._socketPort}."
        )

        # Non-blocking accept
        while True:
            try:
                if self._exitAcceptLoopFlag:
                    break
                self._conn, _ = self._socket.accept()
                logging.info(f"DataWorker: TCP connection from {self._conn}.")
                break
            except socket.timeout:
                pass

    def exitAcceptLoop(self) -> None:
        """Exit the non-blocking accept loop."""
        self._exitAcceptLoopFlag = True

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        self._openSocket()

        logging.info("DataWorker: TCP communication started.")

        # self._conn.sendall(b"=")
        while not self._stopReadingFlag:
            data = self._conn.recv(self._packetSize)

            # Check number of bytes read
            if len(data) != self._packetSize:
                self.commErrorSig.emit()
                logging.error("DataWorker: TCP communication failed.")
                break

            self.dataReadySig.emit(data)
        self._conn.sendall(b":")

        # Close connection and socket
        self._conn.shutdown(socket.SHUT_RDWR)
        self._conn.close()
        self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()

        logging.info("DataWorker: TCP communication stopped.")

    def stopCollecting(self) -> None:
        """Stop data collection."""
        self._stopReadingFlag = True
