# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Dummy sensor interface for BioGAP-Ultra (nRF5340, sensors/dummy_sensor/dummy_sensor_appl.c).

The dummy sensor is a firmware-side test generator: it produces synthetic data
at a fixed rate through the same transport pathway as a real sensor, so the
NRF <-> host data path can be exercised without any ADS1298/mic/IMU hardware
attached. Enable it with CONFIG_DUMMY_SENSOR=y in the firmware build.

Packet layout (211 bytes, matches DUMMY_SENSOR_PCKT_SIZE for EMULATE_EXG_DATA):
  [0]       0x55  header
  [1:3]     counter (uint16 LE)
  [3:7]     timestamp us (uint32 LE)
  [7:207]   payload: 4 samples x 50 bytes
  [207:210] metadata (board_id, sync_pulse_count, reserved)
  [210]     0xAA  trailer

Each 50-byte sample is a raw ramp (sample[i] = (sample_index * 50 + i) & 0xFF,
see fill_dummy_exg_sample()) with no physical meaning - it is only useful to
confirm that the pipeline (counter continuity, timestamps, framing) is intact
end to end, not for signal analysis.

Start/stop opcodes (243/244) are deliberately NOT 249/250/251: those collide
with sensors/wulpus/wulpus_appl.c's protocol-internal 0xFA/0xFB config markers
(see core/connectivity_commands.h). Must stay in sync with the firmware.
"""

import numpy as np

_N_SAMPLES = 4
_N_CH = 50  # raw bytes per sample, exposed as pseudo-channels

packetSize: int = 211
"""Number of bytes in each packet (DUMMY_SENSOR_PCKT_SIZE)."""

startSeq: list[bytes | float] = [
    bytes([243]),           # START_DUMMY_STREAMING
    0.2,
    bytes([238]),           # CMD_SENT            0xEE
]
"""Commands to start dummy-sensor streaming."""

stopSeq: list[bytes | float] = [
    bytes([244]),  # STOP_DUMMY_STREAMING
]
"""Commands to stop dummy-sensor streaming."""

sigInfo: dict = {
    "dummy": {"fs": 10.0, "nCh": _N_CH, "extras": {"type": "time-series"}},
    # Packet counter and us timestamp: one value per packet (10 Hz / 4
    # samples = 2.5 Hz). "plotByDefault": False leaves the "Show plot" box
    # unchecked so they are recorded without cluttering the plots unless
    # explicitly enabled.
    "counter": {"fs": 2.5, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
    "timestamp": {"fs": 2.5, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}},
}
"""Signal definitions: one 50-channel synthetic ramp at 10 Hz, plus packet counter and timestamp."""


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """Decode one 211-byte dummy-sensor packet."""
    counter = int.from_bytes(data[1:3], "little")
    timestamp = int.from_bytes(data[3:7], "little")
    payload = np.frombuffer(data[7:207], dtype=np.uint8).reshape(_N_SAMPLES, _N_CH).astype(np.float32)

    return {
        "dummy": payload,
        "counter": np.array([[counter]], dtype=np.uint16),
        "timestamp": np.array([[timestamp]], dtype=np.uint32),
    }
