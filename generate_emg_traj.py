"""
This module generates the force trajectories.


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
from collections import deque

import numpy as np
from scipy import signal

BAUD_RATE = 115200
BUFFER_SIZE = 1


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
        default=45454,
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
            break
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

    # Filter
    buffer = deque(maxlen=int(round(BUFFER_SIZE * fs)))
    sos = signal.butter(
        N=10,
        Wn=(20, 500),
        fs=fs,
        btype="bandpass",
        output="sos",
    )
    zi = np.zeros((sos.shape[0], 2, 64))

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
        conn.sendall(cmd)

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

            # Read data from serial port
            try:
                data = bytearray(144)
                pos = 0
                while pos < 144:
                    nRead = conn.recv_into(memoryview(data)[pos:])
                    if nRead == 0:
                        raise IncompleteReadError(bytes(data[:pos]), 144)
                    pos += nRead
            except socket.timeout:
                print("TCP communication failed.")
                return
            except IncompleteReadError as e:
                print(f"Read only {len(e.partial)} out of {e.expected} bytes.")
                return

            # Get EMG data
            emg = np.asarray(struct.unpack(">64h", data[:128]), dtype=np.int32).reshape(
                1, 64
            )

            # Convert ADC readings to mV
            mVConvF = 2.86e-4  # conversion factor
            emg = (emg * mVConvF).astype(np.float32)

            # Get AUX data
            aux = np.asarray(
                struct.unpack(">2h", data[128:132]), dtype=np.float32
            ).reshape(-1, 2)
            # Get IMU data
            imu = np.asarray(
                struct.unpack(">4h", data[132:140]), dtype=np.float32
            ).reshape(-1, 4)

            # Filter
            # emg_flt, zi = signal.sosfilt(sos, emg, axis=0, zi=zi)

            # Update buffer
            # buffer.append(emg_flt[0])

            # Compute envelope
            # env = np.sqrt(np.mean(np.asarray(buffer) ** 2, axis=0))[32:]
            # env = env.mean().item()  # average along channels

            # Send data to TCP server
            client_socket.sendall(emg.tobytes())
            client_socket.sendall(aux.tobytes())
            client_socket.sendall(imu.tobytes())

            # Send trajectory values
            # client_socket.sendall(struct.pack("<3f", env, traj_low[i], traj_high[i]))
            i += 1

            # Repeat trajectory
            if i == traj_low.size:
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
