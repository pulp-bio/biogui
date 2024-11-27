"""
This module contains the OTBIO Sessantaquattro+ interface for HD-sEMG
with trajectories based on the envelope.


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


def createCommand(start=1):
    """Internal function to create start/stop commands."""
    rec = 0
    trig = 0
    ext = 0
    hpf = 1
    hres = 0
    mode = 0
    nch = 3
    fsamp = 2
    getset = 0

    command = 0
    command = command + start
    command = command + rec * 2
    command = command + trig * 4
    command = command + ext * 16
    command = command + hpf * 64
    command = command + hres * 128
    command = command + mode * 256
    command = command + nch * 2048
    command = command + fsamp * 8192
    command = command + getset * 32768

    return command


packetSize: int = 268
"""Number of bytes in each package."""

startSeq: list[bytes] = [
    createCommand(1).to_bytes(2, byteorder="big"),
]
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = [
    createCommand(0).to_bytes(2, byteorder="big"),
]
"""Sequence of commands to stop the board."""

fs: list[float] = [2000, 2000]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [64]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "emg traj")
"""Named tuple containing the EMG packet."""


def decodeFn(data: bytes) -> SigsPacket:
    """
    Function to decode the binary data received from OTBIO Sessantaquattro+ into a single sEMG signal.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    SigsPacket
        Named tuple containing the EMG packet with shape (nSamp, nCh).
    """
    # Read EMG
    emg = np.asarray(struct.unpack("<64f", data[:256]), dtype=np.float32).reshape(
        -1, 64
    )

    # Read trajectories
    traj = np.asarray(struct.unpack("<3f", data[256:]), dtype=np.float32).reshape(-1, 3)

    return SigsPacket(emg=emg, traj=traj)
