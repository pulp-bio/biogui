"""
This module reads data from the EMaGer, generates the RMS trajectories,
and appends them to the EMG data.


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

N_CH = 64
WIN_SIZE = 100


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
        help="Target percentage of MVC",
    )
    parser.add_argument(
        "-s",
        "--slope",
        type=int,
        required=True,
        help="Slope of the ramps (in MVC percentage over seconds)",
    )
    parser.add_argument(
        "--gap_width",
        type=int,
        required=True,
        help="Width of the gap (in MVC percentage) between the two trajectories",
    )
    args = vars(parser.parse_args())

    mvc = args["mvc"]
    p_mvc = args["p_mvc"]
    slope = args["slope"]
    gap_width = args["gap_width"]

    return mvc, p_mvc, slope, gap_width


def _gen_trajectories(
    p_mvc, slope, fs, gap_width, rest_duration_s, plateau_duration_s
) -> tuple[np.ndarray, np.ndarray]:
    """Generate trapezoidal trajectories."""
    ramp_duration_s = p_mvc / slope
    rest_duration = int(round(rest_duration_s * fs))
    plateau_duration = int(round(plateau_duration_s * fs))
    ramp_duration = int(round(ramp_duration_s * fs))

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


def _read_tcp(conn: socket.socket, packet_size: int) -> bytearray | None:
    """Read data from a TCP client socket."""
    try:
        data = bytearray(packet_size)
        pos = 0
        while pos < packet_size:
            nRead = conn.recv_into(memoryview(data)[pos:])
            if nRead == 0:
                raise IncompleteReadError(bytes(data[:pos]), packet_size)
            pos += nRead
        return data
    except socket.timeout:
        print("TCP communication failed.")
        return
    except IncompleteReadError as e:
        print(f"Read only {len(e.partial)} out of {e.expected} bytes.")
        return


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
    mvc, p_mvc, slope, gap_width = _parse_input()

    # Trapezoidal trajectories
    trap_fs = 1000 // WIN_SIZE  # Hz
    traj_low, traj_high = _gen_trajectories(
        p_mvc, slope, trap_fs, gap_width, rest_duration_s=5, plateau_duration_s=20
    )
    traj_low = traj_low * mvc / 100
    traj_high = traj_high * mvc / 100

    try:
        # Create TCP server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", 3333))
        server_socket.listen()
        print("Waiting for TCP connection on port 3333...")

        conn, (addr, _) = server_socket.accept()

        # Create TCP client socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                client_socket.connect(("127.0.0.1", 3334))
                break
            except ConnectionRefusedError:
                print("Connection refused, retrying in a second...")
                time.sleep(1)
        print("Connected to server at 127.0.0.1:3334")

        # Wait for start command
        # cmd = client_socket.recv(2)
        # print(f'Received "{cmd}" command from server. Starting transmission.')
        # conn.sendall(cmd)

        # Start a thread to listen for the stop command
        # stop_event = threading.Event()  # Event to stop the transmission
        # listener_thread = threading.Thread(
        #     target=_listen_for_stop, args=(client_socket, stop_event)
        # )
        # listener_thread.start()

        i = 0
        while True:
            # if stop_event.is_set():
            #     break  # Stop sending if stop event is triggered

            # Read data from server socket
            data = _read_tcp(conn, N_CH * WIN_SIZE * 4)
            if data is None:
                break

            # Get EMG data
            emg = np.asarray(
                struct.unpack(f"<{N_CH * WIN_SIZE}f", data), dtype=np.float32
            ).reshape(WIN_SIZE, N_CH)
            print(f"EMG data shape: {emg.shape}")

            # Compute RMS
            emg_rms = np.sqrt(np.mean(emg**2, axis=0)).sum() - 2

            # Send data to TCP server
            client_socket.sendall(emg_rms.tobytes())
            client_socket.sendall(traj_low[i : i + 1].tobytes())
            client_socket.sendall(traj_high[i : i + 1].tobytes())
            i += 1

            # Repeat trajectory
            if i >= traj_low.size:
                i = 0

        # Wait for the listener thread to finish
        # listener_thread.join()
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
