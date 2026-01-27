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
from collections import namedtuple
import datetime

import numpy as np

packetSize: int = 234
"""Number of bytes in each package."""

startSeq: list[bytes] = [
    bytes([20, 1, 50]),
    (18).to_bytes(),
    bytes([6, 0, 1, 4, 0, 13, 10]),
]
"""Sequence of commands to start the board."""

stopSeq: list[bytes] = [(19).to_bytes()]
"""Sequence of commands to stop the board."""

fs: list[float] = [500, 500, 500]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [8,1,3]
"""Sequence of integers representing the number of channels of each signal."""

SigsPacket = namedtuple("SigsPacket", "emg triggerWulpus counter")
"""Named tuple containing the EMG packet."""


def decodeFn(data: bytes) -> SigsPacket:
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

    nSamp = 7

    # ADC parameters
    vRef = 4
    gain = 6.0
    nBit = 24

    # counter for packets
    dataCnt = struct.unpack("B", data[1:2])
    #print(dataCnt)
    #print(data[1:2])
    counter = np.asarray(np.repeat(dataCnt, nSamp), dtype=np.int32)
    #print(counter)


    dataEmgTmp = bytearray(
        data[2:26] #sample 1; ch 1-8; 3 bytes per channel.
        + data[34:58] #sample 2 
        + data[66:90] # sample 3
        + data[98:122]
        + data[130:154]
        + data[162:186]
        + data[194:218]
    )

    """
    imuX = bytearray(
        data[26:28] #sample 1; ch 1-8; 3 bytes per channel.
        + data[58:60] #sample 2 
        + data[90:92] # sample 3
        + data[122:124]
        + data[154:156]
        + data[186:188]
        + data[218:220]
    )

    imuY = bytearray(
        data[28:30] #sample 1; ch 1-8; 3 bytes per channel.
        + data[60:62] #sample 2 
        + data[92:94] # sample 3
        + data[124:126]
        + data[156:158]
        + data[188:190]
        + data[220:222]
    )


    imuZ = bytearray(
        data[30:32] #sample 1; ch 1-8; 3 bytes per channel.
        + data[62:64] #sample 2 
        + data[94:96] # sample 3
        + data[126:128]
        + data[158:160]
        + data[190:192]
        + data[222:224]
    )


    )
    """
    """
    dataCounterTmp = bytearray(
        data[32:33] #sample 1; ch 1-8; 3 bytes per channel.
        + data[64:65] #sample 2 
        + data[96:97] # sample 3
        + data[128:129]
        + data[160:161]
        + data[192:193]
        + data[224:225]
    )
    
     
    # Unpack the bytes as unsigned 8-bit integers ('B' format)
    counter = np.asarray(struct.unpack(f'>{len(dataCounterTmp)}B', dataCounterTmp), dtype=np.int32)
    #print(counter)
    """
    # counter is stored on the space reserved for IMU
    dataWulpusCounterTmp = bytearray(
        data[27:29] #sample 1; ch 1-8; 3 bytes per channel.
        + data[59:61] #sample 2 
        + data[91:93] # sample 3
        + data[123:125]
        + data[155:157]
        + data[187:189]
        + data[219:221]
    )

    # counter is stored on the space reserved for IMU
    dataImuCounterTmp = bytearray(
        data[29:32] #sample 1; ch 1-8; 3 bytes per channel.
        + data[61:64] #sample 2 
        + data[93:96] # sample 3
        + data[125:128]
        + data[157:160]
        + data[189:192]
        + data[221:224]
    )

    # Trigger for WULPUS signal 
    dataTriggerTmp = bytearray(
        data[33:34]
        + data[65:66]
        + data[97:98]
        + data[129:130]
        + data[161:162]
        + data[193:194]
        + data[225:226]
    )
    #print(dataTriggerTmp)


    # Convert 24-bit to 32-bit integer
    pos = 0
    for _ in range(len(dataEmgTmp) // 3):
        prefix = 255 if dataEmgTmp[pos] > 127 else 0
        dataEmgTmp.insert(pos, prefix)
        pos += 4
    emg = np.asarray(struct.unpack(f">{nSamp * 8}i", dataEmgTmp), dtype=np.int32)
    
    # Convert 24-bit to 32-bit integer
    pos = 0
    for _ in range(len(dataImuCounterTmp) // 3):
        #prefix = 255 if dataImuCounterTmp[pos] > 127 else 0
        prefix = 0                  # 0 since we know that the number will always be positive 
        dataImuCounterTmp.insert(pos, prefix)
        pos += 4
    imuCounter = np.asarray(struct.unpack(f">{len(dataImuCounterTmp) // 4}i", dataImuCounterTmp), dtype=np.int32)
    #print(imuCounter)
    # Create One Unique Channel for everything
   

    #pos = 0
    #for _ in range(len(dataWulpusCounterTmp) // 3):
        #prefix = 255 if dataImuCounterTmp[pos] > 127 else 0
    #    prefix = 0                  # 0 since we know that the number will always be positive 
    #    dataImuCounterTmp.insert(pos, prefix)
    #    pos += 4

    # 
    WulpusCounter = np.asarray(struct.unpack(f">{len(dataWulpusCounterTmp) // 2}h", dataWulpusCounterTmp), dtype=np.int16)
    #print(WulpusCounter)
    counter = np.column_stack((counter, imuCounter, WulpusCounter))

    triggerWulpusTemp = bytearray()
    triggerWulpusSlowTemp = bytearray()
    for data in dataTriggerTmp:
        triggerWulpusTemp.append(data & 0x0F)
        triggerWulpusSlowTemp.append(data >> 4)
    triggerWulpus = np.asarray(struct.unpack(f"<{nSamp}B", triggerWulpusTemp), dtype=np.int32)
    #print(triggerWulpus)
    triggerWulpusSlow = np.asarray(struct.unpack(f"<{nSamp}B", triggerWulpusSlowTemp), dtype=np.int32)
    #SSprint(triggerWulpusSlow)
    # Reading the counter
    #counterTmp = bytearray()
    #for data in counterTmp:
    #    counterTmp.append(data & 0x0F)



    """
    counterTemp = bytearray()
    for data in dataCounterTmp:
        counterTemp.append(data & 0x0F)
    counter = np.asarray(struct.unpack(f"<{nSamp}B", counterTemp), dtype=np.int32)
    """

    # Reshape and convert ADC readings to uV
    emg = emg.reshape(nSamp, 8)
    emg = emg * (vRef / gain / 2**nBit)  # V
    emg *= 1_000_000  # uV
    emg = emg.astype(np.float32)
    print('....')
    return SigsPacket(emg=emg, triggerWulpus=triggerWulpusSlow.reshape(nSamp, 1), counter=counter.reshape(nSamp,3))
