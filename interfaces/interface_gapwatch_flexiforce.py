"""
This module contains the GAPWatch interface for sEMG.


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

import struct

import numpy as np

packetSize: int = 720
"""Number of bytes in each package."""

startSeq: list[bytes] = []
"""Sequence of commands to start the device."""

stopSeq: list[bytes] = []
"""Sequence of commands to stop the device."""

sigInfo: dict = {"force": {"fs": 4000, "nCh": 3}}
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

    return {"force": force[:, [8, 9, 10]]}