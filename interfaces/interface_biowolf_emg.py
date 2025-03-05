"""
This module contains the BioWolf interface for sEMG.


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

packetSize: int = 243
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

sigInfo: dict = {"emg": {"fs": 4000, "nCh": 16}}
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
    nSamp, nCh = 5, sigInfo["emg"]["nCh"]

    # ADC parameters
    vRef = 2.5
    gain = 6.0
    nBit = 24

    # Convert 24-bit to 32-bit integer
    dataTmp = bytearray(data)[2:242]
    pos = 0
    for _ in range(len(dataTmp) // 3):
        prefix = 255 if dataTmp[pos] > 127 else 0
        dataTmp.insert(pos, prefix)
        pos += 4
    emgAdc = np.asarray(
        struct.unpack(f">{nSamp * nCh}i", dataTmp), dtype=np.int32
    ).reshape(nSamp, nCh)

    # ADC readings to mV
    emg = emgAdc * vRef / (gain * (2 ** (nBit - 1) - 1))  # V
    emg *= 1_000  # mV
    emg = emg.astype(np.float32)

    return {"emg": emg}
