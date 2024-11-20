<<<<<<<< HEAD:interfaces/interface_manus.py
"""
This module contains the Manus interface for kinematic data.


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

startSeq: list[bytes] = [b"A"]
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = []
"""Sequence of commands to stop the board."""

fs: list[float] = [120]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [20]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "manus")
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
    joints = np.asarray(struct.unpack(f"<{40}f", data), dtype=np.float32)

    # Reshape and convert ADC readings to uV
    joints = joints.reshape(1, 40)[:, 20:]

    return SigsPacket(manus=joints)
========
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

packetSize: int = 132
"""Number of bytes in each packet (all data transmitted as floats)."""

startSeq: list[bytes] = []
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = [b"S"]
"""Sequence of commands to stop the board."""

fs: list[float] = [120, 120]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [24, 2]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "manusData tsRaw")
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
    # 35 floats:
    # - 20 for angles
    # -  1 for nodeId
    # -  3 for position
    # -  4 for quaternion
    # -  3 for scale
    # -  2 for raw timestamp (double)

    manusData = np.zeros(shape=(1, 24), dtype=np.float32)

    # Read the 20 angles [0:80]
    manusData[0, :20] = np.asarray(struct.unpack("<20f", data[:80]), dtype=np.float32)

    # Read the quaternions [96:112]
    manusData[0, 20:24] = np.asarray(
        struct.unpack("<4f", data[96:112]), dtype=np.float32
    )

    # Read timestamp as two separate floats [124:132]
    tsRaw = np.asarray(struct.unpack("<2f", data[124:]), dtype=np.float32).reshape(1, 2)

    return SigsPacket(manusData=manusData, tsRaw=tsRaw)
>>>>>>>> f7d8538 (Removed one timestamp from MANUS interface file; added stop command.):interfaces/interface_manus_ergo_raw.py
