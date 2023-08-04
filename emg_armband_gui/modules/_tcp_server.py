"""This module containes the TCP server controller.


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

from PySide6.QtCore import QObject, QThread, Signal, Slot


class _TCPServerWorker(QObject):
    """Worker that creates two TCP sockets to control the virtual hands in Simulink.

    Parameters
    ----------
    address : str
        Server address
    port1 : str
        Port for the first socket connected to the virtual hand.
    port2 : str
        Port for the second socket connected to the target hand.
    gestureMap : dict of {int : list of int}
        Mapping between gesture label and joint angles.

    Attributes
    ----------
    _address : str
        Server address
    _port1 : str
        Port for the first socket connected to the virtual hand.
    _port2 : str
        Port for the second socket connected to the target hand.
    _sock1 : socket or None
        The socket for the virtual hand.
    _sock2 : socket or None
        The socket for the target hand.
    _conn1 : socket or None
        Connection to the virtual hand.
    _conn2 : socket or None
        Connection to the target hand.
    _gestureMap : dict of {int : list of int}
        Mapping between gesture label and joint angles.
    """

    def __init__(
        self, address: str, port1: int, port2: int, gestureMap: dict[int, list[int]]
    ) -> None:
        super(_TCPServerWorker, self).__init__()

        self._address = address
        self._port1 = port1
        self._port2 = port2

        self._sock1 = None
        self._sock2 = None
        self._conn1 = None
        self._conn2 = None

        self._gestureMap = gestureMap

    def openConnection(self) -> None:
        """Open the connection for the Simulink TCP clients."""
        self._sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock1.bind((self._address, self._port1))
        self._sock1.listen(1)
        logging.info(f"TCPServerWorker: waiting for connection on port {self._port1}.")

        self._sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock2.bind((self._address, self._port2))
        self._sock2.listen(1)
        logging.info(f"TCPServerWorker: waiting for connection on port {self._port2}.")

        self._conn1, _ = self._sock1.accept()
        logging.info(
            f"TCPServerWorker: connection on port {self._port1} from {self._conn1}."
        )

        self._conn2, _ = self._sock2.accept()
        logging.info(
            f"TCPServerWorker: connection on port {self._port2}  from {self._conn2}."
        )

    def closeConnection(self) -> None:
        """Close the connection."""
        self._conn1.shutdown(socket.SHUT_RDWR)
        self._conn1.close()
        self._conn2.shutdown(socket.SHUT_RDWR)
        self._conn2.close()
        self._sock1.shutdown(socket.SHUT_RDWR)
        self._sock1.close()
        self._sock2.shutdown(socket.SHUT_RDWR)
        self._sock2.close()

    @Slot(int)
    def sendMovements(self, data: int) -> None:
        """This method is called automatically when the associated signal is received, and
        it sends the new hand position using the TCP socket

        Parameters
        ----------
        data : int
            Gesture label.
        """
        self._conn1.sendall(bytes(self._gestureMap[data]))
        self._conn2.sendall(bytes(self._gestureMap[data]))


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
    _tcpServerWorker : _TCPServerWorker
        Instance of _TCPServerWorker.
    _tcpServerThread : QThread
        The QThread associated to the TCP server worker.
    """

    def __init__(
        self, address: str, port1: int, port2: int, gestureMap: dict[int, list[int]]
    ) -> None:
        super(TCPServerController, self).__init__()

        # Create worker and thread
        self._tcpServerWorker = _TCPServerWorker(address, port1, port2, gestureMap)
        self._tcpServerThread = QThread()
        self._tcpServerWorker.moveToThread(self._tcpServerThread)
        self._tcpServerThread.started.connect(self._tcpServerWorker.openConnection)
        self._tcpServerThread.finished.connect(self._tcpServerWorker.closeConnection)

    def signalConnect(self, sig: Signal) -> None:
        """Connect a given signal to the TCPServerWorker send method.

        Parameters
        ----------
        sig : Signal
            Signal to connect to the TCPServerWorker send method.
        """
        sig.connect(self._tcpServerWorker.sendMovements)

    def _startTransmission(self) -> None:
        """Start the transmission to TCP clients."""
        self._tcpServerThread.start()

    def _stopTransmission(self) -> None:
        """Stop the transmission to TCP clients."""
        self._tcpServerThread.quit()
        self._tcpServerThread.wait()
