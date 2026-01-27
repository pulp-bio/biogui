"""
This module contains the BioGAP interface for sEMG.


Copyright 2023 Mattia Orlandi, Pierangelo Maria Rapa
Modified by Giusy Spacone, 2025

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

packetSize: int = 234
"""Number of bytes in each package."""

startSeq: list[bytes] = [
    #bytes([20, 1, 50]),
    (18).to_bytes(),                                # send byte 18 to start 
    0.2,
    #bytes([6, 0, 1, 4, 0, 13, 10]),                # sample_rate, ADS_MODE (0), [2], [4], PGA_GAIN
    bytes([6, 0, 2, 4, 0])
]


#[b'\x12', b'\x06\x00\x02\x04\x00\r\n']
#Received data with len:0

"""Sequence of commands to start the board."""

stopSeq: list[bytes] = [(19).to_bytes()]
"""Sequence of commands to stop the board."""

fs: list[float] = [500]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [16]
"""Sequence of integers representing the number of channels of each signal."""


sigInfo: dict = {"biogap": {"fs": 500, "nCh": 16}, "counter": {"fs": 125, "nCh": 1}}
"""Dictionary containing the signals information."""


def decodeFn(data: bytes)  -> dict[str, np.ndarray]:
    """
    Function to decode the binary data received from BioGAP into a single sEMG signal.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    SigsPacket
        Named tuple containing the EMG packet with shape (nSamp, nCh).
    """
    nSamp = 4
    nCh = 16
    nChSingleADS = 8

    # ADC parameters
    vRef = 2.4                      # For differential measurements
    gain = 6.0
    nBit = 24
    # Byte 1: Header; Byte2: Counter; 
    # dataTmp = bytearray(
    #     data[2:26]                      # ADS A sample1   (8 channels)
    #     +data[58:82]                    # ADS A sample2
    #     +data[114:138]                  # ADS A sample3
    #     +data[170:194]                  # ADS A sample4
    #     +data[26:50]                    # ADSB sample1     (8 channels)
    #     +data[82:106]                   # ADSB sample2
    #     +data[138:162]                  # ADS2 sample3
    #     +data[194:218]                  # ADSB sample4
    # )
    counter = bytearray(data[1:2])

    # Cast the counter to np.int32
    counter = np.asarray(struct.unpack(">B", counter), dtype=np.int32)
    
    dataADSATmp = bytearray(
        data[2:26]                      # ADS A sample1   (8 channels)
        +data[58:82]                    # ADS A sample2
        +data[114:138]                  # ADS A sample3
        +data[170:194]                  # ADS A sample4
    )
    dataADSBTmp = bytearray(
        data[26:50]                    # ADSB sample1     (8 channels)
        +data[82:106]                   # ADSB sample2
        +data[138:162]                  # ADS2 sample3
        +data[194:218]                  # ADSB sample4
    )

    pos = 0
    for _ in range(len(dataADSATmp) // 3):
        prefix = 255 if dataADSATmp[pos] > 127 else 0
        dataADSATmp.insert(pos, prefix)
        pos += 4
    emgADSA = np.asarray(struct.unpack(f">{nSamp *nChSingleADS}i", dataADSATmp), dtype=np.int32)
    emgADSA = emgADSA.reshape(nSamp, nChSingleADS)
    pos = 0
    for _ in range(len(dataADSBTmp) // 3):
        prefix = 255 if dataADSBTmp[pos] > 127 else 0
        dataADSBTmp.insert(pos, prefix)
        pos += 4
    emgADSB = np.asarray(struct.unpack(f">{nSamp *nChSingleADS}i", dataADSBTmp), dtype=np.int32)
    emgADSB = emgADSB.reshape(nSamp, nChSingleADS)
    emgAllChannels = np.concatenate((emgADSA, emgADSB), axis=1)  # (nSamp, 16)

    counter = counter.reshape(1, 1)
    emg = emgAllChannels * (vRef / (gain * (2 ** (nBit - 1) - 1)))
    emg *= 10e6  # uV
    emg = emg.astype(np.float32)

    return {"biogap": emg, "counter": counter}
