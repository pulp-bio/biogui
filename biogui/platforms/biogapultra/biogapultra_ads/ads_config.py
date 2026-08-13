# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Configuration for the ADS1298  (see Firmware/src_NRF/afe/ads_spi_config.c
for the register tables this mirrors).

Every EEG/EMG start command must is followed by a 5-byte config:
``[sample_rate, ads_mode, ch2_function, ch4_function, gain]``. 
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

# =============================================================================
# Register tables
# =============================================================================

SAMPLE_RATE_OPTIONS: dict[int, str] = {
    4: "2 kHz",
    5: "1 kHz",
    6: "0.5 kHz",
}
"""Data-rate register byte -> display label. Capped at 2 kHz (tested stable in FW); 
the ADS also has registers for 4/8/16/32 kHz, not exposed here."""

SAMPLE_RATE_HZ: dict[int, float] = {
    4: 2000.0,
    5: 1000.0,
    6: 500.0,
}
"""Data-rate register byte -> actual per-channel sampling rate, in Hz."""

ADS_MODE_OPTIONS: dict[int, str] = {
    0: "Normal",
    5: "Test signal (square wave)",
    1: "Shorted (noise measurement)",
}
"""ADS1298 mode register byte -> display label."""

GAIN_OPTIONS: dict[int, str] = {
    16: "1",
    32: "2",
    48: "3",
    64: "4",
    0: "6",
    80: "8",
    96: "12",
}
"""PGA gain register byte -> physical gain multiplier label. Non-linear
lookup table, not a formula, per the firmware's register map."""

GAIN_MULTIPLIER: dict[int, float] = {
    16: 1.0,
    32: 2.0,
    48: 3.0,
    64: 4.0,
    0: 6.0,
    80: 8.0,
    96: 12.0,
}
"""PGA gain register byte -> numeric multiplier, for the ADC-to-uV scale."""

TEST_SIGNAL_MODE = 5
"""ads_mode value that switches the ADS1298 to its internal test square wave."""

TEST_SIGNAL_FORCED_GAIN = 16
"""Gain the firmware requires (0x10) whenever TEST_SIGNAL_MODE is selected."""

CH2_FUNCTION = 2
CH4_FUNCTION = 4
"""Channel-2/channel-4 function bytes. Fixed for now, not user-configurable."""

_VREF = 2.5  # V
_NBIT = 24

_EXTRAS_KEY = "ads_config"


@dataclass(frozen=True)
class AdsConfig:
    """
    Runtime-adjustable ADS1298 settings, sent to the firmware as the 5-byte
    config that must accompany every START_E[X]G_STREAMING command.
    """

    sample_rate: int = 6
    """Data-rate register byte, see SAMPLE_RATE_OPTIONS. Default 0.5 kHz."""

    ads_mode: int = 0
    """ADS1298 mode register byte, see ADS_MODE_OPTIONS. Default Normal."""

    gain: int = 0
    """PGA gain register byte, see GAIN_OPTIONS. Default gain 6x."""

    def validated(self) -> "AdsConfig":
        """Fall back to the default for any field not in its option table;
        force the gain the test-signal mode requires."""
        sample_rate = self.sample_rate if self.sample_rate in SAMPLE_RATE_OPTIONS else DEFAULT_CONFIG.sample_rate
        ads_mode = self.ads_mode if self.ads_mode in ADS_MODE_OPTIONS else DEFAULT_CONFIG.ads_mode
        gain = self.gain if self.gain in GAIN_OPTIONS else DEFAULT_CONFIG.gain
        if ads_mode == TEST_SIGNAL_MODE:
            gain = TEST_SIGNAL_FORCED_GAIN
        return replace(self, sample_rate=sample_rate, ads_mode=ads_mode, gain=gain)


DEFAULT_CONFIG = AdsConfig()
"""0.5 kHz / Normal / gain 6x"""


def to_bytes(config: AdsConfig) -> bytes:
    """Encode as the 5-byte config that follows a START_E[X]G_STREAMING opcode."""
    c = config.validated()
    return bytes([c.sample_rate, c.ads_mode, CH2_FUNCTION, CH4_FUNCTION, c.gain])


def sample_rate_hz(config: AdsConfig) -> float:
    """Per-channel sampling rate, in Hz, for the chosen data-rate register."""
    return SAMPLE_RATE_HZ[config.validated().sample_rate]


def scale_uv(config: AdsConfig, vref: float = _VREF, nbit: int = _NBIT) -> float:
    """ADC code -> microvolt scale factor for the chosen gain."""
    gain = GAIN_MULTIPLIER[config.validated().gain]
    return vref / (gain * (2 ** (nbit - 1) - 1)) * 1e6


def extras_for(config: AdsConfig) -> dict:
    """Extras entry to merge into a signal's ``extras`` dict, so the dialog
    can recover the settings a module was built with (mirrors
    ``radar.sigInfoDict``'s use of ``extras`` for the same purpose)."""
    c = config.validated()
    return {_EXTRAS_KEY: {"sample_rate": c.sample_rate, "ads_mode": c.ads_mode, "gain": c.gain}}


def settings_from_sig_info(sigInfo: dict, signal_name: str) -> AdsConfig:
    """Recover the settings a module was built with, for prefilling the
    dialog. Falls back to defaults for anything missing."""
    extras = sigInfo.get(signal_name, {}).get("extras", {}).get(_EXTRAS_KEY, {})
    return AdsConfig(
        sample_rate=int(extras.get("sample_rate", DEFAULT_CONFIG.sample_rate)),
        ads_mode=int(extras.get("ads_mode", DEFAULT_CONFIG.ads_mode)),
        gain=int(extras.get("gain", DEFAULT_CONFIG.gain)),
    ).validated()


def unpack_ads_channel_block(
    data: bytes, offset: int, scale: float, n_ch: int, bytes_ch: int
) -> np.ndarray:
    """Unpack one ``n_ch`` x ``bytes_ch`` big-endian signed ADS block into a
    float32 array in physical units, given the ADC-to-uV ``scale`` for the
    channel's current gain."""
    out = np.empty(n_ch, dtype=np.float32)
    for ch in range(n_ch):
        b = offset + ch * bytes_ch
        raw = (data[b] << 16) | (data[b + 1] << 8) | data[b + 2]
        if raw >= 0x800000:
            raw -= 0x1000000
        out[ch] = raw * scale
    return out


HELP: dict[str, str] = {
    "sample_rate": "Sampling rate for each ADS cannel",
    "ads_mode": "Sets the mode of operation of the ADS. "
    "Normal: normal operation"
    "Test signal: generates an internal square wave, used for functional checks"
    "Shorted: ties the inputs together, used fornoise-floor measurement.",
    "gain": "Analog front-end gain.",
}
