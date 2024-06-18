"""This module contains the decode function for sEMG from GAPWatch.


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

packetSize: int = 160
"""Number of bytes in each package."""

startSeq: list[bytes] = [b"="]
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = [b":"]
"""Sequence of commands to stop the board."""

fs: list[float] = [90]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [20]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "manus")
"""Named tuple containing the Manus data packet."""


def decodeFn(data: bytes) -> SigsPacket:
    """Function to decode the binary data received from Manus.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    SigsPacket
        Named tuple containing the Manus data packet with shape (nSamp, nCh).
    """
    nSamp = 1

    joints = np.asarray(struct.unpack(f"<{nSamp * 40}f", data), dtype="float32")

    # Reshape and convert ADC readings to uV
    joints = joints.reshape(nSamp, 40)[:, :20]

    return SigsPacket(manus=joints)
