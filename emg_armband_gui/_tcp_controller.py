"""Class implementing the ESB acquisition controller.


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

import socket

import numpy as np
from PySide6.QtCore import QObject, QThread, Signal, Slot

from ._svm_controller import SVMController


class _TcpServerWorker(QObject):
    """Worker that create two tcp socket to control the virtual hands in simulink

    Parameters
    ----------
    address : str
        Server address
    port1 : str
        port for the first socket connected to the virtual hand
    port2 : str
        port for the second socket connected to the target hand

    Attributes
    ----------

    """

    def __init__(self, address: str, port1: int, port2: int) -> None:
        super(_TcpServerWorker, self).__init__()
        self.sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock1.bind((address, port1))
        self.sock1.listen(1)

        self.sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock2.bind((address, port2))
        self.sock2.listen(1)
        self._movements = {
            "rest": [0, 0, 45, 0, 90, 90, 0, 90, 90, 0, 90, 90, 0, 0, 0],
            "open hand": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "fist (power grip)": [
                90,
                0,
                90,
                0,
                90,
                90,
                0,
                90,
                90,
                0,
                90,
                90,
                0,
                90,
                90,
            ],
            "index pointed": [90, 0, 90, 0, 0, 0, 0, 90, 90, 0, 90, 90, 0, 90, 90],
            "ok (thumb up)": [0, 0, 20, 0, 90, 90, 0, 90, 90, 0, 90, 90, 0, 90, 90],
            "right flexion (wrist supination)": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            "left flexion (wristpronation)": [
                0,
                0,
                0,
                0,
                10,
                10,
                0,
                10,
                10,
                0,
                10,
                10,
                10,
                10,
                0,
            ],
            "horns": [90, 0, 90, 0, 0, 0, 0, 90, 90, 0, 90, 90, 0, 0, 0],
            "shaka": [0, 0, 45, 0, 90, 90, 0, 90, 90, 0, 90, 90, 0, 0, 0],
        }

    def accept_connection(self):
        self.client1_connection, _ = self.sock1.accept()
        print("Connected from", self.client1_connection)
        self.client2_connection, _ = self.sock2.accept()

    @Slot(int)
    def send_movements1(self, data: int) -> None:
        """This method is called automatically when the associated signal is received, and
        it sends the new hand position using the TCP socket

        Parameters
        ----------
        data : bytearray
            New binary data.
        """
        self.client1_connection.sendall(bytes(list(self._movements.values())[data]))
        self.client2_connection.sendall(bytes(list(self._movements.values())[data]))


class TcpServerController(QObject):
    """Controller for the TCP servers

    Parameters
        ----------
        address : str
            Server address
        port1 : str
            port for the first socket connected to the virtual hand
        port2 : str
            port for the second socket connected to the target hand

        Attributes
        ----------
        data_worker : _DataWorker
            Worker for generating data.
        data_thread : QThread
            QThread associated to the data worker.
    """

    def __init__(
        self, address: str, port1: int, port2: int, svmController: SVMController
    ) -> None:
        super(TcpServerController, self).__init__()

        # Create worker and thread
        self._tcp_worker = _TcpServerWorker(address, port1, port2)
        self._tcp_thread = QThread()
        self._tcp_worker.moveToThread(self._tcp_thread)
        self._tcp_thread.started.connect(self._tcp_worker.accept_connection)
        # Connect to svm controller
        self._svmController = svmController
        self._svmController._SVMWorker.inferenceSig.connect(
            self._tcp_worker.send_movements1
        )

        self._tcp_thread.start()
        # # Connect to acquisition controller
        # self._acq_controller = acq_controller
        # self._acq_controller.connect_data_ready(self._file_worker.write)
        # self._file_thread.start()
