"""
This module contains an example interface for dummy signals.


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

import time

import numpy as np

BUFF_SIZE = 50


packetSize: int = 128 * BUFF_SIZE
"""Number of bytes in each package."""

startSeq: list[bytes | float] = []
"""
Sequence of commands (as bytes) to start the device; floats are
interpreted as delays (in seconds) between commands.
"""

stopSeq: list[bytes | float] = []
"""
Sequence of commands (as bytes) to stop the device; floats are
interpreted as delays (in seconds) between commands.
"""

sigInfo: dict = {"emg": {"fs": 1000, "nCh": 64}}
"""Dictionary containing the signals information."""


def _get_channel_map(version: str = "1.0"):
    if version == "1.1":
        channel_map = (
            [44, 49, 43, 55, 39, 59, 33, 2, 32, 3, 26, 6, 22, 13, 16, 10]
            + [42, 48, 45, 54, 38, 58, 35, 0, 34, 1, 27, 7, 23, 11, 17, 12]
            + [46, 52, 40, 51, 36, 56, 31, 60, 30, 63, 25, 4, 21, 8, 18, 15]
            + [47, 50, 41, 53, 37, 57, 29, 62, 28, 61, 24, 5, 19, 9, 20, 14]
        )
    else:
        channel_map = (
            [10, 22, 12, 24, 13, 26, 7, 28, 1, 30, 59, 32, 53, 34, 48, 36]
            + [62, 16, 14, 21, 11, 27, 5, 33, 63, 39, 57, 45, 51, 44, 50, 40]
            + [8, 18, 15, 19, 9, 25, 3, 31, 61, 37, 55, 43, 49, 46, 52, 38]
            + [6, 20, 4, 17, 2, 23, 0, 29, 60, 35, 58, 41, 56, 47, 54, 42]
        )

    return channel_map


def get_offset(data, mask, match_result):
    """
    Looks for mask/template matching in data array and returns offset

    Parameters
    ----------
    data : numpy array
        1D data input.
    mask : numpy array
        1D mask to be matched.
    match_result : int
        Expected result of mask-data convolution matching.

    Returns
    -------
    int or None
        Offset if found, None otherwise.
    """
    number_of_packet = int(len(data) / 128)

    for i in range(number_of_packet):
        data_lsb = data[i * 128 : (i + 1) * 128] & np.ones(128, dtype=np.int8)
        mask_match = np.convolve(mask, np.append(data_lsb, data_lsb), "valid")
        try:
            offset = np.where(mask_match == match_result)[0][0] - 3
            return offset
        except IndexError:
            continue
    return None


def decodeFn(data: bytes) -> dict[str, np.ndarray | None]:
    """
    Function to decode the binary data received from the device into signals.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    dict of (str: ndarray or None)
        Dictionary containing the signal data packets, each with shape (nSamp, nCh);
        the keys must match with those of the "sigInfo" dictionary.
        If None is provided, the data packet is ignored.
    """
    mask = np.array([0, 2] + [0, 1] * 63)

    emg = []

    # Check call timing
    call_time = time.perf_counter()
    if hasattr(decodeFn, "time"):
        if hasattr(decodeFn, "partial_data") and call_time - decodeFn.time > 0.1:
            del decodeFn.partial_data
    decodeFn.time = time.perf_counter()

    # Handle state between calls
    if not hasattr(decodeFn, "partial_data"):  # first call
        # Compute offset
        offset = get_offset(list(data), mask, 63)
        if offset is None or offset < 0:
            return {"emg": None}

        # Discard first incomplete packet
        data = data[offset:]

        # Store partial data for next call
        decodeFn.partial_data = data[-(len(data) % 128) :]
    else:
        # Prepend partial data from previous call
        if len(decodeFn.partial_data) > 0:
            data = decodeFn.partial_data + data

        # Store new partial data for next call and remove it from current data
        decodeFn.partial_data = data[-(len(data) % 128) :]
        data = data[: -(len(data) % 128)]

    # Divide data into packets
    number_of_packet = int(len(data) / 128)
    for p in range(number_of_packet):
        data_packet = data[p * 128 : (p + 1) * 128]
        samples = [
            int.from_bytes(
                bytes([data_packet[s * 2], data_packet[s * 2 + 1]]),
                "big",
                signed=True,
            )
            for s in range(64)
        ]
        samples = np.array(samples)[
            _get_channel_map()
        ]  # sort columns so columns correspond to channels in ascending order

        emg.append(samples[np.newaxis])

    emg = np.concatenate(emg)
    emg = emg.astype(np.float32) * 0.000195  # mV

    return {"emg": emg}
