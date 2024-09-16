"""
This module contains the BioGAP interface for sEMG.


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

packetSize: int = 234
"""Number of bytes in each package."""

startSeq: list[bytes] = [
    bytes([20, 1, 50]),
    (18).to_bytes(),
    bytes([6, 0, 1, 4, 0, 13, 10]),
]
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = [(19).to_bytes()]
"""Sequence of commands to stop the board."""

fs: list[float] = [500, 500]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [8, 1]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "emg triggerWulpus")
"""Named tuple containing the EMG packet."""


def decodeFn(data: bytes) -> SigsPacket:
    """
    Function to decode the binary data received from BioGAP into a single sEMG signal.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    SigsPacket
        Named tuple containing the EMG packet with shape (nSamp, nCh).
    """
    nSamp = 7

    # ADC parameters
    vRef = 4
    gain = 6.0
    nBit = 24

    dataEmgTmp = bytearray(
        data[2:26] #sample 1; ch 1-8; 3 bytes per channel.
        + data[34:58]
        + data[66:90]
        + data[98:122]
        + data[130:154]
        + data[162:186]
        + data[194:218]
    )

    dataTriggerTmp = bytearray(
        data[33:34]
        + data[65:66]
        + data[97:98]
        + data[129:130]
        + data[161:162]
        + data[193:194]
        + data[225:226]
    )

    # Convert 24-bit to 32-bit integer
    pos = 0
    for _ in range(len(dataEmgTmp) // 3):
        prefix = 255 if dataEmgTmp[pos] > 127 else 0
        dataEmgTmp.insert(pos, prefix)
        pos += 4
    emg = np.asarray(struct.unpack(f">{nSamp * 8}i", dataEmgTmp), dtype=np.int32)
    
    triggerWulpusTemp = bytearray()
    for data in dataTriggerTmp:
        triggerWulpusTemp.append(data & 0x0F)
    triggerWulpus = np.asarray(struct.unpack(f"<{nSamp}B", triggerWulpusTemp), dtype=np.int32)

    # Reshape and convert ADC readings to uV
    emg = emg.reshape(nSamp, 8)
    emg = emg * (vRef / gain / 2**nBit)  # V
    emg *= 1_000_000  # uV
    emg = emg.astype(np.float32)

    return SigsPacket(emg=emg, triggerWulpus=triggerWulpus.reshape(nSamp, 1))
