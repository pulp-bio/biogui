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
from collections.abc import Sequence

import numpy as np


def decodeFn(data: bytes) -> Sequence[np.ndarray]:
    """Function to decode the binary data received from GAPWatch into PPG, ECG and accelerometer signals.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    ndarray
        PPG signal with shape (nSamp, nCh).
    ndarray
        ECG signal with shape (nSamp, nCh).
    ndarray
        Accelerometer signal with shape (nSamp, nCh).
    """

    # Split bytes into PPG, ECG and accelerometer
    ppgBytes = bytearray(data[:30])
    ecgBytes1 = bytearray(data[30:60])
    accelBytes = bytearray(data[60:66])
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
    ppg = np.asarray(struct.unpack(">10i", ppgBytes), dtype="int32")
    ecg = np.asarray(ecgBytes2, dtype="int32")
    acc = np.asarray(struct.unpack("<3h", accelBytes), dtype="int32")

    # ADC parameters
    vRefECG = 1.0
    gainECG = 160.0
    nBitECG = 17
    accConvFactor = 0.061

    # Reshape PPG
    ppg = ppg.reshape(-1, 1)  # 1 channel
    ppg = ppg.astype("float32")
    # Reshape ECG and convert it to mV
    ecg = ecg.reshape(-1, 1)  # 1 channel
    ecg = ecg * (vRefECG / gainECG / 2**nBitECG)  # V
    ecg *= 1000  # mV
    ecg = ecg.astype("float32")
    # Reshape accelerometer and convert it to mg
    acc = acc.reshape(-1, 3)  # 3 channels
    acc = acc * accConvFactor  # mg
    acc = acc.astype("float32")

    return ppg, ecg, acc
