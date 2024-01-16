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

from ..ui.ui_socket_config_widget import Ui_SocketConfigWidget
from ._abc_data_source import ConfigResult, ConfigWidget, DataSource, DataSourceType


class SocketConfigWidget(ConfigWidget, Ui_SocketConfigWidget):
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

    def __str__(self):
        return f"TCP socket - port {self._socketPort}"

    def exitAcceptLoop(self) -> None:
        """Exit the non-blocking accept loop."""
        self._exitAcceptLoopFlag = True

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        self._stopReadingFlag = False
        self._exitAcceptLoopFlag = False

        # Open socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)
        sock.bind(("", self._socketPort))
        sock.listen(1)

        logging.info(
            f"DataWorker: waiting for TCP connection on port {self._socketPort}."
        )

        # Non-blocking accept
        while True:
            try:
                if self._exitAcceptLoopFlag:
                    break
                conn, _ = sock.accept()

                logging.info(
                    f"DataWorker: TCP connection from {conn}, communication started."
                )

                # conn.sendall(b"=")
                while not self._stopReadingFlag:
                    data = conn.recv(self._packetSize)

                    # Check number of bytes read
                    if len(data) != self._packetSize:
                        self.commErrorSig.emit("TCP communication failed.")
                        logging.error("DataWorker: TCP communication failed.")
                        break

                    self.dataReadySig.emit(data)
                # conn.sendall(b":")

                # Close connection and socket
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()

                logging.info("DataWorker: TCP communication stopped.")

                break
            except socket.timeout:
                pass

    def stopCollecting(self) -> None:
        """Stop data collection."""
        self._stopReadingFlag = True
