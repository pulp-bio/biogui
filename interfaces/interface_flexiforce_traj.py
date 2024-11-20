"""
This module contains the FlexiForce interface for force data,
together with synthetic force trajectories.


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

packetSize: int = 12
"""Number of bytes in each package."""

startSeq: list[bytes] = []
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = []
"""Sequence of commands to stop the board."""

fs: list[float] = [30]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [3]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "force")
"""Named tuple containing the EMG packet."""


def decodeFn(data: bytes) -> SigsPacket:
    """
    Function to decode the binary data received from the FlexiForce script into force values.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    SigsPacket
        Named tuple containing the data with shape (nSamp, nCh).
    """
    force = np.zeros(shape=(1, 3), dtype=np.float32)

    # Read force data
    force[0, 0] = struct.unpack("<f", data[:4])[0]

    # Read trajectories
    force[0, 1:] = np.asarray(struct.unpack("<2f", data[4:]), dtype=np.float32)

    return SigsPacket(force=force)
