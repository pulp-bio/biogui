"""This module contains the decode function for sEMG from BioGAP.


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

PACKET_SIZE: int = 234
"""Number of bytes in each package."""


startSeq: list[bytes] = [
    bytes([20, 1, 50]),
    (18).to_bytes(),
    bytes([6, 0, 1, 4, 0, 13, 10]),
]
"""Sequence of commands to start the board."""


stopSeq: list[bytes] = [(19).to_bytes()]
"""Sequence of commands to stop the board."""


SigsPacket = namedtuple("SigsPacket", "emg")
"""Named tuple containing the EMG packet."""


def decodeFn(data: bytes) -> SigsPacket:
    """Function to decode the binary data received from BioGAP into a single sEMG signal.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    SigsPacket
        Named tuple containing the EMG packet with shape (nSamp, nCh).
    """
    # PACKET SIZE: 234

    nSamp = 7
    nCh = 8

    # ADC parameters
    vRef = 2.5
    gain = 6.0
    nBit = 24

    dataTmp = bytearray(
        data[2:26]
        + data[34:58]
        + data[66:90]
        + data[98:122]
        + data[130:154]
        + data[162:186]
        + data[194:218]
    )
    # Convert 24-bit to 32-bit integer
    pos = 0
    for _ in range(len(dataTmp) // 3):
        prefix = 255 if dataTmp[pos] > 127 else 0
        dataTmp.insert(pos, prefix)
        pos += 4
    emg = np.asarray(struct.unpack(f">{nSamp * nCh}i", dataTmp), dtype="int32")

    # Reshape and convert ADC readings to uV
    emg = emg.reshape(nSamp, nCh)
    emg = emg * (vRef / gain / 2**nBit)  # V
    emg *= 1_000_000  # uV
    emg = emg.astype("float32")

    return SigsPacket(emg=emg)
