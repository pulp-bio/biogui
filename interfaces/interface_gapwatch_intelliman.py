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
from datetime import datetime

BUFF_SIZE = 1

packetSize: int = (252) * BUFF_SIZE
"""Number of bytes in each package."""

startSeq: list[bytes] = [b"="]
"""Sequence of commands to start the device."""

stopSeq: list[bytes] = [b":"]
"""Sequence of commands to stop the device."""

sigInfo: dict = {
    "emg": {"fs": 2000, "nCh": 16},
    "battery": {"fs": 400, "nCh": 1},
    "counter": {"fs": 400, "nCh": 1},
    "ts": {"fs": 400, "nCh": 1},
}
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
    nSampEMG, nChEMG = 5 * BUFF_SIZE, sigInfo["emg"]["nCh"]
    nSampBat = nSampCounter = nSampTs = 1 * BUFF_SIZE

    # ADC parameters
    vRef = 4
    gain = 6
    nBit = 24

    dataEMG = bytearray()
    dataBat = bytearray()
    dataCounter = bytearray()
    dataTs = bytearray()
    for i in range(BUFF_SIZE):
        dataEMG.extend(bytearray(data[i * 252 : i * 252 + 240]))
        dataBat.extend(bytearray(data[i * 252 + 240 : i * 252 + 241]))
        dataCounter.extend(bytearray(data[i * 252 + 241 : i * 252 + 243]))
        dataTs.extend(bytearray(data[i * 252 + 244 : i * 252 + 252]))

    # Convert 24-bit to 32-bit integer
    pos = 0
    for _ in range(len(dataEMG) // 3):
        prefix = 255 if dataEMG[pos] > 127 else 0
        dataEMG.insert(pos, prefix)
        pos += 4
    emgADC = np.asarray(
        struct.unpack(f">{nSampEMG * nChEMG}i", dataEMG), dtype=np.int32
    ).reshape(nSampEMG, nChEMG)

    # ADC readings to mV
    emg = emgADC * vRef / (gain * (2 ** (nBit - 1) - 1))  # V
    emg *= 1_000  # mV
    emg = emg.astype(np.float32)

    # Read battery and packet counter
    battery = np.asarray(
        struct.unpack(f"<{nSampBat}B", dataBat), dtype=np.float32
    ).reshape(nSampBat, 1)
    counter = np.asarray(
        struct.unpack(f">{nSampCounter}H", dataCounter), dtype=np.float32
    ).reshape(nSampCounter, 1)
    ts = np.asarray(
        struct.unpack(f"<{nSampTs}Q", dataTs), dtype=np.uint64
    ).reshape(nSampTs, 1)

    return {"emg": emg, "battery": battery, "counter": counter, "ts": ts}
