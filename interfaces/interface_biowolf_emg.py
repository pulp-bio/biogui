"""This module contains the BioWolf interface for sEMG.


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
from collections import namedtuple

import numpy as np

packetSize: int = 486
"""Number of bytes in each package."""

startSeq: list[bytes] = [b"="]
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = [b":"]
"""Sequence of commands to stop the board."""

fs: list[float] = [4000]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [16]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "emg")
"""Named tuple containing the EMG packet."""


def decodeFn(data: bytes) -> SigsPacket:
    """Function to decode the binary data received from BioWolf into a single sEMG signal.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    SigsPacket
        Named tuple containing the EMG packet with shape (nSamp, nCh).
    """
    nSamp = 5  # additional buffering of 2

    # ADC parameters
    vRef = 2.5
    gain = 6.0
    nBit = 24

    emg = np.zeros(shape=(0, 16), dtype=np.float32)

    for i in range(2):
        dataTmp = bytearray(data)[i * 243 + 2 : (i + 1) * 243 - 1]

        # Convert 24-bit to 32-bit integer
        pos = 0
        for _ in range(len(dataTmp) // 3):
            prefix = 255 if dataTmp[pos] > 127 else 0
            dataTmp.insert(pos, prefix)
            pos += 4
        emgTmp = np.asarray(struct.unpack(f">{nSamp * 16}i", dataTmp), dtype=np.int32)
        emg = np.concatenate([emg, emgTmp.reshape(nSamp, 16)])

    # Convert ADC readings to uV
    emg = emg * (vRef / gain / 2**nBit)  # V
    emg *= 1_000_000  # uV
    emg = emg.astype(np.float32)

    return SigsPacket(emg=emg)
