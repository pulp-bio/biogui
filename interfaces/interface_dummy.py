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

from collections import namedtuple

import numpy as np

packetSize: int = 0
"""Number of bytes in each package."""

startSeq: list[bytes] = []
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = []
"""Sequence of commands to stop the board."""

fs: list[float] = [128, 51.2]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [4, 2]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "sig1, sig2")
"""Named tuple containing the packets for the two dummy signals."""


def decodeFn(data: bytes) -> SigsPacket:
    """
    Function to decode the binary data generated into two dummy signals.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    SigsPacket
        Named tuple containing the two dummy signals.
    """
    dataTmp = np.frombuffer(data, dtype=np.float32)
    nSamp1, nSamp2 = 10, 4
    sig1 = dataTmp[: nSamp1 * 4].reshape(nSamp1, 4)
    sig2 = dataTmp[nSamp1 * 4 :].reshape(nSamp2, 2)

    return SigsPacket(sig1=sig1, sig2=sig2)
