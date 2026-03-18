# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
BioGUI entry point.
"""

import argparse
import socket
import sys

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QGuiApplication

from biogui import BioGUI


class SocketListener(QObject):
    """
    Component handling remote acquisition management via a socket.

    Parameters
    ----------
    port : int
        Socket port.

    Attributes
    ----------
    _port : int
        Socket port.
    _isRunning : bool
        Whether the socket is still running.

    Class attributes
    ----------------
    startCmdRecv : Signal
        Qt Signal emitted when the socket receive a start command.
    stopCmdRecv : Signal
        Qt Signal emitted when the socket receive a stop command.
    """

    startCmdRecv = Signal()
    stopCmdRecv = Signal()

    def __init__(self, port: int, parent=None):
        super().__init__(parent)
        self._port = port
        self._isRunning = True

    def run(self):
        # Create a socket listener
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", self._port))
            s.listen()

            # Set socket to non-blocking mode
            s.settimeout(1.0)

            while self._isRunning:
                try:
                    conn, addr = s.accept()
                    logging.info(f"SocketListener: TCP connection from {addr}.")
                    with conn:
                        data = conn.recv(1024).strip()
                        if data == b"start":
                            logging.info("SocketListener: start command received.")
                            self.startCmdRecv.emit()
                        elif data == b"stop":
                            logging.info("SocketListener: stop command received.")
                            self.stopCmdRecv.emit()
                        # Close the connection
                        conn.close()
                except socket.timeout:
                    continue  # Continue listening if no connection is made
                except Exception as e:
                    logging.error(f"SocketListener: failed with exception {e}")
                    break

    def stop(self):
        self._isRunning = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log",
        action="store_true",
        help="Whether to enable logs",
    )
    parser.add_argument(
        "--rem_port",
        type=int,
        required=False,
        help="Port for remote acquisition management",
    )
    args = vars(parser.parse_args())

    # Enable logging
    if args["log"]:
        import logging

        logging.basicConfig(level=logging.INFO)

    # Disable native macOS menu
    if sys.platform == "darwin":
        QGuiApplication.setAttribute(Qt.AA_DontUseNativeMenuBar, True)  # type: ignore

    # Instantiate app
    app = BioGUI()

    if args["rem_port"]:
        # Instantiate socket listener for remote acquisition execution
        socketListener = SocketListener(args["rem_port"])
        thread = QThread(app)
        socketListener.moveToThread(thread)

        # Safe exit
        def onAppExit():
            socketListener.stop()
            thread.quit()
            thread.wait()
            socketListener.deleteLater()

        # Connect signals
        thread.started.connect(socketListener.run)
        thread.finished.connect(thread.deleteLater)
        socketListener.startCmdRecv.connect(app.mainController.startStreaming)
        socketListener.stopCmdRecv.connect(app.mainController.stopStreaming)
        app.aboutToQuit.connect(onAppExit)

        # Start the thread
        thread.start()

    sys.exit(app.exec())
