"""
This module contains the OTBioelettronica Sessantaquattro+
interface for HD-sEMG.


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
    # getset = 0

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
    # command = command + getset * 32768

    return command


packetSize: int = 144
"""Number of bytes in each package."""

startSeq: list[bytes] = [
    createCommand(1).to_bytes(2, byteorder="big"),
]
"""Sequence of commands to start the device."""

stopSeq: list[bytes] = [
    createCommand(0).to_bytes(2, byteorder="big"),
]
"""Sequence of commands to stop the device."""

sigInfo: dict = {
    "emg": {"fs": 2000, "nCh": 64},
    "aux": {"fs": 2000, "nCh": 2},
    "imu": {"fs": 2000, "nCh": 4},
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
    # 72 shorts:
    # - 64 for EMG data
    # - 2 for AUX
    # - 4 for IMU
    # - 1 for SyncStation trigger
    # - 1 for sample counter

    # Get EMG data
    emg = np.asarray(struct.unpack(">64h", data[:128]), dtype=np.int32).reshape(1, 64)

    # Convert ADC readings to mV
    mVConvF = 2.86e-4  # conversion factor
    emg = (emg * mVConvF).astype(np.float32)

    # Get AUX data
    aux = np.asarray(struct.unpack(">2h", data[128:132]), dtype=np.float32).reshape(
        -1, 2
    )
    # Get IMU data
    imu = np.asarray(struct.unpack(">4h", data[132:140]), dtype=np.float32).reshape(
        -1, 4
    )

    return {"emg": emg, "aux": aux, "imu": imu}
