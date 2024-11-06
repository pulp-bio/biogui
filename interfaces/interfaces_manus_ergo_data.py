"""
This module contains the Manus interface to retrieve ergonomics data.


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
from collections import namedtuple

import numpy as np

packetSize: int = 96
"""Number of bytes in each packet (all data transmitted as floats)."""

startSeq: list[bytes] = [b"A"]
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = []
"""Sequence of commands to stop the board."""

fs: list[float] = [120]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [22]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "manusErgo")
"""Named tuple containing the Manus data packet."""


def decodeFn(data: bytes) -> SigsPacket:
    """
    Function to decode the binary data received from Manus.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    SigsPacket
        Named tuple containing the Manus data packet with shape (nSamp, nCh).
    """
    # 24 floats:
    # -  1 for startId
    # - 20 for angles
    # -  2 for timestamp (double)
    # -  1 for stopId

    ergoData = np.zeros(shape=(1, 22), dtype=np.float32)

    # Read the 20 angles [4:84]
    ergoData[0, :20] = np.asarray(struct.unpack("<20f", data[4:84]), dtype=np.float32)

    # Read timestamp as two separate floats [84:92]
    ergoData[0, 20:] = np.asarray(struct.unpack("<2f", data[84:92]), dtype=np.float32)

    return SigsPacket(manusErgo=ergoData)
