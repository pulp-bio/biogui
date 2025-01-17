"""
This module reads data from MANUS gloves, generates the angle trajectories
and append them to the joints data.


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

PACKET_SIZE = 128


def _decodeFn(data: bytes) -> tuple[np.ndarray]:
    """
    Function to decode the binary data received from the device into signals.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    tuple of ndarrays
        Signal data packets, each with shape (nSamp, nCh).
    """
    # 35 floats:
    # - 20 for angles
    # -  1 for nodeId
    # -  3 for position
    # -  4 for quaternion
    # -  3 for scale
    # -  1 for timestamp

    manusData = np.zeros(shape=(1, 24), dtype=np.float32)

    # Read the 20 angles [0:80]
    manusData[0, :20] = np.asarray(struct.unpack("<20f", data[:80]), dtype=np.float32)

    # Read the quaternions [96:112]
    manusData[0, 20:24] = np.asarray(
        struct.unpack("<4f", data[96:112]), dtype=np.float32
    )

    # Read timestamp [124:128]
    manusTs = np.asarray(struct.unpack("<f", data[124:]), dtype=np.float32).reshape(
        1, 1
    )

    return manusData, manusTs


def _parse_input() -> tuple:
    """Parse the input arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max_angle",
        type=int,
        required=True,
        help="Maximum angle (in °)",
    )
    parser.add_argument(
        "-s",
        "--slope",
        type=int,
        required=True,
        help="Slope of the ramps (in °/s)",
    )
    parser.add_argument(
        "--fs",
        type=int,
        required=True,
        help="Frequency of the signal",
    )
    parser.add_argument(
        "--gap_width",
        type=int,
        required=True,
        help="Width of the gap (in °) between the two trajectories",
    )
    parser.add_argument(
        "--recv_port",
        default=3333,
        type=int,
        required=False,
        help="Receiving port for joint data",
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

    max_angle = args["max_angle"]
    slope = args["slope"]
    fs = args["fs"]
    gap_width = args["gap_width"]
    recv_port = args["recv_port"]
    server_addr = args["server_addr"]
    server_port = args["server_port"]

    return max_angle, slope, fs, gap_width, recv_port, server_addr, server_port


def _gen_trajectories(
    max_val, slope, fs, gap_width, rest_duration_s, plateau_duration_s
) -> tuple[np.ndarray, np.ndarray]:
    """Generate trapezoidal trajectories."""
    ramp_duration_s = max_val / slope
    rest_duration = rest_duration_s * fs
    plateau_duration = plateau_duration_s * fs
    ramp_duration = ramp_duration_s * fs

    # Create trajectories
    t_ramp = np.arange(ramp_duration) / fs
    rest = np.zeros(rest_duration)
    ramp_up = slope * t_ramp
    plateau = np.ones(plateau_duration) * max_val
    ramp_down = max_val - slope * t_ramp
    traj = np.concatenate([rest, ramp_up, plateau, ramp_down, rest])
    traj_low = traj - gap_width
    traj_high = traj + gap_width
    traj_low = traj_low.astype(np.float32)
    traj_high = traj_high.astype(np.float32)

    return traj_low, traj_high


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
    max_angle, slope, fs, gap_width, recv_port, server_addr, server_port = (
        _parse_input()
    )

    # Trapezoidal trajectories
    traj_low, traj_high = _gen_trajectories(
        max_angle, slope, fs, gap_width, rest_duration_s=2, plateau_duration_s=4
    )

    try:
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

        # Create TCP server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", recv_port))
        server_socket.listen()
        print(f"Waiting for TCP connection on port {recv_port}...")

        conn, (addr, _) = server_socket.accept()
        print(f"Connection from {addr}")

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

            # Get force data
            manus_data, _ = _decodeFn(data)
            avg_mcp = manus_data[:, [5, 9, 13]].mean().item()
            # avg_mcp = manus_data[:, 9].item()

            # Send data to TCP server
            client_socket.sendall(struct.pack("<f", avg_mcp))
            client_socket.sendall(struct.pack("<f", traj_low[i]))
            client_socket.sendall(struct.pack("<f", traj_high[i]))
            i += 1

            # Repeat trajectory
            if i >= traj_low.size:
                i = 0

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
