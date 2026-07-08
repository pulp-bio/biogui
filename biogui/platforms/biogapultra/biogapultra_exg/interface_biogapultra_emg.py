# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Standalone EMG interface for BioGAP (nRF5340 + SENSEI_ExGShield, ADS1298 × 2).

Packet layout identical to EEG (211 bytes, EMG_PCKT_SIZE):
  [0]       0x55  header
  [1:3]     counter (uint16 LE)
  [3:7]     timestamp µs (uint32 LE)
  [7:57]    sample 1: ADS_A[0:24] + ADS_B[0:24] + counter_extra + 0x00
  [57:107]  sample 2
  [107:157] sample 3
  [157:207] sample 4
  [207:210] metadata
  [210]     0xAA  trailer

Firmware default: gain = 6, vRef = 2.5 V.
Only the BLE start/stop commands differ from the EEG interface (37/38 vs 18/19).
"""

import numpy as np

_VREF  = 2.5
_GAIN  = 6
_NBIT  = 24
_SCALE = _VREF / (_GAIN * (2 ** (_NBIT - 1) - 1)) * 1e6  # ADC → µV

_N_SAMPLES = 4
_N_CH      = 8
_BYTES_CH  = 3
_ADS_BYTES = _N_CH * _BYTES_CH

_SAMPLE_OFFSETS = [7 + i * 50 for i in range(_N_SAMPLES)]

packetSize: int = 211

startSeq: list[bytes | float] = [
    bytes([20, 1, 0]),   # SET_BOARD_STATE → STATE_STREAMING_NORDIC
    0.2,
    bytes([37]),         # START_EMG_STREAMING
]

stopSeq: list[bytes | float] = [
    bytes([38]),         # STOP_EMG_STREAMING
]

sigInfo: dict = {
    "emg_A": {"fs": 500.0, "nCh": _N_CH, "extras": {"type": "time-series"}},
    "emg_B": {"fs": 500.0, "nCh": _N_CH, "extras": {"type": "time-series"}},
    # Packet counter and µs timestamp: one value per BLE packet (500 Hz / 4
    # samples = 125 Hz). Selectable in the signal wizard like emg_A/emg_B, but
    # "plotByDefault": False leaves the "Show plot" box unchecked so they are
    # recorded without cluttering the plots unless explicitly enabled.
    "counter": {"fs": 125.0, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
    "timestamp": {"fs": 125.0, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
}


def _unpack_ads_block(data: bytes, offset: int) -> np.ndarray:
    out = np.empty(_N_CH, dtype=np.float32)
    for ch in range(_N_CH):
        b = offset + ch * _BYTES_CH
        raw = (data[b] << 16) | (data[b + 1] << 8) | data[b + 2]
        if raw >= 0x800000:
            raw -= 0x1000000
        out[ch] = raw * _SCALE
    return out


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """Decode one 211-byte EMG packet into ADS_A and ADS_B signal arrays."""
    rows_A = np.empty((_N_SAMPLES, _N_CH), dtype=np.float32)
    rows_B = np.empty((_N_SAMPLES, _N_CH), dtype=np.float32)

    for s, base in enumerate(_SAMPLE_OFFSETS):
        rows_A[s] = _unpack_ads_block(data, base)
        rows_B[s] = _unpack_ads_block(data, base + _ADS_BYTES)

    counter = int.from_bytes(data[1:3], "little")
    timestamp = int.from_bytes(data[3:7], "little")

    return {
        "emg_A":     rows_A,
        "emg_B":     rows_B,
        "counter":   np.array([[counter]], dtype=np.uint16),
        "timestamp": np.array([[timestamp]], dtype=np.uint32),
    }
