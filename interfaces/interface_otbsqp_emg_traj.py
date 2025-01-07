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
    # 0 = standard range, 1 = 2x range, 2 = 4x range, 3 = 8x range
    ext = 0
    # 0 = no filter, 1 = filter
    hpf = 1
    # 0 = 16 bit, 1 = 24 bit
    hres = 0
    # 0 = monopolar, 1 = bipolar, 2 = differential,
    # 3 = accelerometers, 6 = impedance check, 7 = test mode
    mode = 0
    # 0 = 8 channels, 1 = 16 channels, 2 = 32 channels, 3 = 64 channels
    nch = 3
    # if mode != 3: 0 = 500 sps, 1 = 1000 sps, 2 = 2000 sps
    # if mode == 3: 0 = 2000 sps, 1 = 4000 sps, 2 = 8000 sps
    fsamp = 2

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

    return command


packetSize: int = 9216
"""Number of bytes in each package."""

startSeq: list[bytes] = [
    createCommand(1).to_bytes(2, byteorder="big"),
]
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = [
    createCommand(0).to_bytes(2, byteorder="big"),
]
"""Sequence of commands to stop the board."""

fs: list[float] = [2000, 2000, 2000, 2000]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [64, 4, 1, 3]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "emg imu trigger force")
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
    buf_size = 32

    # Get EMG data
    emg = np.asarray(
        struct.unpack(f"<{buf_size * 64}f", data[: buf_size * 4 * 64]),
        dtype=np.int32,
    ).reshape(-1, 64)

    # Convert ADC readings to mV
    mVConvF = 2.86e-4  # conversion factor
    emg = (emg * mVConvF).astype(np.float32)

    # Get IMU data
    imu = np.asarray(
        struct.unpack(f"<{buf_size * 4}f", data[buf_size * 4 * 64 : buf_size * 4 * 68]),
        dtype=np.float32,
    ).reshape(-1, 4)

    # Get trigger
    trigger = np.asarray(
        struct.unpack(f"<{buf_size}f", data[buf_size * 4 * 68 : buf_size * 4 * 69]),
        dtype=np.float32,
    ).reshape(-1, 1)

    # Get force and trajectories
    force = np.zeros(shape=(buf_size, 3), dtype=np.float32)
    force[:, 0] = np.asarray(
        struct.unpack(f"<{buf_size}f", data[buf_size * 4 * 69 : buf_size * 4 * 70])
    )
    force[:, 1] = np.asarray(
        struct.unpack(f"<{buf_size}f", data[buf_size * 4 * 70 : buf_size * 4 * 71])
    )
    force[:, 2] = np.asarray(struct.unpack(f"<{buf_size}f", data[buf_size * 4 * 71 :]))

    return SigsPacket(emg=emg, imu=imu, trigger=trigger, force=force)
