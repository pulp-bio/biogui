# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
This module contains the GAPWatch interface for PPG, ECG and accelerometer.
"""

import struct

import numpy as np

packetSize: int = 68
"""Number of bytes in each package."""

startSeq: list[bytes | float] = [b"="]
"""
Sequence of commands (as bytes) to start the device; floats are
interpreted as delays (in seconds) between commands.
"""

stopSeq: list[bytes | float] = [b":"]
"""
Sequence of commands (as bytes) to stop the device; floats are
interpreted as delays (in seconds) between commands.
"""

sigInfo: dict = {
    "ppg": {"fs": 128, "nCh": 1},
    "ecg": {"fs": 128, "nCh": 1},
    "acc": {"fs": 12.8, "nCh": 3},
}
"""Dictionary containing the signals information."""


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """
    Function to decode the binary data received from the device into signals.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    dict of (str: ndarray)
        Dictionary containing the signal data packets, each with shape (nSamp, nCh);
        the keys must match with those of the "sigInfo" dictionary.
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
    ppg = np.asarray(struct.unpack(">10i", ppgBytes), dtype=np.int32)
    ecg = np.asarray(ecgBytes2, dtype=np.int32)
    acc = np.asarray(struct.unpack("<3h", accelBytes), dtype=np.int32)

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

    return {"ppg": ppg, "ecg": ecg, "acc": acc}
