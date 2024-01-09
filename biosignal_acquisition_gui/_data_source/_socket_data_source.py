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

from .._ui.ui_socket_conf_widget import Ui_SocketConfWidget
from ._abc_data_source import ConfigResult, DataConfWidget, DataWorker


class SocketConfWidget(DataConfWidget, Ui_SocketConfWidget):
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
            Named tuple containing:
            - whether the configuration is valid;
            - dictionary representing the configuration (if it is valid);
            - error message (if the configuration is not valid);
            - a source name to display (if the configuration is valid).
        """
        if not self.portTextField.hasAcceptableInput():
            return ConfigResult(
                isValid=False,
                config={},
                errMessage='The "port" field is invalid.',
                configName="",
            )

        socketPort = int(self.portTextField.text())
        return ConfigResult(
            isValid=True,
            config={"socketPort": socketPort},
            errMessage="",
            configName=f"TCP socket - port {socketPort}",
        )


class SocketDataWorker(DataWorker):
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
    _stopReadingFlag : bool
        Flag indicating to stop reading data.
    _forceExit : bool
        Flag indicating to exit the non-blocking accept loop.
    _socket : socket
        TCP socket.
    _conn : socket
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
        self._stopReadingFlag = False
        self._forceExit = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.settimeout(1.0)
        self._socket.bind(("127.0.0.1", socketPort))
        self._socket.listen(1)
        logging.info(f"DataWorker: waiting for TCP connection on port {socketPort}.")

        # Non-blocking accept
        while True:
            try:
                if self._forceExit:
                    break
                self._conn, _ = self._socket.accept()
                logging.info(f"DataWorker: TCP connection from {self._conn}.")
                break
            except socket.timeout:
                pass

    def forceExit(self) -> None:
        self._forceExit = True

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
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

    def stopReading(self) -> None:
        """Stop data collection."""
        self._stopReadingFlag = True
