# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Interface for the BioGAP-Ultra mmWave radar shield (Infineon BGT60TR13C), alone.

The radar streams raw ADC frames; the firmware sends each frame split over
several BLE packets, in the radar's native 12-bit packing:

  [0]        0x60  header
  [1:5]      frame timestamp, microseconds, big endian.
             Bit 0 carries the external sync level and is masked out of the
             timestamp, so every chunk of one frame shares the same value.
  [5]        chunk index, 0-based
  [6]        total number of chunks in this frame
  [7:243]    payload, zero padded in the last chunk
  [243]      0x61  trailer

With the default firmware profile (32 chirps x 8 samples, 1 RX antenna) one frame
is 256 samples = 384 packed bytes = 2 packets, so at 100 fps the link carries 200
packets/s.

Signals:

- ``mmwave_phase`` -- the pulse waveform: unwrapped phase of the selected range
  bin, one sample per frame. This is the measurement. It is not detrended, so
  apply a bandpass (roughly 0.5-20 Hz) in the signal configuration to see the
  arterial pulse rather than posture drift.
- ``mmwave_amp`` -- the same bin's magnitude in dB, one sample per frame:
  ``20*log10`` of the chirp-averaged complex spectrum at ``rangeBin``, floored at
  ``radar.AMP_FLOOR_DB``. Plotted by default alongside the phase, because it is
  what says whether there was a target to believe -- a phase excursion during an
  amplitude dropout is an artefact, not motion. Real values run from roughly 0 dB
  (noise only) to 72 dB (full-scale return).
- ``mmwave_phase_bins`` -- every range bin's unwrapped phase, so a different bin
  can be chosen afterwards without re-recording.
- ``mmwave_raw`` -- the ADC samples in frame order, typed ``"radar"`` for the
  range-time heatmap. Shows where energy returns and how strongly; it will not
  show the pulse, because 100 um of motion changes phase measurably but magnitude
  negligibly. Use it to check sensor placement and pick a range bin.
- ``mmwave_level`` -- per-frame ADC min/max. The only way to see IF gain clipping.

Frame geometry, packet layout, decoding and the settings dialog live in
``biogui.platforms.biogapultra.biogapultra_mmwave``, shared with the combined
ExG + radar and IMU + radar interfaces.

Use this with a radar-only firmware image (``-DMMWAVE_ONLY=ON``) or with the
combined image when only radar data is wanted. To stream ExG or the IMU at the
same time, use ``biogapultra_eeg_mmwave`` or ``biogapultra_imu_mmwave``.
"""

import numpy as np

from biogui.platforms.biogapultra.biogapultra_mmwave import radar
from biogui.platforms.biogapultra.biogapultra_mmwave.radar_config_widget import (
    RadarConfigWidget,
    makeConfigureFn,
)
from biogui.utils import InterfaceModule, PlatformConfig

packetSize: int = radar.PACKET_SIZE
"""Number of bytes in each packet."""

headerByte: int = radar.HEADER_BYTE
"""First byte of each packet (MMWAVE_DATA_HEADER)."""

tailerByte: int = radar.TRAILER_BYTE
"""Last byte of each packet (MMWAVE_DATA_TRAILER)."""


def _buildStartSeq(settings: radar.RadarSettings) -> list[bytes | float]:
    return [
        bytes([20, 1, 0]),  # SET_BOARD_STATE -> STATE_STREAMING_NORDIC
        0.2,
        *radar.powerOnAndConfigureSeq(settings),
        bytes([radar.CMD_START]),  # START_MMWAVE_STREAMING
    ]


def _buildDecodeFn(settings: radar.RadarSettings):
    """Fresh decoder per settings change, so no unwrap state carries over."""
    decoder = radar.RadarDecoder(settings)

    def decode(data: bytes) -> dict[str, np.ndarray]:
        return decoder.feed(data)

    return decode


def _buildModule(settings: radar.RadarSettings) -> InterfaceModule:
    return InterfaceModule(
        packetSize=radar.PACKET_SIZE,
        startSeq=_buildStartSeq(settings),
        stopSeq=radar.stopAndPowerOffSeq(),
        sigInfo=radar.sigInfoDict(settings),
        decodeFn=_buildDecodeFn(settings),
        headerByte=radar.HEADER_BYTE,
        tailerByte=radar.TRAILER_BYTE,
        platformConfig=platformConfig,
    )


platformConfig = PlatformConfig(
    id="mmwave",
    configureInterfaceModule=makeConfigureFn(
        "mmWave Radar Configuration", _buildModule
    ),
    configWidgetClass=RadarConfigWidget,
)
"""Opens the radar settings dialog before acquisition, and from the source's
inline configure action."""

startSeq: list[bytes | float] = _buildStartSeq(radar.DEFAULT_SETTINGS)
"""Commands to power, configure and start the radar."""

stopSeq: list[bytes | float] = radar.stopAndPowerOffSeq()
"""Commands to stop the radar and cut its power."""

sigInfo: dict = radar.sigInfoDict(radar.DEFAULT_SETTINGS)
"""Signal definitions: the pulse waveform, every bin's phase, raw frames and
per-frame ADC level."""

decodeFn = _buildDecodeFn(radar.DEFAULT_SETTINGS)
"""Reassemble radar frames from BLE packets and decode them."""
