"""
Classes for the TCP socket data source.


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

import logging
import socket
from asyncio import IncompleteReadError

from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QWidget

from ..ui.tcp_config_widget_ui import Ui_TCPConfigWidget
from .base import ConfigResult, ConfigWidget, DataSourceController, DataSourceType


class TCPConfigWidget(ConfigWidget, Ui_TCPConfigWidget):
    """
    Widget to configure the socket source.

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

        self.destroyed.connect(self.deleteLater)

    def validateConfig(self) -> ConfigResult:
        """
        Validate the configuration.

        Returns
        -------
        ConfigResult
            Configuration result.
        """
        if not self.portTextField.hasAcceptableInput():
            return ConfigResult(
                dataSourceType=DataSourceType.TCP,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "port" field is invalid.',
            )

        socketPort = int(self.portTextField.text())
        return ConfigResult(
            dataSourceType=DataSourceType.TCP,
            dataSourceConfig={"socketPort": socketPort},
            isValid=True,
            errMessage="",
        )


class TCPDataSourceController(DataSourceController):
    """
    Concrete DataSourceController that collects data from a TCP socket.

    Parameters
    ----------
    packetSize : int
        Size of each packet read from the socket.
    startSeq : list of bytes
        Sequence of commands to start the source.
    stopSeq : list of bytes
        Sequence of commands to stop the source.
    socketPort: int
        Socket port.

    Attributes
    ----------
    _packetSize : int
        Size of each packet read from the socket.
    _startSeq : list of bytes
        Sequence of commands to start the source.
    _stopSeq : list of bytes
        Sequence of commands to stop the source.
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
    errorSig : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(
        self,
        packetSize: int,
        startSeq: list[bytes],
        stopSeq: list[bytes],
        socketPort: int,
    ) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._socketPort = socketPort
        self._stopReadingFlag = False
        self._exitAcceptLoopFlag = False

    def __str__(self):
        return f"TCP socket - port {self._socketPort}"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        self._stopReadingFlag = False
        self._exitAcceptLoopFlag = False

        # Open socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.5)
        sock.bind(("", self._socketPort))
        sock.listen()

        logging.info(
            f"DataWorker: waiting for TCP connection on port {self._socketPort}."
        )

        # Non-blocking accept
        while not self._exitAcceptLoopFlag:
            try:
                conn, (addr, _) = sock.accept()
                conn.settimeout(5)

                logging.info(
                    f"DataWorker: TCP connection from {addr}, communication started."
                )

                # Start command
                for c in self._startSeq:
                    conn.sendall(c)

                while not self._stopReadingFlag:
                    try:
                        data = bytearray(self._packetSize)
                        pos = 0
                        while pos < self._packetSize:
                            nRead = conn.recv_into(memoryview(data)[pos:])
                            if nRead == 0:
                                raise IncompleteReadError(
                                    bytes(data[:pos]), self._packetSize
                                )
                            pos += nRead
                    except socket.timeout:
                        self.errorSig.emit("TCP communication failed.")
                        logging.error("DataWorker: TCP communication failed.")
                        return
                    except IncompleteReadError as e:
                        logging.error(
                            f"DataWorker: read only {len(e.partial)} out of {e.expected} bytes."
                        )
                        return

                    self.dataReadySig.emit(data)

                # Stop command
                for c in self._stopSeq:
                    conn.sendall(c)

                # Close connection and socket
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
                sock.close()

                logging.info("DataWorker: TCP communication stopped.")

                self._exitAcceptLoopFlag = True
            except socket.timeout:
                pass

    def stopCollecting(self) -> None:
        """Stop data collection."""
        self._exitAcceptLoopFlag = True
        self._stopReadingFlag = True
