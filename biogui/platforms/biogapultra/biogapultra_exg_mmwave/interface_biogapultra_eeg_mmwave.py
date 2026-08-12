# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Combined EEG + mmWave radar interface for BioGAP-Ultra.

Streams the ExG shield (ADS1298 x 2) and the mmWave radar shield
(Infineon BGT60TR13C) simultaneously over one BLE link. The two packet types are
told apart by their header byte:

  0x55, 211 bytes  EEG   -- 4 samples x 2 x 8 channels, 24-bit
  0x60, 244 bytes  radar -- one chunk of a radar frame, 12-bit packed

Both shields sit on SPI_A. The firmware arbitrates the bus with a mutex and
switches it to the radar's SPI mode for the duration of each radar transaction,
restoring the ADS1298's mode afterwards, so the two acquire concurrently. Build
the firmware with ``-DMMWAVE_SHIELD=ON`` for this; a ``-DMMWAVE_ONLY=ON`` image
has no working ExG and will only ever send radar packets.

The onboard PDM microphone is unavailable in any radar build: its CLK and DATA
pins are the radar's RST and IRQ.

EEG packet layout (211 bytes):
  [0]       0x55  header
  [1:3]     counter (uint16 LE)
  [3:7]     timestamp us (uint32 LE)
  [7:57]    sample 1: ADS_A[0:24] + ADS_B[0:24] + counter_extra + 0x00
  [57:107]  sample 2
  [107:157] sample 3
  [157:207] sample 4
  [207:210] metadata (board_id, pulse_count, reserved)
  [210]     0xAA  trailer

Radar packet layout and decoding live in
``biogui.platforms.biogapultra.biogapultra_mmwave.radar``, shared with the
standalone radar interface.
"""

import numpy as np

from biogui.platforms.biogapultra.biogapultra_mmwave import radar
from biogui.platforms.biogapultra.biogapultra_mmwave.radar_config_widget import (
    RadarConfigWidget,
    makeConfigureFn,
)
from biogui.utils import InterfaceModule, PlatformConfig

# =============================================================================
# EEG constants (ADS1298 x 2, gain 6, vRef 2.5 V)
# =============================================================================

_VREF = 2.5  # V
_GAIN = 6  # ADS1298 register 0x00 = gain 6
_NBIT = 24
_SCALE = _VREF / (_GAIN * (2 ** (_NBIT - 1) - 1)) * 1e6  # ADC -> uV

_N_SAMPLES = 4
_N_CH = 8  # channels per ADS chip
_BYTES_CH = 3  # 24-bit
_ADS_BYTES = _N_CH * _BYTES_CH  # 24

_EEG_HEADER = 0x55
_EEG_PACKET_SIZE = 211

# Byte offsets for each sample block (50 bytes each, starting at byte 7)
_SAMPLE_OFFSETS = [7 + i * 50 for i in range(_N_SAMPLES)]

packetSize: list[tuple[int, int]] = [
    (_EEG_HEADER, _EEG_PACKET_SIZE),
    (radar.HEADER_BYTE, radar.PACKET_SIZE),
]
"""Two packet types on one link, selected by the first byte."""

from biogui.platforms.biogapultra.connectivity_commands import START_EEG_STREAMING, STOP_EEG_STREAMING, START_MMWAVE_STREAMING, STOP_MMWAVE_STREAMING
def _buildStartSeq(settings: radar.RadarSettings) -> list[bytes | float]:
    return [
        # Bring the radar up and configure it first. Its register write burst is
        # the heaviest SPI_A traffic either sensor produces, so getting it done
        # before the ADS1298 starts sampling keeps it off the shared bus at a
        # point where ExG would be contending for it.
        *radar.powerOnAndConfigureSeq(settings),
        bytes([START_EEG_STREAMING, 6, 0, 2, 4, 0]),   # START_EEG_STREAMING + 5-byte ADS config]), 
        0.2,
        # Radar streaming last: the ADS1298 is sampling by now, so the bus is
        # shared from this point on.
        bytes([START_MMWAVE_STREAMING]),  # START_MMWAVE_STREAMING
    ]


def _buildStopSeq() -> list[bytes | float]:
    return [
        bytes([STOP_MMWAVE_STREAMING]),  # STOP_MMWAVE_STREAMING
        0.05
        bytes([STOP_EEG_STREAMING]),  # STOP_EEG_STREAMING
        0.05,
        bytes([radar.CMD_TURN_OFF]),  # TURN_OFF_MMWAVE
    ]


def _buildSigInfo(settings: radar.RadarSettings) -> dict:
    return {
        "eeg_A": {"fs": 500.0, "nCh": _N_CH, "extras": {"type": "time-series"}},
        "eeg_B": {"fs": 500.0, "nCh": _N_CH, "extras": {"type": "time-series"}},
        # Packet counter and us timestamp: one value per EEG packet
        # (500 Hz / 4 samples = 125 Hz). "plotByDefault": False records them
        # without cluttering the plots unless explicitly enabled.
        "counter": {"fs": 125.0, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
        "timestamp": {"fs": 125.0, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
        **radar.sigInfoDict(settings),
    }


def _emptyResult() -> dict[str, np.ndarray]:
    """
    "Nothing to report" arrays for every signal.

    decodeFn must return the full key set on every call, whichever packet type
    arrived, and the recording writer locks each signal's dtype to the first
    array it sees -- so these placeholders must match the filled arrays' dtypes.
    """
    return {
        "eeg_A": np.empty((0, _N_CH), dtype=np.float32),
        "eeg_B": np.empty((0, _N_CH), dtype=np.float32),
        "counter": np.empty((0, 1), dtype=np.uint16),
        "timestamp": np.empty((0, 1), dtype=np.uint32),
        **radar.emptyResult(),
    }


def _unpackAdsBlock(data: bytes, offset: int) -> np.ndarray:
    """Unpack one 24-byte ADS block (8 ch x 3 B big-endian signed) -> float32 uV."""
    out = np.empty(_N_CH, dtype=np.float32)
    for ch in range(_N_CH):
        b = offset + ch * _BYTES_CH
        raw = (data[b] << 16) | (data[b + 1] << 8) | data[b + 2]
        if raw >= 0x800000:
            raw -= 0x1000000
        out[ch] = raw * _SCALE
    return out


def _buildDecodeFn(settings: radar.RadarSettings):
    """Fresh radar decoder per settings change, so no unwrap state carries over."""
    decoder = radar.RadarDecoder(settings)

    def decode(data: bytes) -> dict[str, np.ndarray]:
        """
        Decode one packet of either type.

        Parameters
        ----------
        data : bytes
            A single packet, either 211-byte EEG or 244-byte radar.

        Returns
        -------
        dict of {str : ndarray}
            Signal name to data, shape (nSamp, nCh). Signals belonging to the
            other packet type are empty, as are the radar signals on every radar
            packet that is not the last chunk of a frame.
        """
        if not data:
            return _emptyResult()

        header = data[0]

        if header == radar.HEADER_BYTE and len(data) >= radar.PACKET_SIZE:
            result = _emptyResult()
            result.update(decoder.feed(data))
            return result

        if header == _EEG_HEADER and len(data) >= _EEG_PACKET_SIZE:
            result = _emptyResult()

            rowsA = np.empty((_N_SAMPLES, _N_CH), dtype=np.float32)
            rowsB = np.empty((_N_SAMPLES, _N_CH), dtype=np.float32)
            for s, base in enumerate(_SAMPLE_OFFSETS):
                rowsA[s] = _unpackAdsBlock(data, base)
                rowsB[s] = _unpackAdsBlock(data, base + _ADS_BYTES)

            result["eeg_A"] = rowsA
            result["eeg_B"] = rowsB
            result["counter"] = np.array(
                [[int.from_bytes(data[1:3], "little")]], dtype=np.uint16
            )
            result["timestamp"] = np.array(
                [[int.from_bytes(data[3:7], "little")]], dtype=np.uint32
            )
            return result

        return _emptyResult()

    return decode


def _buildModule(settings: radar.RadarSettings) -> InterfaceModule:
    return InterfaceModule(
        packetSize=packetSize,
        startSeq=_buildStartSeq(settings),
        stopSeq=_buildStopSeq(),
        sigInfo=_buildSigInfo(settings),
        decodeFn=_buildDecodeFn(settings),
        platformConfig=platformConfig,
    )


platformConfig = PlatformConfig(
    id="eeg_mmwave",
    configureInterfaceModule=makeConfigureFn(
        "EEG + mmWave Radar Configuration", _buildModule
    ),
    configWidgetClass=RadarConfigWidget,
)
"""Opens the radar settings dialog before acquisition, and from the source's
inline configure action. Only the radar has adjustable settings; the ExG chain is
fixed by the firmware."""

startSeq: list[bytes | float] = _buildStartSeq(radar.DEFAULT_SETTINGS)
"""Commands to configure the radar, start EEG, then start radar streaming."""

stopSeq: list[bytes | float] = _buildStopSeq()
"""Commands to stop radar streaming, stop EEG, then cut the radar's power."""

sigInfo: dict = _buildSigInfo(radar.DEFAULT_SETTINGS)
"""Signal definitions: two 8-channel EEG streams at 500 Hz plus the radar signals."""

decodeFn = _buildDecodeFn(radar.DEFAULT_SETTINGS)
"""Decode one packet of either type."""
