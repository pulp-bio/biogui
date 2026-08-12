# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Combined EEG (ADS1298 × 2) + microphone (PDM) interface for BioGAP-Ultra (nRF5340).

Both sensors stream simultaneously over a single BLE NUS connection; the two
packet types are demultiplexed by their header byte / total length (the data
source frames packets from the ``packetSize`` list of (header, size) tuples):

  0x55 → EEG packet (211 bytes)   ── 4 samples × 16 channels
  0xAA → MIC packet (136 bytes)   ── 64 PCM samples, 16 kHz mono

EEG packet layout (211 bytes, EXG_PCK_LNGTH):
  [0]       0x55  header
  [1:3]     counter (uint16 LE)
  [3:7]     timestamp µs (uint32 LE)
  [7:57]    sample 1: ADS_A[0:24] + ADS_B[0:24] + counter_extra + 0x00
  [57:107]  sample 2
  [107:157] sample 3
  [157:207] sample 4
  [207:210] metadata (board_id, sync_pulse_count, reserved)
  [210]     0xAA  trailer

MIC packet layout (136 bytes, MIC_PCKT_SIZE):
  [0]       0xAA  header
  [1:3]     counter (uint16 LE)
  [3:7]     timestamp µs (uint32 LE)
  [7:135]   64 PCM samples × 2 bytes (int16 LE each)
  [135]     0x55  trailer

Each ADS block is 8 channels × 3 bytes (big-endian 24-bit 2's complement).
Firmware default: gain = 6, vRef = 2.5 V.

Streaming uses the firmware's synced combined command (START_EEG_MIC_STREAMING,
35), which arms a 2-subsystem sync barrier so EEG and MIC start together.
See ``src_NRF/BLE_PACKET_STRUCTURE.md`` for the authoritative packet reference.
"""

import numpy as np

from biogui.platforms.biogapultra.connectivity_commands import (
    START_EEG_MIC_STREAMING,
    STOP_EEG_MIC_STREAMING,
)

# ── ExG (ADS1298) decode constants ─────────────────────────────────────────
_VREF  = 2.5          # V
_GAIN  = 6            # ADS1298 register 0x00 = gain 6
_NBIT  = 24
_SCALE = _VREF / (_GAIN * (2 ** (_NBIT - 1) - 1)) * 1e6  # ADC → µV

_N_SAMPLES = 4        # ExG samples per BLE packet
_N_CH      = 8        # channels per ADS chip
_BYTES_CH  = 3        # 24-bit
_ADS_BYTES = _N_CH * _BYTES_CH   # 24

# Byte offset of each 50-byte sample block, starting at byte 7.
_SAMPLE_OFFSETS = [7 + i * 50 for i in range(_N_SAMPLES)]

_EEG_FS          = 500.0                  # Hz, per channel
_EEG_PACKET_RATE = _EEG_FS / _N_SAMPLES   # 125 packets/s

# ── Microphone (PDM) decode constants ──────────────────────────────────────
_MIC_FS          = 16000.0                # Hz, mono
_MIC_SAMPLES     = 64                     # PCM samples per BLE packet
_MIC_DATA_OFF    = 7                      # first PCM byte
_MIC_PACKET_RATE = _MIC_FS / _MIC_SAMPLES  # 250 packets/s

# ── BLE framing constants ──────────────────────────────────────────────────
_EEG_HEADER      = 0x55
_EEG_PACKET_SIZE = 211
_MIC_HEADER      = 0xAA
_MIC_PACKET_SIZE = 136

packetSize: list[tuple[int, int]] = [
    (_EEG_HEADER, _EEG_PACKET_SIZE),
    (_MIC_HEADER, _MIC_PACKET_SIZE),
]
"""List of (header_byte, packet_size) tuples: EEG (0x55, 211) and MIC (0xAA, 136)."""

startSeq: list[bytes | float] = [
    bytes([START_EEG_MIC_STREAMING, 6, 0, 2, 4, 0]),   # + 5-byte ADS config (synced EEG + MIC)
]
"""Commands to start synced EEG + microphone streaming."""

stopSeq: list[bytes | float] = [
    bytes([STOP_EEG_MIC_STREAMING]),
]
"""Commands to stop EEG + microphone streaming."""

sigInfo: dict = {
    "eeg_A": {"fs": _EEG_FS, "nCh": _N_CH, "extras": {"type": "time-series"}},
    "eeg_B": {"fs": _EEG_FS, "nCh": _N_CH, "extras": {"type": "time-series"}},
    "mic":   {"fs": _MIC_FS, "nCh": 1, "extras": {"type": "time-series"}},
    # Per-packet counters and µs timestamps: one value per BLE packet. Selectable
    # in the signal wizard, but "plotByDefault": False leaves the "Show plot" box
    # unchecked so they are recorded without cluttering the plots.
    "eeg_counter":   {"fs": _EEG_PACKET_RATE, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
    "eeg_timestamp": {"fs": _EEG_PACKET_RATE, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
    "mic_counter":   {"fs": _MIC_PACKET_RATE, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
    "mic_timestamp": {"fs": _MIC_PACKET_RATE, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
}
"""Signal definitions: two 8-channel EEG streams (µV) at 500 Hz, mono microphone
(normalized float) at 16 kHz, plus per-sensor packet counters and timestamps."""


def _unpack_ads_block(data: bytes, offset: int) -> np.ndarray:
    """Unpack one 24-byte ADS block (8 ch × 3 B big-endian signed) → float32 µV."""
    out = np.empty(_N_CH, dtype=np.float32)
    for ch in range(_N_CH):
        b = offset + ch * _BYTES_CH
        raw = (data[b] << 16) | (data[b + 1] << 8) | data[b + 2]
        if raw >= 0x800000:
            raw -= 0x1000000
        out[ch] = raw * _SCALE
    return out


def _empty_result() -> dict[str, np.ndarray]:
    """Empty placeholder for every signal (the preprocessor skips 0-length arrays).

    Placeholders must share the dtype of the filled arrays: the file writer
    captures each signal's dtype from the first array it sees.
    """
    return {
        "eeg_A":         np.empty((0, _N_CH), dtype=np.float32),
        "eeg_B":         np.empty((0, _N_CH), dtype=np.float32),
        "mic":           np.empty((0, 1), dtype=np.float32),
        "eeg_counter":   np.empty((0, 1), dtype=np.uint16),
        "eeg_timestamp": np.empty((0, 1), dtype=np.uint32),
        "mic_counter":   np.empty((0, 1), dtype=np.uint16),
        "mic_timestamp": np.empty((0, 1), dtype=np.uint32),
    }


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """
    Decode one BLE packet from the combined EEG + MIC stream.

    Header 0x55 (211 B) → EEG packet: fills eeg_A, eeg_B, eeg_counter, eeg_timestamp.
    Header 0xAA (136 B) → MIC packet: fills mic, mic_counter, mic_timestamp.

    Returns a dict keyed by every signal in ``sigInfo``; the signals not carried
    by this packet are left as empty (0-length) arrays.
    """
    result = _empty_result()
    header = data[0]

    if header == _EEG_HEADER:
        rows_A = np.empty((_N_SAMPLES, _N_CH), dtype=np.float32)
        rows_B = np.empty((_N_SAMPLES, _N_CH), dtype=np.float32)
        for s, base in enumerate(_SAMPLE_OFFSETS):
            rows_A[s] = _unpack_ads_block(data, base)
            rows_B[s] = _unpack_ads_block(data, base + _ADS_BYTES)
        result["eeg_A"]         = rows_A
        result["eeg_B"]         = rows_B
        result["eeg_counter"]   = np.array([[int.from_bytes(data[1:3], "little")]], dtype=np.uint16)
        result["eeg_timestamp"] = np.array([[int.from_bytes(data[3:7], "little")]], dtype=np.uint32)
        return result

    if header == _MIC_HEADER:
        audio = np.frombuffer(
            data, dtype="<i2", count=_MIC_SAMPLES, offset=_MIC_DATA_OFF
        ).astype(np.float32) / 32768.0
        result["mic"]           = audio.reshape(-1, 1)
        result["mic_counter"]   = np.array([[int.from_bytes(data[1:3], "little")]], dtype=np.uint16)
        result["mic_timestamp"] = np.array([[int.from_bytes(data[3:7], "little")]], dtype=np.uint32)
        return result

    # Unknown header: return empty placeholders (the source framing should
    # never deliver a packet whose first byte is not 0x55 or 0xAA).
    return result
