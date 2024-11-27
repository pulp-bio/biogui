"""
This module contains the OTBIO Sessantaquattro+ interface for sEMG.


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


packetSize: int = 144
"""Number of bytes in each package."""

startSeq: list[bytes] = [
    createCommand(1).to_bytes(2, byteorder="big"),
]
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = [
    createCommand(0).to_bytes(2, byteorder="big"),
]
"""Sequence of commands to stop the board."""

fs: list[float] = [2000]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [64]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "emg")
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
    # Conversion factor for mV
    mVConvF = 2.86e-4

    # Convert 16-bit to 32-bit integer
    emg = np.asarray(struct.unpack(">64h", data[:128]), dtype=np.int32)

    # Reshape and convert ADC readings to mV
    emg = emg.reshape(1, 64)
    emg = emg * mVConvF  # mV
    emg = emg.astype(np.float32)

    return SigsPacket(emg=emg)
