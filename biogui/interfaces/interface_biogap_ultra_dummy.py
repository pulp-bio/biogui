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


EMULATE_EXG_DATA = 1
EMULATE_US_DATA = 0
if (EMULATE_EXG_DATA == 1):
    NRF_SAMPLE_RATE = 500
    NRF_PACKET_SIZE = 211
    NRF_HEADER = 0x55
    NRF_TAILER = 0xAA
    NRF_N_CHANNELS = 1
    NRF_SAMPLES_PER_PACKET = 4


elif (EMULATE_US_DATA == 1):
    NRF_SAMPLE_RATE = 100
    NRF_PACKET_SIZE = 211
    NRF_HEADER = 0x55
    NRF_TAILER = 0xAA
    NRF_N_CHANNELS = 1
    NRF_SAMPLES_PER_PACKET = 1



packetSize = [(NRF_HEADER, NRF_PACKET_SIZE)]
"""List of (header_byte, packet_size) tuples for NRF packets."""

startSeq: list[bytes] = [
    (249).to_bytes(),  # START_DUMMY_SENSOR command
    0.2,  # Wait 200 ms
]
"""Sequence of commands to start DUMMY streaming."""

stopSeq: list[bytes] = [
    (250).to_bytes(),  # STOP_DUMMY_SENSOR command
    0.2,  # Wait 200 ms
]
"""Sequence of commands to stop DUMMY streaming."""

fs: list[float] = [NRF_SAMPLE_RATE]
"""Sequence of floats representing the sampling rate of each signal."""

nCh: list[int] = [NRF_N_CHANNELS]
"""Sequence of integers representing the number of channels of each signal."""

sigInfo: dict = {
    "dummy": {"fs": NRF_SAMPLE_RATE, "nCh": NRF_N_CHANNELS},
    "counter_dummy": {"fs": NRF_SAMPLE_RATE / NRF_SAMPLES_PER_PACKET, "nCh": 1},
    "timestamp_dummy": {"fs": NRF_SAMPLE_RATE / NRF_SAMPLES_PER_PACKET, "nCh": 1},
}
"""Dictionary containing the signals information."""


def _decode_dummy(data: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Decode DUMMY packet.
    Packet structure (NRF_PACKET_SIZE bytes total):
    - 1 byte: Header (0x55)
    - 2 byte: Packet counter
    - 4 bytes: Timestamp (microseconds) 
    - 200 bytes: 4 samples × 50 bytes per sample
      - 24 bytes: ADS1298_A data (8 channels × 3 bytes)
      - 24 bytes: ADS1298_B data (8 channels × 3 bytes)
      - 1 byte: Counter_extra
      - 1 byte: Trigger
    - 3 bytes: Metadata (reserved for future use)
    - 1 byte: Trailer (0xAA)
    """
    nSamp = NRF_SAMPLES_PER_PACKET
    nCh = NRF_N_CHANNELS


    counter = bytearray(data[1:3])

    # Cast the counter to np.int32
    counter = np.asarray(struct.unpack("<H", counter), dtype=np.int32)
    counter = counter.reshape(1, 1)
    
    timestamp = bytearray(data[3:7])
    timestamp = np.asarray(struct.unpack("<I", timestamp), dtype=np.uint32)
    timestamp = timestamp.reshape(1, 1)
    
    dummyData = bytearray(data[7:NRF_PACKET_SIZE-4])

    board_id = data[NRF_PACKET_SIZE-4]
    pulse_cnt = data[NRF_PACKET_SIZE-3]
    reserved = data[NRF_PACKET_SIZE-2]
    header = data[0]
    trailer = data[NRF_PACKET_SIZE-1]
    if trailer != NRF_TAILER:
        raise ValueError(f"Invalid DUMMY trailer: 0x{trailer:02X}, expected 0x{NRF_TAILER:02X}")

    dummyData = dummyData.reshape(nSamp, nCh)
    dummyData = dummyData.astype(np.float32)
    return dummyData, counter, timestamp


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
        - For DUMMY packets: {"dummy": dummy_data, "counter_dummy": dummy_counter}
    """
    packet_len = len(data)
    header = data[0]
    if packet_len == NRF_PACKET_SIZE and header == NRF_HEADER:
        # This is a DUMMY packet
        trailer = data[-1]
        if trailer != NRF_TAILER:
            raise ValueError(f"Invalid DUMMY trailer: 0x{trailer:02X}, expected 0x{NRF_TAILER:02X}")
        dummyData, counter, timestamp = _decode_dummy(data)
        return {"dummy": dummyData, "counter_dummy": counter, "timestamp_dummy": timestamp}
    else:
        raise ValueError(f"Invalid packet: size={packet_len}, header=0x{header:02X}")