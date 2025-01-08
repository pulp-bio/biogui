"""
This module reads data from the GAPWatch, generates the force trajectories
and append them to the FlexiForce data.


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
    nSamp = 15

    # ADC parameters
    vRef = 4
    gain = 1
    nBit = 24

    dataTmp = bytearray(data)
    # Convert 24-bit to 32-bit integer
    pos = 0
    for _ in range(len(dataTmp) // 3):
        prefix = 255 if dataTmp[pos] > 127 else 0
        dataTmp.insert(pos, prefix)
        pos += 4
    forceAdc = np.asarray(
        struct.unpack(f">{nSamp * 16}i", dataTmp), dtype=np.int32
    ).reshape(nSamp, 16)

    # ADC readings to mV
    force = forceAdc * vRef / (gain * (2 ** (nBit - 1) - 1))  # V
    force *= 1_000  # mV
    force = force.astype(np.float32)

    return force[:, [8, 9, 10]]


def _parse_input() -> tuple:
    """Parse the input arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mvc",
        type=float,
        required=True,
        help="Value of the MVC",
    )
    parser.add_argument(
        "--p_mvc",
        type=int,
        required=True,
        help="Value of the MVC (in %)",
    )
    parser.add_argument(
        "-s",
        "--slope",
        type=int,
        required=True,
        help="Slope of the ramps (in %MVC/s)",
    )
    parser.add_argument(
        "--fs",
        type=int,
        required=True,
        help="Frequency of the force signal",
    )
    parser.add_argument(
        "--gap_width",
        type=int,
        required=True,
        help="Width of the gap (in %MVC) between the two trajectories",
    )
    parser.add_argument(
        "--emg_port",
        default=3333,
        type=int,
        required=False,
        help="Receiving port for EMG data",
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

    mvc = args["mvc"]
    p_mvc = args["p_mvc"]
    slope = args["slope"]
    fs = args["fs"]
    gap_width = args["gap_width"]
    emg_port = args["emg_port"]
    server_addr = args["server_addr"]
    server_port = args["server_port"]

    return mvc, p_mvc, slope, fs, gap_width, emg_port, server_addr, server_port


def _gen_trajectories(
    p_mvc, slope, fs, gap_width, rest_duration_s, plateau_duration_s
) -> tuple[np.ndarray, np.ndarray]:
    """Generate trapezoidal trajectories."""
    ramp_duration_s = p_mvc / slope
    rest_duration = rest_duration_s * fs
    plateau_duration = plateau_duration_s * fs
    ramp_duration = ramp_duration_s * fs

    # Create trajectories
    t_ramp = np.arange(ramp_duration) / fs
    rest = np.zeros(rest_duration)
    ramp_up = slope * t_ramp
    plateau = np.ones(plateau_duration) * p_mvc
    ramp_down = p_mvc - slope * t_ramp
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
    mvc, p_mvc, slope, fs, gap_width, emg_port, server_addr, server_port = (
        _parse_input()
    )

    # Trapezoidal trajectories
    traj_low, traj_high = _gen_trajectories(
        p_mvc, slope, fs, gap_width, rest_duration_s=5, plateau_duration_s=20
    )
    traj_low = traj_low * mvc / 100
    traj_high = traj_high * mvc / 100

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
        server_socket.bind(("", emg_port))
        server_socket.listen()
        print(f"Waiting for TCP connection on port {emg_port}...")

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
            force = _decodeFn(data)
            avg_force = force.mean(axis=0).mean().item()

            # Send data to TCP server
            client_socket.sendall(struct.pack("<f", avg_force))
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
