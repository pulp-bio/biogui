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

nCh: list[int] = [21]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "manus_ergo")
"""Named tuple containing the Manus data packet."""

ergoDataSize: int=24
"""Number of packets in Each Package recevied from TCP (start_id + 20 angles + 2 timestamps + stop_id)"""
packetSize: int = 4 * ergoDataSize
"""Number of bytes in each packet (all data transmitted as floats)."""
num_joint_angles: int=20
"""Number of joint angles transmitted from the Manus SDK (20 for single Hand)"""


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
    #print(f'Data from Ergo Port:{data}')
    # First, read the first float (start of ergo data communication)
    start_ergo = struct.unpack('<1f', data[:4])  
    #print(f'Start of ergonomic data: {start_ergo}')
    # Read the 20 floats (for glove data) [4:84]
    glove_data = struct.unpack('<20f', data[4:84])  
    #print(f'Glove data: {glove_data}')
    # Unpack the two floats (timestamps)
    float_values = struct.unpack('<2f', data[84:92])  # Little-endian floats
    # Combine the two floats back into a double
    double_as_bytes = struct.pack('<2f', *float_values)
    seconds_as_double = struct.unpack('<d', double_as_bytes)[0]
    #print(f'{seconds_as_double:.6f}')
    # Read the last float (stop of ergo data communication)
    stop_ergo = struct.unpack('<1f', data[92:96])  
    # Prepare the joint data for logging
    joints = np.array(glove_data)
    #joints_and_ts = joints + (seconds_as_double,)
    #joints_and_ts = np.append(joints, seconds_as_double)           OLD CODE
    joints_and_ts = np.append(joints, float_values)
    #reshape in a format for plotting utils
    joints_and_ts = joints_and_ts.reshape(1, 22)
    #print(joints_and_ts)
    return SigsPacket(manus_ergo=joints_and_ts)
