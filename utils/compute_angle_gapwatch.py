"""
This module reads IMU data from the GAPWatch and translates it into an angle.


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

import argparse
import socket
import struct
import threading
import time
from asyncio import IncompleteReadError

import numpy as np

PACKET_SIZE = 720


def _decodeFn(data: bytes) -> np.ndarray:
    """
    Function to decode the binary data received from the device into signals.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    ndarray
        Signal with shape (nSamp, nCh).
    """
    imuTmp = bytes(data[:6] + data[240:246] + data[480:486])
    imu = np.asarray(struct.unpack("<9h", imuTmp), dtype=np.float32).reshape(3, 3)
    imu *= 0.061

    return imu


def _parse_input() -> tuple:
    """Parse the input arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fs",
        type=int,
        required=True,
        help="Frequency of the force signal",
    )
    parser.add_argument(
        "--recv_port",
        default=3333,
        type=int,
        required=False,
        help="Receiving port for the force data",
    )
    parser.add_argument(
        "--server_addr",
        default="127.0.0.1",
        type=str,
        required=False,
        help="Server address of the TCP socket",
    )
    parser.add_argument(
        "--server_port",
        default=3334,
        type=int,
        required=False,
        help="Port of the TCP socket",
    )
    args = vars(parser.parse_args())

    fs = args["fs"]
    recv_port = args["recv_port"]
    server_addr = args["server_addr"]
    server_port = args["server_port"]

    return fs, recv_port, server_addr, server_port


def _compute_bend_angle(g_neutral, g_bent):
    # Compute the dot product
    dot_product = np.dot(g_neutral, g_bent)

    # Compute the magnitudes of the vectors
    magnitude_neutral = np.linalg.norm(g_neutral)
    magnitude_bent = np.linalg.norm(g_bent)

    # Calculate the cosine of the angle
    cos_theta = dot_product / (magnitude_neutral * magnitude_bent)

    # Compute the angle in radians and convert to degrees
    theta = np.arccos(np.clip(cos_theta, -1.0, 1.0))  # Clip for numerical stability
    theta_degrees = np.degrees(theta)

    return theta_degrees


def _listen_for_stop(client_socket, stop_event):
    """Listen for a "stop" command from the server."""
    try:
        while not stop_event.is_set():
            cmd = client_socket.recv(2)
            print(f'Received "{cmd}" command from server. Stopping transmission.')
            stop_event.set()
    except Exception as e:
        print(f"Error while listening for stop command: {e}")


def main():
    # Input arguments
    fs, recv_port, server_addr, server_port = _parse_input()

    try:
        # Create TCP server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", recv_port))
        server_socket.listen()
        print(f"Waiting for TCP connection on port {recv_port}...")

        conn, (addr, _) = server_socket.accept()
        print(f"Connection from {addr}")

        # Create TCP client socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                client_socket.connect((server_addr, server_port))
                break
            except ConnectionRefusedError:
                print("Connection refused, retrying in a second...")
                time.sleep(1)
        print(f"Connected to server at {server_addr}:{server_port}")

        # Wait for start command
        cmd = client_socket.recv(2)
        print(f'Received "{cmd}" command from server. Starting transmission.')
        # conn.sendall(cmd)

        # Start a thread to listen for the stop command
        stop_event = threading.Event()  # Event to stop the transmission
        listener_thread = threading.Thread(
            target=_listen_for_stop, args=(client_socket, stop_event)
        )
        listener_thread.start()

        i = 0
        calib_complete = False
        neutral_angle = 0
        while True:
            if stop_event.is_set():
                break  # Stop sending if stop event is triggered

            # Read data from server socket
            try:
                data = bytearray(PACKET_SIZE)
                pos = 0
                while pos < PACKET_SIZE:
                    nRead = conn.recv_into(memoryview(data)[pos:])
                    if nRead == 0:
                        raise IncompleteReadError(bytes(data[:pos]), PACKET_SIZE)
                    pos += nRead
            except socket.timeout:
                print("TCP communication failed.")
                return
            except IncompleteReadError as e:
                print(f"Read only {len(e.partial)} out of {e.expected} bytes.")
                return

            # Get IMU data
            imu = _decodeFn(data)
            n_samp = imu.shape[0]
            angle = np.zeros(shape=n_samp, dtype=np.float32)
            i += n_samp
            if i < 5 * fs:  # 2-seconds calibration
                neutral_angle += imu.sum(axis=0)
            else:
                if not calib_complete:
                    neutral_angle /= i
                    calib_complete = True
                    print(f"Calibration done (i = {i})")
                for k in range(n_samp):
                    angle[k] = _compute_bend_angle(neutral_angle, imu[k])

            # Send data to TCP server
            client_socket.sendall(imu.tobytes())
            client_socket.sendall(angle.tobytes())

        # Wait for the listener thread to finish
        listener_thread.join()
        print("Stopped by server.")
    except KeyboardInterrupt:
        print("\nExiting program...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close resources
        client_socket.close()
        print("Client socket closed.")
        if "server_socket" in locals():
            server_socket.close()
            print("Server socket closed.")


if __name__ == "__main__":
    main()
