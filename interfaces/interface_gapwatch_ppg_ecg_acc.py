"""This module contains the decode function for GAPWatch bio-signals.


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

packetSize: int = 204
"""Number of bytes in each package."""

startSeq: list[bytes] = []
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = []
"""Sequence of commands to stop the board."""

fs: list[float] = [128, 128, 12.8]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [1, 1, 3]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "ppg, ecg, acc")
"""Named tuple containing the PPG, ECG and accelerometer packets."""


def decodeFn(data: bytes) -> SigsPacket:
    """Function to decode the binary data received from GAPWatch into PPG, ECG and accelerometer signals.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    SigsPacket
        Named tuple containing the PPG, ECG and accelerometer packets, each with shape (nSamp, nCh).
    """

    # Split bytes into PPG, ECG and accelerometer
    ppgBytes = bytearray(data[:30] + data[68:98] + data[136:166])
    ecgBytes1 = bytearray(data[30:60] + data[98:128] + data[166:196])
    accelBytes = bytearray(data[60:66] + data[128:134] + data[196:202])
    ecgBytes2 = []

    # Convert to 32-bit integer
    pos = 0
    for _ in range(len(ppgBytes) // 3):
        ppgBytes.insert(pos, 0)

        # Handle ECG format
        ecgBytes1.insert(pos, 0)
        ecgTmp = struct.unpack(">I", ecgBytes1[pos : pos + 4])[0] >> 6
        ecgByte = bytearray(struct.pack(">I", ecgTmp))
        if ecgByte[1] > 1:
            ecgByte[0] = 255
            ecgByte[1] |= 252
        ecgBytes2.append(struct.unpack(">i", ecgByte)[0])

        pos += 4
    ppg = np.asarray(struct.unpack(">30i", ppgBytes), dtype=np.int32)
    ecg = np.asarray(ecgBytes2, dtype=np.int32)
    acc = np.asarray(struct.unpack("<9h", accelBytes), dtype=np.int32)

    # ADC parameters
    vRefECG = 1.0
    gainECG = 160.0
    nBitECG = 17
    accConvFactor = 0.061

    # Reshape PPG
    ppg = ppg.reshape(-1, 1)  # 1 channel
    ppg = ppg.astype(np.float32)
    # Reshape ECG and convert it to mV
    ecg = ecg.reshape(-1, 1)  # 1 channel
    ecg = ecg * (vRefECG / gainECG / 2**nBitECG)  # V
    ecg *= 1000  # mV
    ecg = ecg.astype(np.float32)
    # Reshape accelerometer and convert it to mg
    acc = acc.reshape(-1, 3)  # 3 channels
    acc = acc * accConvFactor  # mg
    acc = acc.astype(np.float32)

    return SigsPacket(ppg=ppg, ecg=ecg, acc=acc)
