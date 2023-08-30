"""This module contains the TCP server controller.


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
import struct

from PySide6.QtCore import QObject, QThread, Signal, Slot


class _TCPServerWorker(QObject):
    """Worker that creates a TCP socket to control the virtual hand in Simulink.

    Parameters
    ----------
    address : str
        Server address
    port : str
        Server port.
    gestureMap : dict of {int : list of int}
        Mapping between gesture label and joint angles.

    Attributes
    ----------
    _address : str
        Server address
    _port : str
        Server port.
    _sock : socket or None
        TCP socket.
    _conn : socket or None
        Connection to the virtual hand.
    _gestureMap : dict of {int : list of int}
        Mapping between gesture label and joint angles.
    """

    def __init__(
        self, address: str, port: int, gestureMap: dict[int, list[int]]
    ) -> None:
        super(_TCPServerWorker, self).__init__()

        self._address = address
        self._port = port
        self._gestureMap = gestureMap

        self._sock = None
        self._conn = None
        self._forceExit = False

    @property
    def forceExit(self) -> bool:
        """bool: Property for forcing exit from socket accept."""
        return self._forceExit

    @forceExit.setter
    def forceExit(self, forceExit: bool) -> None:
        self._forceExit = forceExit

    def openConnection(self) -> None:
        """Open the connection for the Simulink TCP client."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.settimeout(1.0)
        self._sock.bind((self._address, self._port))
        self._sock.listen(1)
        logging.info(f"TCPServerWorker: waiting for connection on port {self._port}.")

        # Non-blocking accept
        while True:
            try:
                if self._forceExit:
                    break
                self._conn, _ = self._sock.accept()
                logging.info(
                    f"TCPServerWorker: connection on port {self._port} from {self._conn}."
                )
                break
            except socket.timeout:
                pass

    def closeConnection(self) -> None:
        """Close the connection."""
        if self._conn is not None:
            self._conn.shutdown(socket.SHUT_RDWR)
            self._conn.close()
        self._sock.shutdown(socket.SHUT_RDWR)
        self._sock.close()

    @Slot(int)
    def sendMovements(self, data: int) -> None:
        """This method is called automatically when the associated signal is received, and
        it sends the new hand position using the TCP socket.

        Parameters
        ----------
        data : int
            Gesture label.
        """
        if self._conn is not None:
            mov = self._gestureMap[data]
            self._conn.sendall(struct.pack(f"{len(mov)}i", *mov))


class TCPServerController(QObject):
    """Controller for the TCP servers.

    Parameters
    ----------
    address : str
        Server address
    port1 : str
        port for the first socket connected to the virtual hand
    port2 : str
        port for the second socket connected to the target hand
    gestureMap : dict of {int : list of int}
        Mapping between gesture label and joint angles.

    Attributes
    ----------
    _tcpServerWorker1 : _TCPServerWorker
        Instance of _TCPServerWorker.
    _tcpServerThread1 : QThread
        The QThread associated to the TCP server worker.
    _tcpServerWorker2 : _TCPServerWorker
        Instance of _TCPServerWorker.
    _tcpServerThread2 : QThread
        The QThread associated to the TCP server worker.
    """

    def __init__(
        self, address: str, port1: int, port2: int, gestureMap: dict[int, list[int]]
    ) -> None:
        super(TCPServerController, self).__init__()

        # Create worker and thread for first connection
        self._tcpServerWorker1 = _TCPServerWorker(address, port1, gestureMap)
        self._tcpServerThread1 = QThread()
        self._tcpServerWorker1.moveToThread(self._tcpServerThread1)
        self._tcpServerThread1.started.connect(self._tcpServerWorker1.openConnection)
        self._tcpServerThread1.finished.connect(self._tcpServerWorker1.closeConnection)
        # Create worker and thread for second connection
        self._tcpServerWorker2 = _TCPServerWorker(address, port2, gestureMap)
        self._tcpServerThread2 = QThread()
        self._tcpServerWorker2.moveToThread(self._tcpServerThread2)
        self._tcpServerThread2.started.connect(self._tcpServerWorker2.openConnection)
        self._tcpServerThread2.finished.connect(self._tcpServerWorker2.closeConnection)

    def signalConnect(self, sig: Signal) -> None:
        """Connect a given signal to the TCPServerWorker send method.

        Parameters
        ----------
        sig : Signal
            Qt signal to connect to the TCPServerWorker send method.
        """
        sig.connect(self._tcpServerWorker1.sendMovements)
        sig.connect(self._tcpServerWorker2.sendMovements)

    def startTransmission(self) -> None:
        """Start the transmission to TCP clients."""
        self._tcpServerThread1.start()
        self._tcpServerThread2.start()

    def stopTransmission(self) -> None:
        """Stop the transmission to TCP clients."""
        self._tcpServerWorker1.forceExit = True
        self._tcpServerWorker2.forceExit = True
        self._tcpServerThread1.quit()
        self._tcpServerThread2.quit()
        self._tcpServerThread1.wait()
        self._tcpServerThread2.wait()
