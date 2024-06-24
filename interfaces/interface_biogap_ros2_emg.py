"""
This module contains the BioGAP-ROS2 interface for sEMG.


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
from collections.abc import Sequence

import numpy as np

packetSize: int = 224
"""Number of bytes in each package."""

startSeq: list[bytes] = []
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = []
"""Sequence of commands to stop the board."""

fs: list[float] = [500]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [8]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "emg")
"""Named tuple containing the EMG packet."""


def decodeFn(data: bytes) -> Sequence[np.ndarray]:
    """
    Function to decode the binary data received from GAP via ROS2 into a single sEMG signal.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    Sequence of ndarray
        Sequence of corresponding signals with shape (nSamp, nCh).
    """
    dataTmp = np.frombuffer(data, dtype=np.float32)
    nSamp, nCh = 7, 8
    sig = dataTmp[: nSamp * nCh].reshape(nSamp, nCh)

    return [sig]
