# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Standalone IMU interface for BioGAP-Ultra (nRF5340 + LSM6DSV16BX 6-axis IMU).

Packet layout (236 bytes, IMU_PCKT_SIZE):
  [0]       0x56  header
  [1:3]     counter (uint16 LE)
  [3:7]     timestamp µs (uint32 LE)
  [7:235]   19 samples × 12 bytes:
              acc  X, Y, Z (int16 BE each)
              gyro X, Y, Z (int16 BE each)
  [235]     0x57  trailer

Firmware configuration (sensors/imu/lsm6dsv16bx_sensor.c):
  ODR 480 Hz (accel + gyro), accel FS ±8 g (0.244 mg/LSB),
  gyro FS ±2000 dps (70 mdps/LSB).
"""

import numpy as np

_FS = 480.0           # Hz, LSM6DSV16BX ODR (accel and gyro)
_N_SAMPLES = 19       # samples per BLE packet
_N_CH = 3             # channels per signal (X, Y, Z)
_PACKET_RATE = _FS / _N_SAMPLES  # ~25.3 packets/s

_ACC_SCALE = 0.244    # mg/LSB at ±8 g (lsm6dsv16bx_from_fs8_to_mg)
_GYRO_SCALE = 0.070   # dps/LSB at ±2000 dps (lsm6dsv16bx_from_fs2000_to_mdps / 1000)

packetSize: int = 236
"""Number of bytes in each BLE packet (IMU_PCKT_SIZE)."""

startSeq: list[bytes | float] = [
    bytes([20, 1, 0]),   # SET_BOARD_STATE → STATE_STREAMING_NORDIC
    0.2,
    bytes([33]),         # START_IMU_STREAMING
]
"""Commands to start IMU streaming."""

stopSeq: list[bytes | float] = [
    bytes([34]),         # STOP_IMU_STREAMING
]
"""Commands to stop IMU streaming."""

sigInfo: dict = {
    "acc":  {"fs": _FS, "nCh": _N_CH, "extras": {"type": "time-series"}},
    "gyro": {"fs": _FS, "nCh": _N_CH, "extras": {"type": "time-series"}},
    # Packet counter and µs timestamp: one value per BLE packet (~25.3 Hz).
    # Selectable in the signal wizard like acc/gyro, but "plotByDefault": False
    # leaves the "Show plot" box unchecked so they are recorded without
    # cluttering the plots unless explicitly enabled.
    "counter": {"fs": _PACKET_RATE, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
    "timestamp": {"fs": _PACKET_RATE, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
}
"""Signal definitions: 3-channel accelerometer (mg) and gyroscope (dps) at 480 Hz,
plus packet counter and timestamp."""


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """Decode one 236-byte IMU packet into accelerometer and gyroscope arrays."""
    # 19 samples × 6 int16 BE values: [ax, ay, az, gx, gy, gz]
    raw = (
        np.frombuffer(data, dtype=">i2", count=_N_SAMPLES * 2 * _N_CH, offset=7)
        .reshape(_N_SAMPLES, 2 * _N_CH)
        .astype(np.float32)
    )
    acc = raw[:, :_N_CH] * _ACC_SCALE    # mg
    gyro = raw[:, _N_CH:] * _GYRO_SCALE  # dps

    counter = int.from_bytes(data[1:3], "little")
    timestamp = int.from_bytes(data[3:7], "little")

    return {
        "acc":       acc,
        "gyro":      gyro,
        "counter":   np.array([[counter]], dtype=np.uint16),
        "timestamp": np.array([[timestamp]], dtype=np.uint32),
    }
