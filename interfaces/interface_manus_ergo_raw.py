"""
This module contains the Manus interface to retrieve
both ergonomics and raw data from MANUS gloves.


Copyright 2024 Mattia Orlandi, Pierangelo Maria Rapa

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

import struct

import numpy as np

packetSize: int = 128
"""Number of bytes in each packet (all data transmitted as floats)."""

startSeq: list[bytes] = []
"""Sequence of commands to start the device."""

stopSeq: list[bytes] = [b"S"]
"""Sequence of commands to stop the device."""

sigInfo: dict = {"manusData": {"fs": 120, "nCh": 24}, "manusTs": {"fs": 120, "nCh": 1}}
"""Dictionary containing the signals information."""


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """
    Function to decode the binary data received from the device into signals.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    dict of (str: ndarray)
        Dictionary containing the signal data packets, each with shape (nSamp, nCh);
        the keys must match with those of the "sigInfo" dictionary.
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

    return {"manusData": manusData, "manusTs": manusTs}
