"""
This module reads IMU data from the GAPWatch, translates it into an angle, and generates the angle trajectories.


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
        "--n_reps",
        type=int,
        required=True,
        help="Number of repetitions",
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
    n_reps = args["n_reps"]
    recv_port = args["recv_port"]
    server_addr = args["server_addr"]
    server_port = args["server_port"]

    return max_angle, slope, fs, gap_width, n_reps, recv_port, server_addr, server_port


def _gen_trajectories(
    max_val, slope, fs, gap_width, rest_duration_s, plateau_duration_s
) -> tuple[np.ndarray, np.ndarray]:
    """Generate trapezoidal trajectories."""
    ramp_duration_s = max_val / slope
    rest_duration = int(round(rest_duration_s * fs))
    plateau_duration = int(round(plateau_duration_s * fs))
    ramp_duration = int(round(ramp_duration_s * fs))

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


def _listen_for_stop(client_socket, conn, stop_event):
    """Listen for a "stop" command from the server."""
    try:
        while not stop_event.is_set():
            cmd = client_socket.recv(2)
            print(f'Received "{cmd}" command from server. Stopping transmission.')
            stop_event.set()
            conn.sendall(cmd)
    except Exception as e:
        print(f"Error while listening for stop command: {e}")


def _compute_bend_angle(g_neutral, g_bent):
    """Compute the bend angle from the IMU data given a neutral position."""
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


def _pad_with_last_value(arr, target_size):
    """Pad a 1D NumPy array to a given size by repeating the last value."""
    if len(arr) >= target_size:
        return arr[:target_size]  # Truncate if the array is already larger or equal.

    pad_size = target_size - len(arr)
    padding = np.full(pad_size, arr[-1])

    return np.concatenate((arr, padding)).astype(arr.dtype)


def main():
    # Input arguments
    max_angle, slope, fs, gap_width, n_reps, recv_port, server_addr, server_port = (
        _parse_input()
    )

    # Trapezoidal trajectories
    traj_low, traj_high = _gen_trajectories(
        max_angle, slope, fs, gap_width, rest_duration_s=0.5, plateau_duration_s=1
    )
    practice_duration_s = 10
    practice_duration = int(round(practice_duration_s * fs))
    traj_low = np.concatenate(
        [np.ones(practice_duration, dtype=np.float32) * traj_low[0], traj_low]
    )
    traj_high = np.concatenate(
        [np.ones(practice_duration, dtype=np.float32) * traj_high[0], traj_high]
    )

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
        conn.sendall(cmd)

        # Start a thread to listen for the stop command
        stop_event = threading.Event()  # Event to stop the transmission
        listener_thread = threading.Thread(
            target=_listen_for_stop, args=(client_socket, conn, stop_event)
        )
        listener_thread.start()

        calib_time_s = 5.0
        calib_time = int(round(calib_time_s * fs))
        calib_complete = False
        neutral_angle = 0
        rep_counter = 0
        i = 0
        while True:
            if stop_event.is_set():
                break  # Stop sending if stop event is triggered

            # Read data from server socket
            data = _read_tcp(conn, PACKET_SIZE)
            if data is None:
                break

            # Get IMU data
            imu = _decodeFn(data)
            n_samp = imu.shape[0]
            angle = np.zeros(n_samp, dtype=np.float32)
            i += n_samp
            if not calib_complete:
                neutral_angle += imu.sum(axis=0)
                cur_traj_low = np.zeros(n_samp, dtype=np.float32)
                cur_traj_high = np.zeros(n_samp, dtype=np.float32)

                if i >= calib_time:
                    neutral_angle /= i
                    i = 0
                    calib_complete = True
                    print(f"Calibration done: neutral position = {neutral_angle}")
            else:
                for k in range(n_samp):
                    angle[k] = _compute_bend_angle(neutral_angle, imu[k])

                cur_traj_low = _pad_with_last_value(traj_low[i - n_samp : i], n_samp)
                cur_traj_high = _pad_with_last_value(traj_high[i - n_samp : i], n_samp)

                # Repeat trajectory
                if i >= traj_low.size:
                    print(f"{rep_counter} -> {rep_counter + 1}")
                    rep_counter += 1
                    i = practice_duration

            # Send data to TCP server
            client_socket.sendall(imu.tobytes())
            client_socket.sendall(angle.tobytes())
            client_socket.sendall(cur_traj_low.tobytes())
            client_socket.sendall(cur_traj_high.tobytes())

            if rep_counter == n_reps:
                print("Experiment ended.")
                break

        if not stop_event.is_set():
            stop_event.set()
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
