"""
This module contains the BioGAP interface for sEMG.


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

GAIN = 12


def createCommand():
    """Internal function to create start command."""
    command = []
    # Byte 0: ADS sampling rate
    # - 6 -> 500sps
    command.append(6)
    # Byte 1: ADS1298 mode
    # - 0 -> default
    command.append(0)
    # Byte 2: depends on the number of ADSs
    command.append(1)
    # Byte 3: chip select (not modifiable)
    command.append(4)
    # Byte 4: PGA gain
    # 16 ->  1
    # 32 ->  2
    # 64 ->  4
    #  0 ->  6
    # 80 ->  8
    # 96 -> 12
    gainCmdMap = {
        1: 16,
        2: 32,
        4: 64,
        6: 0,
        8: 80,
        12: 96,
    }
    command.append(gainCmdMap[GAIN])
    # Byte 5: CR (not modifiable)
    command.append(13)
    # Byte 6: LF (not modifiable)
    command.append(10)

    return command


packetSize: int = 234
"""Number of bytes in each package."""

startSeq: list[bytes | float] = [
    bytes([20, 1, 50]),
    0.2,
    (18).to_bytes(),
    0.2,
    bytes(createCommand()),
]
"""
Sequence of commands (as bytes) to start the device; floats are
interpreted as delays (in seconds) between commands.
"""

stopSeq: list[bytes | float] = [(19).to_bytes()]
"""
Sequence of commands (as bytes) to stop the device; floats are
interpreted as delays (in seconds) between commands.
"""

sigInfo: dict = {"emg": {"fs": 500, "nCh": 8}}
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
    nSamp, nCh = 7, sigInfo["emg"]["nCh"]

    # ADC parameters
    vRef = 2.5
    nBit = 24

    dataTmp = bytearray(
        data[2:26]
        + data[34:58]
        + data[66:90]
        + data[98:122]
        + data[130:154]
        + data[162:186]
        + data[194:218]
    )
    # Convert 24-bit to 32-bit integer
    pos = 0
    for _ in range(len(dataTmp) // 3):
        prefix = 255 if dataTmp[pos] > 127 else 0
        dataTmp.insert(pos, prefix)
        pos += 4
    emgAdc = np.asarray(
        struct.unpack(f">{nSamp * nCh}i", dataTmp), dtype=np.int32
    ).reshape(nSamp, nCh)

    # ADC readings to mV
    emg = (emgAdc * vRef / (GAIN * (2 ** (nBit - 1) - 1))).astype(np.float32)  # V
    emg *= 1_000  # mV

    return {"emg": emg}
