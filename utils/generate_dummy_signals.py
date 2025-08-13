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
import sys
import threading
import time

import numpy as np


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


def main():
    # Parse inputs
    if len(sys.argv) not in (2, 3):
        sys.exit("Usage: python3 generate_dummy_signals.py [ADDRESS] PORT")

    if len(sys.argv) == 2:
        addr = "127.0.0.1"
    else:
        addr = sys.argv[1]
    try:
        port = int(sys.argv[-1])
    except ValueError:
        sys.exit("Port is not an integer.")

    stop_event = None
    listener_thread = None
    sock = None
    try:
        # Create TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                sock.connect((addr, port))
                break
            except ConnectionRefusedError:
                print("Connection refused, retrying in a second...")
                time.sleep(1)
        print(f"Connected to server at {addr}:{port}.")

        # Wait for start command
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
        prng = np.random.default_rng(seed=42)
        mean = 0.0
        while not stop_event.is_set():
            # 1st signal: 4 channels, 10 samples, 128sps
            data1 = prng.normal(loc=mean, scale=100.0, size=(10, 4)).astype(np.float32)
            # 2nd signal: 2 channel, 4 samples, 51.2sps
            data2 = prng.normal(loc=mean, scale=100.0, size=(4, 2)).astype(np.float32)

            # Send data to TCP server
            data = np.concatenate((data1.flatten(), data2.flatten()))
            sock.sendall(data.tobytes())

            # Update mean
            mean += prng.normal(scale=50.0)

            # Fastest signal: 128 sps, 10 samples generated at once
            # -> set timer interval corresponding to one tenth of 128 sps, i.e., 78 ms
            time.sleep(0.078)

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
