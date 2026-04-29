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
SAMPLE_RATE_EMG = 500  # Hz
SAMPLES_PER_PACKET_EMG = 4  # samples per packet
EMG_N_CHANNELS = 16

# Microphone configuration
SAMPLE_RATE_MIC = 16000  # Hz
SAMPLE_BIT_WIDTH = 16  # bits
SAMPLES_PER_PACKET_MIC = 64  # 16-bit samples per BLE packet

# Packet format constants
EMG_HEADER = 0x55
EMG_TRAILER = 0xAA
EMG_PACKET_SIZE = 211

MIC_HEADER = 0xAA
MIC_TRAILER = 0x55
MIC_PACKET_SIZE = 136


packetSize = [(EMG_HEADER, EMG_PACKET_SIZE), (MIC_HEADER, MIC_PACKET_SIZE)]
"""List of (header_byte, packet_size) tuples for EMG and MIC packets."""

startSeq: list[bytes] = [
    (37).to_bytes(),  # START_EMG_STREAMING command
    0.2,  # Wait 200 ms
    (26).to_bytes(),  # START_MIC_STREAMING command
]
"""Sequence of commands to start EMG and microphone streaming."""

stopSeq: list[bytes] = [
    (38).to_bytes(),  # STOP_EMG_STREAMING command
    0.2,  # Wait 200 ms
    (27).to_bytes(),  # STOP_MIC_STREAMING command
]
"""Sequence of commands to stop EMG and microphone streaming."""

fs: list[float] = [SAMPLE_RATE_EMG, SAMPLE_RATE_MIC]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [EMG_N_CHANNELS, 1]
"""Sequence of integers representing the number of channels of each signal."""

sigInfo: dict = {
    "emg": {"fs": SAMPLE_RATE_EMG, "nCh": EMG_N_CHANNELS},
    "mic_emg": {"fs": SAMPLE_RATE_MIC, "nCh": 1},
    "counter_emg": {"fs": SAMPLE_RATE_EMG / SAMPLES_PER_PACKET_EMG, "nCh": 1},
    "counter_mic_emg": {"fs": SAMPLE_RATE_MIC / SAMPLES_PER_PACKET_MIC, "nCh": 1},
    "timestamp_emg": {"fs": SAMPLE_RATE_EMG / SAMPLES_PER_PACKET_EMG, "nCh": 1},
    "timestamp_mic_emg": {"fs": SAMPLE_RATE_MIC / SAMPLES_PER_PACKET_MIC, "nCh": 1},
}
"""Dictionary containing the signals information."""


def _decode_emg(data: bytes) -> np.ndarray:
    """Decode EMG packet.
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
    timestamp = np.asarray(struct.unpack("<I", timestamp), dtype=np.int32)
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

    emg = emgAllChannels * (vRef / (gain * (2 ** (nBit - 1) - 1)))
    emg *= 10e6  # uV
    emg = emg.astype(np.float32)
    return emg, counter, timestamp


def _decode_mic(data: bytes) -> np.ndarray:
    """Decode microphone packet.
    Packet structure (136 bytes total):
    - 1 byte header (0xAA)
    - 2 byte counter
    - 64 samples of 16-bit signed audio data (128 bytes)
    - 1 byte trailer (0x55)
    """
    counter = bytearray(data[1:3])
    counter = np.asarray(struct.unpack("<H", counter), dtype=np.int32)
    counter = counter.reshape(1, 1)

    timestamp = bytearray(data[3:7])
    timestamp = np.asarray(struct.unpack("<I", timestamp), dtype=np.int32)
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

    Distinguishes between microphone and EMG packets based on the header byte
    and packet size. Returns the decoded signal immediately, with an empty array
    for the other signal type.

    Parameters
    ----------
    data : bytes
        A packet of either 136 bytes (MIC) or 211 bytes (EMG).

    Returns
    -------
    dict[str, np.ndarray]
        Dictionary containing the decoded signals:
        - For mic packets: {"emg": empty, "mic_emg": mic_data, "counter_emg": None, "counter_mic_emg": mic_counter}
        - For EMG packets: {"emg": emg_data, "mic_emg": empty, "counter_emg": emg_counter, "counter_mic_emg": None}
    """
    packet_len = len(data)
    header = data[0]
    if packet_len == MIC_PACKET_SIZE and header == MIC_HEADER:
        # This is a microphone packet
        trailer = data[-1]
        if trailer != MIC_TRAILER:
            raise ValueError(f"Invalid mic trailer: 0x{trailer:02X}, expected 0x{MIC_TRAILER:02X}")
        audio, counter, timestamp = _decode_mic(data)
        return {"emg": None, "counter_emg": None, "mic_emg": audio, "counter_mic_emg": counter, "timestamp_emg": None, "timestamp_mic_emg": timestamp}
    elif packet_len == EMG_PACKET_SIZE and header == EMG_HEADER:
        # This is an EMG packet
        trailer = data[-1]
        if trailer != EMG_TRAILER:
            raise ValueError(f"Invalid EMG trailer: 0x{trailer:02X}, expected 0x{EMG_TRAILER:02X}")
        emg, counter, timestamp = _decode_emg(data)
        return {"emg": emg, "counter_emg": counter, "mic_emg": None, "counter_mic_emg": None, "timestamp_emg": timestamp, "timestamp_mic_emg": None}
    else:
        raise ValueError(f"Invalid packet: size={packet_len}, header=0x{header:02X}")