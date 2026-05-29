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

# EEG configuration
SAMPLE_RATE_EEG = 500  # Hz
SAMPLES_PER_PACKET_EEG = 4  # samples per packet
EEG_N_CHANNELS = 16

# Microphone configuration
SAMPLE_RATE_MIC = 16000  # Hz
SAMPLE_BIT_WIDTH = 16  # bits
SAMPLES_PER_PACKET_MIC = 64  # 16-bit samples per BLE packet

# Packet format constants
EEG_HEADER = 0x55
EEG_TRAILER = 0xAA
EEG_PACKET_SIZE = 211

MIC_HEADER = 0xAA
MIC_TRAILER = 0x55
MIC_PACKET_SIZE = 136


packetSize = [(EEG_HEADER, EEG_PACKET_SIZE), (MIC_HEADER, MIC_PACKET_SIZE)]
"""List of (header_byte, packet_size) tuples for EEG and MIC packets."""

startSeq: list[bytes] = [
    (18).to_bytes(),  # START_EEG_STREAMING command
    0.2,  # Wait 200 ms
    (26).to_bytes(),  # START_MIC_STREAMING command
]
"""Sequence of commands to start EEG and microphone streaming."""

stopSeq: list[bytes] = [
    (19).to_bytes(),  # STOP_EEG_STREAMING command
    0.2,  # Wait 200 ms
    (27).to_bytes(),  # STOP_MIC_STREAMING command
]
"""Sequence of commands to stop EEG and microphone streaming."""

fs: list[float] = [SAMPLE_RATE_EEG, SAMPLE_RATE_MIC]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [EEG_N_CHANNELS, 1]
"""Sequence of integers representing the number of channels of each signal."""

sigInfo: dict = {
    "eeg": {"fs": SAMPLE_RATE_EEG, "nCh": EEG_N_CHANNELS},
    "mic_eeg": {"fs": SAMPLE_RATE_MIC, "nCh": 1},
    "counter_eeg": {"fs": SAMPLE_RATE_EEG / SAMPLES_PER_PACKET_EEG, "nCh": 1},
    "counter_mic_eeg": {"fs": SAMPLE_RATE_MIC / SAMPLES_PER_PACKET_MIC, "nCh": 1},
    "timestamp_eeg": {"fs": SAMPLE_RATE_EEG / SAMPLES_PER_PACKET_EEG, "nCh": 1},
    "timestamp_mic_eeg": {"fs": SAMPLE_RATE_MIC / SAMPLES_PER_PACKET_MIC, "nCh": 1},
}
"""Dictionary containing the signals information."""


def _decode_eeg(data: bytes) -> np.ndarray:
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


def _decode_mic(data: bytes) -> np.ndarray:
    """Decode microphone packet.
    Packet structure (132 bytes total):
    - 1 byte header (0xAA)
    - 2 byte counter
    - 64 samples of 16-bit signed audio data (128 bytes)
    - 1 byte trailer (0x55)
    """
    counter = bytearray(data[1:3])
    counter = np.asarray(struct.unpack("<H", counter), dtype=np.int32)
    counter = counter.reshape(1, 1)

    timestamp = bytearray(data[3:7])
    timestamp = np.asarray(struct.unpack("<I", timestamp), dtype=np.uint32)
    timestamp = timestamp.reshape(1, 1)
    
    audio_data = data[7:7 + SAMPLES_PER_PACKET_MIC * 2] 

    # Unpack 16-bit signed samples (little-endian)
    audio = np.array(
        struct.unpack(f"<{SAMPLES_PER_PACKET_MIC}h", audio_data),
        dtype=np.int16
    )

    # Reshape to (nSamp, nCh) format
    audio = audio.reshape(-1, 1)

    # Convert to float32 normalized to [-1.0, 1.0] range
    audio = audio.astype(np.float32) / 32768.0

    return audio, counter, timestamp


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """
    Function to decode binary data received from BioGAP.

    Distinguishes between microphone and EEG packets based on the header byte
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
        - For mic packets: {"eeg": empty, "mic_eeg": mic_data, "counter_eeg": None, "counter_mic_eeg": mic_counter}
        - For EEG packets: {"eeg": eeg_data, "mic_eeg": empty, "counter_eeg": eeg_counter, "counter_mic_eeg": None}
    """
    packet_len = len(data)
    header = data[0]
    if packet_len == MIC_PACKET_SIZE and header == MIC_HEADER:
        # This is a microphone packet
        trailer = data[-1]
        if trailer != MIC_TRAILER:
            raise ValueError(f"Invalid mic trailer: 0x{trailer:02X}, expected 0x{MIC_TRAILER:02X}")
        audio, counter, timestamp = _decode_mic(data)
        return {"eeg": None, "counter_eeg": None, "mic_eeg": audio, "counter_mic_eeg": counter, "timestamp_eeg": None, "timestamp_mic_eeg": timestamp}
    elif packet_len == EEG_PACKET_SIZE and header == EEG_HEADER:
        # This is an EEG packet
        trailer = data[-1]
        if trailer != EEG_TRAILER:
            raise ValueError(f"Invalid EEG trailer: 0x{trailer:02X}, expected 0x{EEG_TRAILER:02X}")
        eeg, counter, timestamp = _decode_eeg(data)
        return {"eeg": eeg, "counter_eeg": counter, "mic_eeg": None, "counter_mic_eeg": None, "timestamp_eeg": timestamp, "timestamp_mic_eeg": None}
    else:
        raise ValueError(f"Invalid packet: size={packet_len}, header=0x{header:02X}")