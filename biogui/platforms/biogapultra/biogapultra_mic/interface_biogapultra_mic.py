# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Standalone microphone interface for BioGAP-Ultra (nRF5340, PDM audio).

Single-channel PDM microphone, 16 kHz, 16-bit PCM, 64 samples per BLE packet.

Packet layout (136 bytes, MIC_PCKT_SIZE):
  [0]       0xAA  header
  [1:3]     counter (uint16 LE)
  [3:7]     timestamp µs (uint32 LE)
  [7:135]   64 PCM samples × 2 bytes (int16 LE each)
  [135]     0x55  trailer

Audio is normalized to float32 in [-1.0, 1.0). See
``src_NRF/BLE_PACKET_STRUCTURE.md`` for the authoritative packet reference.
"""

import numpy as np

_MIC_FS          = 16000.0                # Hz, mono
_MIC_SAMPLES     = 64                     # PCM samples per BLE packet
_MIC_DATA_OFF    = 7                      # first PCM byte
_MIC_PACKET_RATE = _MIC_FS / _MIC_SAMPLES  # 250 packets/s

packetSize: int = 136
"""Number of bytes in each BLE packet (MIC_PCKT_SIZE)."""

startSeq: list[bytes | float] = [
    bytes([20, 1, 0]),   # SET_BOARD_STATE → STATE_STREAMING_NORDIC
    0.2,
    bytes([26]),         # START_MIC_STREAMING
]
"""Commands to start microphone streaming."""

stopSeq: list[bytes | float] = [
    bytes([27]),         # STOP_MIC_STREAMING
]
"""Commands to stop microphone streaming."""

sigInfo: dict = {
    "mic": {"fs": _MIC_FS, "nCh": 1, "extras": {"type": "time-series"}},
    # Packet counter and µs timestamp: one value per BLE packet (250 Hz).
    # Selectable in the signal wizard like mic, but "plotByDefault": False leaves
    # the "Show plot" box unchecked so they are recorded without cluttering the
    # plots unless explicitly enabled.
    "counter":   {"fs": _MIC_PACKET_RATE, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
    "timestamp": {"fs": _MIC_PACKET_RATE, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
}
"""Signal definitions: mono microphone (normalized float) at 16 kHz, plus packet
counter and timestamp."""


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """Decode one 136-byte microphone packet into a normalized audio array."""
    audio = np.frombuffer(
        data, dtype="<i2", count=_MIC_SAMPLES, offset=_MIC_DATA_OFF
    ).astype(np.float32) / 32768.0

    counter = int.from_bytes(data[1:3], "little")
    timestamp = int.from_bytes(data[3:7], "little")

    return {
        "mic":       audio.reshape(-1, 1),
        "counter":   np.array([[counter]], dtype=np.uint16),
        "timestamp": np.array([[timestamp]], dtype=np.uint32),
    }
