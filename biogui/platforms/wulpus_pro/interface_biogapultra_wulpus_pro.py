# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
WULPUS interface for ultrasound (default framing: START then newline,
4-byte header, payload).

Shared helpers live in biogui.platforms.wulpus_pro.runtime.
"""

import logging

import numpy as np

from biogui.platforms.wulpus_pro import WULPUS_PLATFORM
from biogui.platforms.wulpus_pro.protocol import (
    NUM_IMU_SAMPLES,
    get_num_us_samples_from_config,
    is_accelerometer_enabled_from_config,
)
from biogui.platforms.wulpus_pro.defaults import create_default_biceps_wulpus_uss_config
from biogui.platforms.wulpus_pro.runtime import (
    get_rx_channel_for_config,
    get_standard_signal_definitions_for_mode,
)

logger = logging.getLogger(__name__)

wulpus_config = create_default_biceps_wulpus_uss_config()

_BLE_PACKET_SIZE = 211
_BLE_NUM_PACKETS = 4
_BLE_HEADERS = (0x10, 0x11, 0x12, 0x13)
# Each chunk carries the header/counter/timestamp prefix (harmonized with the
# ExG/MIC/PPG packets); the 201-byte SPI payload follows at byte 7 and must be
# extracted from there before concatenating the 4 chunks into one US frame.
# Per-frame metadata is mirrored into every chunk (see firmware WULPUS_META_*):
#   [0]      chunk header (0x10..0x13)
#   [1:3]    frame counter (uint16 LE)
#   [3:7]    timestamp us  (uint32 LE)
#   [7:208]  201-byte SPI payload chunk
_WULPUS_SPI_BYTES = 201
_WULPUS_SPI_OFF = 7          # SPI payload starts here in each chunk
_WULPUS_META_CNT_OFF = 1     # frame counter (uint16 LE)
_WULPUS_META_TS_OFF = 3      # microsecond timestamp (uint32 LE)

packetSize: int = _BLE_PACKET_SIZE
"""Number of bytes in each BLE packet; four packets make one US frame."""

_ble_buffer: list[bytes] = []
"""Accumulates BLE payload chunks until a complete 4-packet frame is ready."""

startSeq: list[bytes | float] = [
    wulpus_config.get_restart_package(),  # Send restart first
    0.5,
    wulpus_config.get_conf_package(),  # Send configuration which acts as start command
]
"""
Sequence of commands (as bytes) to start the device; floats are
interpreted as delays (in seconds) between commands.
"""


stopSeq: list[bytes | float] = [
    wulpus_config.get_restart_package(),  # Send restart command aka stop command,
]
"""
Sequence of commands (as bytes) to stop the device; floats are
interpreted as delays (in seconds) between commands.
"""

platformConfig = WULPUS_PLATFORM
"""Optional curated platform metadata for the WULPUS interface."""


def get_standard_signal_definitions(meas_period_s: float) -> dict:
    """
    Get standard signal definitions for WULPUS (IMU + metadata).
    """
    return get_standard_signal_definitions_for_mode(
        meas_period_s,
        is_accelerometer_enabled_from_config(wulpus_config),
    )


# Each configuration gets data every (num_txrx_configs * meas_period) due to round-robin
meas_period_s = wulpus_config.meas_period / 1e6  # Convert to seconds
period_per_config_s = meas_period_s * wulpus_config.num_txrx_configs
accelerometer_enabled = is_accelerometer_enabled_from_config(wulpus_config)
num_us_samples = get_num_us_samples_from_config(wulpus_config)

# Effective sampling rate: samples delivered per second for each configuration
samples_per_second_per_config = num_us_samples / period_per_config_s

# ADC start delay relative to pulse generation
adc_start_delay = (wulpus_config.start_adcsampl - wulpus_config.start_ppg) * 1e-6

# Build sigInfo and mapping: one signal per active configuration
sigInfo: dict = {}
config_to_signal_name: dict[int, str] = {}  # Maps config_id -> signal_name

for config_id in range(wulpus_config.num_txrx_configs):
    rx_channel = get_rx_channel_for_config(wulpus_config, config_id)

    if rx_channel is None:
        # TX-only config, skip
        logger.info(f"WULPUS Config {config_id}: TX-only, skipping")
        continue

    # Generate signal name
    if wulpus_config.num_txrx_configs == 1:
        signal_name = "ultrasound"
    else:
        signal_name = f"ultrasound_cfg{config_id}_rx{rx_channel}"

    # Store mapping
    config_to_signal_name[config_id] = signal_name

    sigInfo[signal_name] = {
        "fs": samples_per_second_per_config,
        "nCh": 1,
        "extras": {
            "type": "ultrasound",
            "config_id": config_id,
            "rx_channel": rx_channel,
            "num_samples": num_us_samples,
            "meas_period": wulpus_config.meas_period,
            "adc_sampling_freq": wulpus_config.sampling_freq,
            "adc_start_delay": adc_start_delay,
        },
    }

    logger.info(
        f"WULPUS Config {config_id}: Created signal '{signal_name}' "
        f"(RX Ch{rx_channel}, fs={samples_per_second_per_config:.2f} Hz)"
    )


# Add standard signals (IMU + metadata: acquisition_number and tx_rx_id)
sigInfo.update(get_standard_signal_definitions_for_mode(meas_period_s, accelerometer_enabled))
if accelerometer_enabled:
    logger.info(f"WULPUS: Created signal 'imu' (fs={1.0 / meas_period_s:.2f} Hz)")


if len(sigInfo) == 0:
    raise ValueError(
        "No active RX configurations found in WULPUS setup. "
        "At least one configuration must have an active RX channel."
    )

"""Dictionary containing the signals information."""


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """
    Decode one 211-byte BLE packet. Accumulates 4 packets into one US frame.
    Returns empty arrays until a complete frame is assembled.
    Resyncs automatically on unexpected headers.
    """
    global _ble_buffer

    header = data[0]

    if header == 0x10:
        if _ble_buffer:
            logger.warning("WULPUS: 0x10 received before previous frame completed, resyncing")
        _ble_buffer = [bytes(data[_WULPUS_SPI_OFF:_WULPUS_SPI_OFF + _WULPUS_SPI_BYTES])]
    elif _ble_buffer and header == _BLE_HEADERS[len(_ble_buffer)]:
        _ble_buffer.append(bytes(data[_WULPUS_SPI_OFF:_WULPUS_SPI_OFF + _WULPUS_SPI_BYTES]))
    else:
        logger.warning(f"WULPUS: Unexpected BLE header 0x{header:02X}, resyncing")
        _ble_buffer = []

    if len(_ble_buffer) < 4:
        empty: dict[str, np.ndarray] = {}
        for signal_name in sigInfo.keys():
            if signal_name in ("acquisition_number", "wulpus_counter"):
                empty[signal_name] = np.empty((0, 1), dtype=np.uint16)
            elif signal_name == "wulpus_timestamp":
                empty[signal_name] = np.empty((0, 1), dtype=np.uint32)
            elif signal_name == "tx_rx_id":
                empty[signal_name] = np.empty((0, 1), dtype=np.uint8)
            elif signal_name == "imu":
                empty[signal_name] = np.empty((0, 3), dtype=np.int16)
            else:
                empty[signal_name] = np.empty((0, 1), dtype=np.int16)
        return empty

    payload = b"".join(_ble_buffer)
    _ble_buffer = []

    # Per-frame metadata lives in the padding tail of each chunk (mirrored);
    # `data` here is the 4th chunk (0x13), so read counter/timestamp from it.
    wulpus_counter = int.from_bytes(data[_WULPUS_META_CNT_OFF:_WULPUS_META_CNT_OFF + 2], "little")
    wulpus_timestamp = int.from_bytes(data[_WULPUS_META_TS_OFF:_WULPUS_META_TS_OFF + 4], "little")

    # Payload layout: [SOF_MASK, tx_rx_id, frame_nr_lo, frame_nr_hi, US data...]
    sof_mask = payload[0]
    tx_rx_id = payload[1]
    acq_nr = np.frombuffer(payload[2:4], dtype="<u2")[0]
    rf_arr = np.frombuffer(payload[4:], dtype="<i2")

    print(
        f"[WULPUS] SOF=0x{sof_mask:02X} tx_rx_id={tx_rx_id} acq_nr={acq_nr} "
        f"rf_samples={len(rf_arr)} raw_header_bytes={payload[:8].hex()}"
    )

    accelerometer_enabled = is_accelerometer_enabled_from_config(wulpus_config)
    num_us_samples = get_num_us_samples_from_config(wulpus_config)

    us_samples = rf_arr[:num_us_samples]
    imu_samples = None
    if accelerometer_enabled:
        imu_samples = rf_arr[num_us_samples : num_us_samples + NUM_IMU_SAMPLES]

    result = {}

    for signal_name in sigInfo.keys():
        if signal_name == "acquisition_number":
            result[signal_name] = np.array([[acq_nr]], dtype=np.uint16)

        elif signal_name == "wulpus_counter":
            result[signal_name] = np.array([[wulpus_counter]], dtype=np.uint16)

        elif signal_name == "wulpus_timestamp":
            result[signal_name] = np.array([[wulpus_timestamp]], dtype=np.uint32)

        elif signal_name == "tx_rx_id":
            result[signal_name] = np.array([[tx_rx_id]], dtype=np.uint8)

        elif signal_name == "imu":
            if imu_samples is None:
                result[signal_name] = np.empty((0, 3), dtype=np.int16)
            else:
                result[signal_name] = imu_samples.reshape(1, 3)

        else:
            if config_to_signal_name.get(tx_rx_id) == signal_name:
                result[signal_name] = us_samples.reshape(-1, 1)
            else:
                result[signal_name] = np.empty((0, 1), dtype=np.int16)

    return result
