"""
This module contains the BioGAP interface for combined EEG and microphone streaming.

Copyright 2025 ETH Zurich and University of Bologna

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

# EMG configuration
SAMPLE_RATE_EEG = 500  # Hz
SAMPLES_PER_PACKET_EEG = 4  # samples per packet
EEG_N_CHANNELS = 16

# Packet format constants
EEG_HEADER = 0x55
EEG_TRAILER = 0xAA
EEG_PACKET_SIZE = 211


packetSize = [(EEG_HEADER, EEG_PACKET_SIZE)]
"""List of (header_byte, packet_size) tuples for EEG packets."""

startSeq: list[bytes] = [
    (18).to_bytes(),  # START_EEG_STREAMING command
    0.2,  # Wait 200 ms
]
"""Sequence of commands to start EEG streaming."""

stopSeq: list[bytes] = [
    (19).to_bytes(),  # STOP_EEG_STREAMING command
    0.2,  # Wait 200 ms
]
"""Sequence of commands to stop EEG streaming."""

fs: list[float] = [SAMPLE_RATE_EEG]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [EEG_N_CHANNELS]
"""Sequence of integers representing the number of channels of each signal."""

sigInfo: dict = {
    "eeg": {"fs": SAMPLE_RATE_EEG, "nCh": EEG_N_CHANNELS},
    "counter_eeg": {"fs": SAMPLE_RATE_EEG / SAMPLES_PER_PACKET_EEG, "nCh": 1},
    "timestamp_eeg": {"fs": SAMPLE_RATE_EEG / SAMPLES_PER_PACKET_EEG, "nCh": 1},
}
"""Dictionary containing the signals information."""


def _decode_eeg(data: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Decode EEG packet.
    Packet structure (211 bytes total):
    - 1 byte: Header (0x55)
    - 2 byte: Packet counter
    - 4 bytes: Timestamp (microseconds, for cross-packet synchronization)
    - 200 bytes: 4 samples × 50 bytes per sample
      - 24 bytes: ADS1298_A data (8 channels × 3 bytes)
      - 24 bytes: ADS1298_B data (8 channels × 3 bytes)
      - 1 byte: Counter_extra
      - 1 byte: Trigger
    - 3 bytes: Metadata (reserved for future use)
    - 1 byte: Trailer (0xAA)
    """
    nSamp = 4
    nCh = 16
    nChSingleADS = 8
    vRef = 2.4
    gain = 6.0
    nBit = 24

    counter = bytearray(data[1:3])

    # Cast the counter to np.int32
    counter = np.asarray(struct.unpack("<H", counter), dtype=np.int32)
    counter = counter.reshape(1, 1)
    
    timestamp = bytearray(data[3:7])
    timestamp = np.asarray(struct.unpack("<I", timestamp), dtype=np.uint32)
    timestamp = timestamp.reshape(1, 1)
    
    dataADSATmp = bytearray(
        data[7:31] + data[57:81] + data[107:131] + data[157:181]
    )
    dataADSBTmp = bytearray(
       data[31:55] + data[81:105] + data[131:155] + data[181:205]
    )

    pos = 0
    for _ in range(len(dataADSATmp) // 3):
        prefix = 255 if dataADSATmp[pos] > 127 else 0
        dataADSATmp.insert(pos, prefix)
        pos += 4
    eegADSA = np.asarray(struct.unpack(f">{nSamp *nChSingleADS}i", dataADSATmp), dtype=np.int32)
    eegADSA = eegADSA.reshape(nSamp, nChSingleADS)
    pos = 0
    for _ in range(len(dataADSBTmp) // 3):
        prefix = 255 if dataADSBTmp[pos] > 127 else 0
        dataADSBTmp.insert(pos, prefix)
        pos += 4
    eegADSB = np.asarray(struct.unpack(f">{nSamp *nChSingleADS}i", dataADSBTmp), dtype=np.int32)
    eegADSB = eegADSB.reshape(nSamp, nChSingleADS)
    eegAllChannels = np.concatenate((eegADSA, eegADSB), axis=1)  # (nSamp, 16)

    eeg = eegAllChannels * (vRef / (gain * (2 ** (nBit - 1) - 1)))
    eeg *= 10e6  # uV
    eeg = eeg.astype(np.float32)
    return eeg, counter,timestamp


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """
    Function to decode binary data received from BioGAP. It determines the signal type based on the header byte
    and packet size. Returns the decoded signal immediately, with an empty array
    for the other signal type.

    Parameters
    ----------
    data : bytes
        A packet of either 132 bytes (MIC) or 211 bytes (EEG).

    Returns
    -------
    dict[str, np.ndarray]
        Dictionary containing the decoded signals:
        - For EEG packets: {"eeg": eeg_data, "counter_eeg": eeg_counter}
    """
    packet_len = len(data)
    header = data[0]
    if packet_len == EEG_PACKET_SIZE and header == EEG_HEADER:
        # This is an EEG packet
        trailer = data[-1]
        if trailer != EEG_TRAILER:
            raise ValueError(f"Invalid EEG trailer: 0x{trailer:02X}, expected 0x{EEG_TRAILER:02X}")
        eeg, counter, timestamp = _decode_eeg(data)
        return {"eeg": eeg, "counter_eeg": counter, "timestamp_eeg": timestamp}
    else:
        raise ValueError(f"Invalid packet: size={packet_len}, header=0x{header:02X}")