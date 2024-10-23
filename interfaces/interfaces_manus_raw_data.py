"""
This module contains the Manus interface to Retrieve Ergonomics Data from the Manus Glove 

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

startSeq: list[bytes] = [b"A"]
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = []
"""Sequence of commands to stop the board."""

fs: list[float] = [120]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [20]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "manus")
"""Named tuple containing the Manus data packet."""

rawDataSize: int=15
"""Number of packets in Each Package recevied from TCP (start_id + 11 values (node_id - 3positions - 4quaternions - 3scales) + 2 timestamps + stop_id)"""
packetSize: int = 4
"""Number of bytes in each packet (all data transmitted as floats)."""



def decodeFn(data: bytes) -> SigsPacket:
    """
    Function to decode the binary data received from Manus.

    Parameters
    ----------
    data : bytes
        A packet of bytes 

    Returns
    -------
    SigsPacket
        Named tuple containing the Manus data packet with shape (nSamp, nCh).
    """
    start_raw = struct.unpack('<1f', data[:4])  
    #print(f'Start of raw data: {start_raw}')
    # Read the 11 floats (for glove data) [4:84]
    node_id = struct.unpack('<1f', data[4:8])  
    pos = struct.unpack('<3f', data[8:20])  
    rots = struct.unpack('<4f', data[20:36])
    #print(rots)
    scales=struct.unpack('<3f', data[36:48])
    #print(f'Glove data: {glove_data}')
    # Unpack the two floats (timestamps)
    float_values = struct.unpack('<2f', data[48:56])  # Little-endian floats
    # Combine the two floats back into a double
    double_as_bytes = struct.pack('<2f', *float_values)
    seconds_as_double = struct.unpack('<d', double_as_bytes)[0]
    #print(f'{seconds_as_double:.6f}')
    # Read the last float (stop of ergo data communication)
    stop_raw = struct.unpack('<1f', data[56:60])  
    quats_and_ts = rots + (seconds_as_double,)

    return SigsPacket(manus=quats_and_ts)
