# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Standalone EEG interface for BioGAP (nRF5340 + SENSEI_ExGShield, ADS1298 × 2).

Packet layout (211 bytes, EEG_PCKT_SIZE):
  [0]       0x55  header
  [1:3]     counter (uint16 LE)
  [3:7]     timestamp µs (uint32 LE)
  [7:57]    sample 1: ADS_A[0:24] + ADS_B[0:24] + counter_extra + 0x00
  [57:107]  sample 2
  [107:157] sample 3
  [157:207] sample 4
  [207:210] metadata (board_id, pulse_count, reserved)
  [210]     0xAA  trailer

Each ADS block is 8 channels × 3 bytes (big-endian 24-bit 2's complement).
The ADS1298's sample rate, mode and gain are user-configurable via the
gear-icon dialog (see biogapultra_ads.ads_config.AdsConfig); the values used
here at import time are just the defaults, matching what used to be
hardcoded before that dialog existed.
"""

import numpy as np

from biogui.platforms.biogapultra.biogapultra_ads import ads_config
from biogui.platforms.biogapultra.biogapultra_ads.ads_config_widget import (
    AdsConfigWidget,
)
from biogui.platforms.biogapultra.connectivity_commands import (
    START_EEG_STREAMING,
    STOP_EEG_STREAMING,
)
from biogui.platforms.biogapultra.shared_config_dialog import openDialogShell
from biogui.utils import InterfaceModule, PlatformConfig

_N_SAMPLES = 4
_N_CH      = 8        # channels per ADS chip
_BYTES_CH  = 3         # 24-bit
_ADS_BYTES = _N_CH * _BYTES_CH   # 24

# Byte offsets for each sample block (50 bytes each, starting at byte 7)
_SAMPLE_OFFSETS = [7 + i * 50 for i in range(_N_SAMPLES)]

packetSize: int = 211
"""Number of bytes in each BLE packet (EEG_PCKT_SIZE)."""

headerByte: int = 0x55
"""Expected first byte of each packet (NRF_EXG_HEADER) -- used by the TCP
client data source to detect and resync from a misaligned stream."""

tailerByte: int = 0xAA
"""Expected last byte of each packet (NRF_EXG_TAILER) -- see headerByte."""

wifiPacketSize: int = packetSize
"""Number of bytes in each Wi-Fi packet; same size as the BLE packet."""


def _buildStartSeq(ads: ads_config.AdsConfig) -> list[bytes | float]:
    return [
        bytes([START_EEG_STREAMING]) + ads_config.to_bytes(ads),
    ]


def _buildStopSeq() -> list[bytes | float]:
    return [
        bytes([STOP_EEG_STREAMING]),
    ]


def _buildSigInfo(ads: ads_config.AdsConfig) -> dict:
    fs = ads_config.sample_rate_hz(ads)
    return {
        "eeg_A": {
            "fs": fs,
            "nCh": _N_CH,
            "extras": {"type": "time-series", **ads_config.extras_for(ads)},
        },
        "eeg_B": {"fs": fs, "nCh": _N_CH, "extras": {"type": "time-series"}},
        # Packet counter and µs timestamp: one value per BLE packet. Selectable
        # in the signal wizard like eeg_A/eeg_B, but "plotByDefault": False
        # leaves the "Show plot" box unchecked so they are recorded without
        # cluttering the plots unless explicitly enabled.
        "counter": {"fs": fs / _N_SAMPLES, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
        "timestamp": {"fs": fs / _N_SAMPLES, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
    }


def _buildDecodeFn(ads: ads_config.AdsConfig):
    scale = ads_config.scale_uv(ads)

    def decode(data: bytes) -> dict[str, np.ndarray]:
        """Decode one 211-byte EEG packet into ADS_A and ADS_B signal arrays."""
        rows_A = np.empty((_N_SAMPLES, _N_CH), dtype=np.float32)
        rows_B = np.empty((_N_SAMPLES, _N_CH), dtype=np.float32)

        for s, base in enumerate(_SAMPLE_OFFSETS):
            rows_A[s] = ads_config.unpack_ads_channel_block(data, base, scale, _N_CH, _BYTES_CH)
            rows_B[s] = ads_config.unpack_ads_channel_block(data, base + _ADS_BYTES, scale, _N_CH, _BYTES_CH)

        counter = int.from_bytes(data[1:3], "little")
        timestamp = int.from_bytes(data[3:7], "little")

        return {
            "eeg_A":     rows_A,
            "eeg_B":     rows_B,
            "counter":   np.array([[counter]], dtype=np.uint16),
            "timestamp": np.array([[timestamp]], dtype=np.uint32),
        }

    return decode


def _buildModule(ads: ads_config.AdsConfig) -> InterfaceModule:
    return InterfaceModule(
        packetSize=packetSize,
        startSeq=_buildStartSeq(ads),
        stopSeq=_buildStopSeq(),
        sigInfo=_buildSigInfo(ads),
        decodeFn=_buildDecodeFn(ads),
        platformConfig=platformConfig,
        headerByte=headerByte,
        tailerByte=tailerByte,
        wifiPacketSize=wifiPacketSize,
    )


def _configure(parent, interfaceModule: InterfaceModule) -> InterfaceModule | None:
    current = ads_config.settings_from_sig_info(interfaceModule.sigInfo, "eeg_A")
    widget = AdsConfigWidget(parent)
    widget.loadSettings(current)
    if not openDialogShell(parent, [widget], "ADS1298 (EEG) Configuration"):
        return None
    return _buildModule(widget.currentSettings())


platformConfig = PlatformConfig(
    id="eeg_ads",
    configureInterfaceModule=_configure,
    configWidgetClass=AdsConfigWidget,
    hasInlineConfigAction=True,
    inlineActionIconName="preferences-system",
    inlineActionToolTip="Configure ADS1298",
)
"""Opens the ADS1298 settings dialog before acquisition, and from the
source's inline configure action."""

startSeq: list[bytes | float] = _buildStartSeq(ads_config.DEFAULT_CONFIG)
"""Commands to start EEG streaming."""

stopSeq: list[bytes | float] = _buildStopSeq()
"""Commands to stop EEG streaming."""

sigInfo: dict = _buildSigInfo(ads_config.DEFAULT_CONFIG)
"""Signal definitions: two 8-channel EEG streams, plus packet counter and timestamp."""

decodeFn = _buildDecodeFn(ads_config.DEFAULT_CONFIG)
"""Decode one 211-byte EEG packet into ADS_A and ADS_B signal arrays."""
