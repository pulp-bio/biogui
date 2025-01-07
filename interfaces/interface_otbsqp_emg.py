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
    # The command comprises 2 control bytes. For further details, please refer to the manual:
    # https://otbioelettronica.it/download/182/sessantaquattro/2943/sessantaquattro-tcp-communication-protocol

    # Bit 0
    go = start
    # Bit 1
    rec = 0
    # Bits 3-2
    trig = 0
    # Bit 5-4:
    # - gain = 0:
    #   - hres = 0 -> preamp gain is 8;
    #   - hres = 1 -> preamp gain is 2;
    # - gain = 1 -> preamp gain is 4;
    # - gain = 2 -> preamp gain is 6;
    # - gain = 3 -> preamp gain is 8.
    gain = 0
    # Bit 6:
    # - hpf = 0 -> no high pass filter
    # - hpf = 1 -> high pass filter with EMA (cut-off of fs / 190 = 10.5 Hz)
    hpf = 1
    # Bit 7:
    # - hres = 0 -> 16 bits
    # - hres = 1 -> 24 bits
    hres = 0

    # Bits 2-0:
    # - mode = 0 -> monopolar;
    # - mode = 1 -> bipolar (AD8x1SP);
    # - mode = 2 -> differential;
    # - mode = 3 -> accelerometers;
    # - mode = 4 -> bipolar (AD4x8SP);
    # - mode = 5 -> impedance check advanced;
    # - mode = 6 -> impedance check;
    # - mode = 7 -> test mode (i.e., ramps).
    mode = 0
    # Bits 4-3:
    # nch = 0 -> 8 channels;
    # nch = 1 -> 16 channels;
    # nch = 2 -> 32 channels;
    # nch = 3 -> 64 channels.
    nch = 3
    # Bits 6-5:
    # - fsamp = 0 -> 500 sps;
    # - fsamp = 1 -> 1000 sps;
    # - fsamp = 2 -> 2000 sps;
    # - fsamp = 3 -> 4000 sps (only for reduced number of channels);
    fsamp = 2
    # Bit 7
    getset = 0

    # Build command
    command = go + rec * 2 + trig * 4 + gain * 16 + hpf * 64 + hres * 128
    command += mode * 256 + nch * 2048 + fsamp * 8192 + getset * 32768

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
