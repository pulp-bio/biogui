"""
This script generates dummy signals to test the GUI.


Copyright 2025 Mattia Orlandi, Pierangelo Maria Rapa

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

import socket
import struct
import sys
import threading
import time

import numpy as np

type Endpoint = str | tuple[str, int]


def parse_endpoint(endpoint: str) -> Endpoint:
    """
    Parse an endpoint string into a Unix socket or address:port pair.

    Arguments
    ---------
    endpoint : str
        Endpoint string, either a Unix socket path or "address:port" pair.

    Returns
    -------
    Endpoint
        Parsed endpoint.
    """
    if ":" in endpoint:
        address, port_str = endpoint.split(":")
        try:
            port = int(port_str)
        except ValueError:
            raise ValueError(f"Invalid port number: {port_str}")
        return (address, port)
    else:
        return endpoint


FS_DICT = {
    0x01: 200,
    0x02: 500,
    0x03: 1000,
}
GAIN_DICT = {
    0x00: 1,
    0x10: 2,
    0x20: 4,
    0x30: 8,
}
"""Dummy protocol: the script excepts a start command comprising:
- 1 byte: sampling frequency code for sig1;
- 1 byte: gain code for sig1;
- 1 byte: sampling frequency code for sig2;
- 1 byte: gain code for sig2;
- 1 byte: start command (b':').
The script will then generate signals accordingly.
"""


def _listen_for_stop(sock, stop_event):
    """Listen for a "stop" command from the server."""
    try:
        while not stop_event.is_set():
            cmd = sock.recv(1)
            print(f'Received "{cmd}" command from server, stopping transmission.')
            stop_event.set()
            break
    except socket.timeout:
        pass
    except Exception as e:
        sys.exit(f"Error while listening for stop command: {e}.")


def _square_chunk(n_samp: int, fs: float, gain: int, phase: float):
    phase_inc = 2 * np.pi * 5 / fs  # 5 Hz
    k = np.arange(n_samp)
    ph = (phase + phase_inc * k) % (2 * np.pi)
    samples = np.where(ph < 2 * np.pi * 0.5, gain, -gain)
    new_phase = (phase + phase_inc * n_samp) % (2 * np.pi)
    return samples, new_phase


def _sine_chunk(n_samp: int, fs: float, gain: int, phase: float):
    phase_inc = 2 * np.pi * 10 / fs  # 10 Hz
    k = np.arange(n_samp)
    ph = (phase + phase_inc * k) % (2 * np.pi)
    samples = gain * np.sin(ph)
    new_phase = (phase + phase_inc * n_samp) % (2 * np.pi)
    return samples, new_phase


def main():
    # Parse inputs
    if len(sys.argv) != 2:
        sys.exit(
            "Usage: python3 generate_dummy_signals.py ADDRESS:PORT | UNIX_SOCKET_PATH"
        )
    endpoint = parse_endpoint(sys.argv[1])

    stop_event = None
    listener_thread = None
    sock = None
    try:
        # Create socketmatch emg_endpoint:
        match endpoint:
            case str():
                if sys.platform == "win32":
                    sys.exit("Unix sockets are not supported on Windows.")

                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            case (str(), int()):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            case _:
                raise ValueError("Invalid endpoint type.")

        while True:
            try:
                sock.connect(endpoint)
                break
            except ConnectionRefusedError:
                print("Connection refused, retrying in a second...")
                time.sleep(1)
        print(f"Connected to server at {endpoint}.")

        # Wait for start command
        conf = sock.recv(2)
        fs1 = FS_DICT[struct.unpack("B", conf[0:1])[0]]
        gain1 = GAIN_DICT[struct.unpack("B", conf[1:2])[0]]
        print(f"1st signal: fs={fs1} Hz, gain={gain1}.")
        conf = sock.recv(2)
        fs2 = FS_DICT[struct.unpack("B", conf[0:1])[0]]
        gain2 = GAIN_DICT[struct.unpack("B", conf[1:2])[0]]
        print(f"2nd signal: fs={fs2} Hz, gain={gain2}.")
        cmd = sock.recv(1)
        print(f'Received "{cmd}" command from server, starting transmission.')

        # Start a thread to listen for the stop command
        sock.settimeout(0.5)
        stop_event = threading.Event()  # Event to stop the transmission
        listener_thread = threading.Thread(
            target=_listen_for_stop, args=(sock, stop_event)
        )
        listener_thread.start()

        # Start generating signals
        phase1 = 0.0
        phase2 = 0.0
        while not stop_event.is_set():
            # 1st signal: 4 channels of square wave
            data1 = []
            new_phase = phase1
            for _ in range(4):
                data_i, new_phase = _square_chunk(fs1 // 50, fs1, gain1, phase1)
                data1.append(data_i)
            phase1 = new_phase
            data1 = np.column_stack(data1).astype(np.float32)

            # 2nd signal: 2 channels of sine wave
            data2 = []
            new_phase = phase2
            for _ in range(2):
                data_i, new_phase = _sine_chunk(fs2 // 50, fs2, gain2, phase2)
                data2.append(data_i)
            phase2 = new_phase
            data2 = np.column_stack(data2).astype(np.float32)

            # Send data to TCP server
            data = np.concatenate((data1.flatten(), data2.flatten()))
            sock.sendall(data.tobytes())

            # Emulate acquisition
            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\nExiting program...")
    except Exception as e:
        print(f"An error occurred: {e}.")
    finally:
        if stop_event is not None:
            # Wait for the listener thread to finish
            if not stop_event.is_set():
                stop_event.set()
        if listener_thread is not None:
            listener_thread.join()

        # Close socket
        if sock is not None:
            sock.close()
            print("Socket closed.")


if __name__ == "__main__":
    main()
