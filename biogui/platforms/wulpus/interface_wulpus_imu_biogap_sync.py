# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
WULPUS interface with extra BIOGAP synchronization and extended frame layout.

Differs from interface_wulpus: 9-byte prefix before RF samples and an extra
synchronization_signal entry in sigInfo.
"""

import logging

import numpy as np

from biogui.platforms.wulpus import (
    NUM_IMU_SAMPLES,
    WULPUS_PLATFORM,
    get_num_us_samples_from_config,
    is_accelerometer_enabled_from_config,
)
from biogui.platforms.wulpus.defaults import create_default_biceps_wulpus_uss_config
from biogui.platforms.wulpus.runtime import get_rx_channel_for_config

logger = logging.getLogger(__name__)

wulpus_config = create_default_biceps_wulpus_uss_config()

packetSize: int = wulpus_config.num_samples * 2 + 7 + 6
"""Number of bytes in each package."""

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
    Get standard signal definitions for WULPUS (IMU + metadata + synchronization).
    """
    return get_standard_signal_definitions_for_mode(
        meas_period_s,
        is_accelerometer_enabled_from_config(wulpus_config),
    )


def get_standard_signal_definitions_for_mode(
    meas_period_s: float,
    accelerometer_enabled: bool,
) -> dict:
    """WULPUS metadata, optional IMU, and extra synchronization_signal for BIOGAP sync."""
    fs = 1.0 / meas_period_s
    definitions: dict = {
        "acquisition_number": {
            "fs": fs,
            "nCh": 1,
            "hidden": True,
            "extras": {"type": "time-series"},
        },
        "tx_rx_id": {
            "fs": fs,
            "nCh": 1,
            "hidden": True,
            "extras": {"type": "time-series"},
        },
        "synchronization_signal": {
            "fs": fs,
            "nCh": 1,
            "extras": {"type": "time-series"},
        },
    }

    if accelerometer_enabled:
        definitions["imu"] = {
            "fs": fs,
            "nCh": 3,
            "extras": {"type": "time-series"},
        }

    return definitions


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
        logger.info(f"WULPUS Config {config_id}: TX-only, skipping")
        continue

    if wulpus_config.num_txrx_configs == 1:
        signal_name = "ultrasound"
    else:
        signal_name = f"ultrasound_cfg{config_id}_rx{rx_channel}"

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
    Decode binary data received from WULPUS into signals.
    """
    if data[:6] != b"START\n":
        raise ValueError(
            "WULPUS INTERFACE ERROR: Data packet does not start with expected "
            "b'START\\n' sequence. Data alignment error."
        )

    data = data[9:]  # Remove b'START\n' + 3 bytes of header (total 9 bytes)
    # data[0] = frame mask (unused here)
    tx_rx_id = data[1]
    acq_nr = data[2]
    sync_signal = data[3]
    rf_arr = np.frombuffer(data[4:], dtype="<i2")

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

        elif signal_name == "tx_rx_id":
            result[signal_name] = np.array([[tx_rx_id]], dtype=np.uint8)

        elif signal_name == "imu":
            if imu_samples is None:
                result[signal_name] = np.empty((0, 3), dtype=np.int16)
            else:
                result[signal_name] = imu_samples.reshape(1, 3)

        elif signal_name == "synchronization_signal":
            result[signal_name] = np.array([[sync_signal]], dtype=np.uint8)
        else:
            if config_to_signal_name.get(tx_rx_id) == signal_name:
                result[signal_name] = us_samples.reshape(-1, 1)
            else:
                result[signal_name] = np.empty((0, 1), dtype=np.int16)

    return result
