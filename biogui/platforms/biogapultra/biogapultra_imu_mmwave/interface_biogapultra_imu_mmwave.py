# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Combined IMU + mmWave radar interface for BioGAP-Ultra.

Streams the onboard LSM6DSV16BX 6-axis IMU and the mmWave radar shield
(Infineon BGT60TR13C) simultaneously over one BLE link. The two packet types are
told apart by their header byte:

  0x56, 236 bytes  IMU   -- 19 samples x (3 acc + 3 gyro), int16 BE
  0x60, 244 bytes  radar -- one chunk of a radar frame, 12-bit packed

Unlike the ExG + radar combination, these two sensors do not contend for a bus:
the IMU sits on I2C_B while the radar has SPI_A, so neither adds latency to the
other. That makes this pairing the cheaper way to get motion context alongside
radar -- useful for telling genuine chest-wall motion from whole-body movement
when the radar is used for pulse sensing.

IMU packet layout (236 bytes):
  [0]       0x56  header
  [1:3]     counter (uint16 LE)
  [3:7]     timestamp us (uint32 LE)
  [7:235]   19 samples x 12 bytes:
              acc  X, Y, Z (int16 BE each)
              gyro X, Y, Z (int16 BE each)
  [235]     0x57  trailer

Firmware configuration (sensors/imu/lsm6dsv16bx_sensor.c):
  ODR 480 Hz (accel + gyro), accel FS +-8 g (0.244 mg/LSB),
  gyro FS +-2000 dps (70 mdps/LSB).

Radar packet layout and decoding live in
``biogui.platforms.biogapultra.biogapultra_mmwave.radar``, shared with the
standalone radar interface and the ExG + radar one.

Build the firmware with CONFIG_SENSOR_MMWAVE=y in prj.conf. A -DMMWAVE_ONLY=ON
image also works for this pairing -- the IMU is unaffected by that variant, since
only the SPI_A transport changes.
"""

import numpy as np

from biogui.platforms.biogapultra.biogapultra_mmwave import radar
from biogui.platforms.biogapultra.biogapultra_mmwave.radar_config_widget import (
    RadarConfigWidget,
    makeConfigureFn,
)
from biogui.utils import InterfaceModule, PlatformConfig

# =============================================================================
# IMU constants (LSM6DSV16BX)
# =============================================================================

_FS = 480.0  # Hz, LSM6DSV16BX ODR (accel and gyro)
_N_SAMPLES = 19  # samples per BLE packet
_N_CH = 3  # channels per signal (X, Y, Z)
_PACKET_RATE = _FS / _N_SAMPLES  # ~25.3 packets/s

_ACC_SCALE = 0.244  # mg/LSB at +-8 g (lsm6dsv16bx_from_fs8_to_mg)
_GYRO_SCALE = 0.070  # dps/LSB at +-2000 dps (lsm6dsv16bx_from_fs2000_to_mdps / 1000)

_IMU_HEADER = 0x56
_IMU_PACKET_SIZE = 236

packetSize: list[tuple[int, int]] = [
    (_IMU_HEADER, _IMU_PACKET_SIZE),
    (radar.HEADER_BYTE, radar.PACKET_SIZE),
]
"""Two packet types on one link, selected by the first byte."""

def _buildStartSeq(settings: radar.RadarSettings) -> list[bytes | float]:
    return [
        bytes([20, 1, 0]),  # SET_BOARD_STATE -> STATE_STREAMING_NORDIC
        0.2,
        # Radar first: powering and configuring it is a burst of SPI traffic, and
        # doing it before anything else streams keeps the two start-ups from
        # overlapping. The IMU is on I2C, so this is tidiness rather than need.
        *radar.powerOnAndConfigureSeq(settings),
        bytes([33]),  # START_IMU_STREAMING
        0.1,
        bytes([radar.CMD_START]),  # START_MMWAVE_STREAMING
    ]


def _buildStopSeq() -> list[bytes | float]:
    return [
        bytes([radar.CMD_STOP]),  # STOP_MMWAVE_STREAMING
        0.05,
        bytes([34]),  # STOP_IMU_STREAMING
        0.05,
        bytes([radar.CMD_TURN_OFF]),  # TURN_OFF_MMWAVE
    ]


def _buildSigInfo(settings: radar.RadarSettings) -> dict:
    return {
        "acc": {"fs": _FS, "nCh": _N_CH, "extras": {"type": "time-series"}},
        "gyro": {"fs": _FS, "nCh": _N_CH, "extras": {"type": "time-series"}},
        # Packet counter and us timestamp: one value per IMU packet (~25.3 Hz).
        # "plotByDefault": False records them without cluttering the plots unless
        # explicitly enabled.
        "counter": {"fs": _PACKET_RATE, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
        "timestamp": {"fs": _PACKET_RATE, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
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
        "acc": np.empty((0, _N_CH), dtype=np.float32),
        "gyro": np.empty((0, _N_CH), dtype=np.float32),
        "counter": np.empty((0, 1), dtype=np.uint16),
        "timestamp": np.empty((0, 1), dtype=np.uint32),
        **radar.emptyResult(),
    }


def _buildDecodeFn(settings: radar.RadarSettings):
    """Fresh radar decoder per settings change, so no unwrap state carries over."""
    decoder = radar.RadarDecoder(settings)

    def decode(data: bytes) -> dict[str, np.ndarray]:
        """
        Decode one packet of either type.

        Parameters
        ----------
        data : bytes
            A single packet, either 236-byte IMU or 244-byte radar.

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

        if header == _IMU_HEADER and len(data) >= _IMU_PACKET_SIZE:
            result = _emptyResult()

            # 19 samples x 6 int16 BE values: [ax, ay, az, gx, gy, gz]
            raw = (
                np.frombuffer(data, dtype=">i2", count=_N_SAMPLES * 2 * _N_CH, offset=7)
                .reshape(_N_SAMPLES, 2 * _N_CH)
                .astype(np.float32)
            )

            result["acc"] = raw[:, :_N_CH] * _ACC_SCALE  # mg
            result["gyro"] = raw[:, _N_CH:] * _GYRO_SCALE  # dps
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
    id="imu_mmwave",
    configureInterfaceModule=makeConfigureFn(
        "IMU + mmWave Radar Configuration", _buildModule
    ),
    configWidgetClass=RadarConfigWidget,
)
"""Opens the radar settings dialog before acquisition, and from the source's
inline configure action. Only the radar has adjustable settings; the IMU's ODR and
full-scale ranges are fixed by the firmware."""

startSeq: list[bytes | float] = _buildStartSeq(radar.DEFAULT_SETTINGS)
"""Commands to configure the radar, start the IMU, then start radar streaming."""

stopSeq: list[bytes | float] = _buildStopSeq()
"""Commands to stop radar streaming, stop the IMU, then cut the radar's power."""

sigInfo: dict = _buildSigInfo(radar.DEFAULT_SETTINGS)
"""Signal definitions: 3-channel accelerometer (mg) and gyroscope (dps) at 480 Hz,
plus the radar signals."""

decodeFn = _buildDecodeFn(radar.DEFAULT_SETTINGS)
"""Decode one packet of either type."""
