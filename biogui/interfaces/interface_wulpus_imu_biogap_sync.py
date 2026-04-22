# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
This module contains the WULPUS interface for ultrasound.

Signal Configuration:
--------------------
The interface defines several signal types forwarded to BioGUI:
- Ultrasound: One or more channels (depending on TX/RX configuration)
- IMU: 3-channel accelerometer data (ax, ay, az)
- acquisition_number: Packet sequence number (hidden, for loss detection)
- tx_rx_id: Hardware configuration ID (hidden, for channel identification)

Helper Functions:
----------------
- get_standard_signal_definitions(): Returns IMU + metadata signals (acquisition_number, tx_rx_id)

Protocol constants and USS configuration live in :mod:`biogui.platforms.wulpus`.
"""

import logging

import numpy as np

from biogui.platforms.wulpus import (
    ACQ_LENGTH_SAMPLES,
    MEAS_MODE_ACCELEROMETER_ENABLED,
    NUM_IMU_SAMPLES,
    RX_MAP,
    WULPUS_PLATFORM,
    WulpusRxTxConfigGen,
    WulpusUssConfig,
    get_num_us_samples_from_config,
    is_accelerometer_enabled_from_config,
)
from biogui.platforms.wulpus import (
    PGA_GAIN as PGA_GAIN,
    TX_MAP as TX_MAP,
    USS_CAPTURE_ACQ_RATES as USS_CAPTURE_ACQ_RATES,
)


logger = logging.getLogger(__name__)


# Create biceps exercise wulpus configuration
rx_tx_config = WulpusRxTxConfigGen()
rx_tx_config.add_config(
    tx_channels=[3],
    rx_channels=[3],
    optimized_switching=False,
)


wulpus_config = WulpusUssConfig(
    dcdc_turnon=19530,
    meas_period=33333,
    meas_mode=MEAS_MODE_ACCELEROMETER_ENABLED,
    pulse_freq=2250000,
    num_pulses=2,
    sampling_freq=8000000.0,
    num_samples=ACQ_LENGTH_SAMPLES,
    rx_gain=30.8,
    num_txrx_configs=rx_tx_config.tx_rx_len,
    tx_configs=rx_tx_config.get_tx_configs(),
    rx_configs=rx_tx_config.get_rx_configs(),
    start_hvmuxrx=498,
    start_ppg=500,
    turnon_adc=5,
    start_pgainbias=5,
    start_adcsampl=509,
    restart_capt=3000,
    capt_timeout=3000,
)

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
    # 1.0,
]
"""
Sequence of commands (as bytes) to stop the device; floats are
interpreted as delays (in seconds) between commands.
"""

platformConfig = WULPUS_PLATFORM
"""Optional curated platform metadata for the WULPUS interface."""


def get_rx_channel_for_config(config: WulpusUssConfig, config_id: int) -> int | None:
    """
    Get the active RX channel for a specific TX/RX configuration.
    Assumes each configuration has at most one active RX channel.
    """
    if config_id >= config.num_txrx_configs:
        return None

    rx_config_bits = config.rx_configs[config_id]

    # Find the active RX channel
    for channel_id in range(8):
        switch_id = RX_MAP[channel_id]
        if (rx_config_bits >> switch_id) & 1:
            return channel_id

    return None  # No RX channel active (TX-only config)


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
    """Get standard signal definitions for WULPUS metadata, sync, and optional IMU."""
    fs = 1.0 / meas_period_s
    definitions = {
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


# Add standard signals (IMU + metadata + synchronization_signal)
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

    # Validate start sequence
    if data[:6] != b"START\n":
        raise ValueError(
            "WULPUS INTERFACE ERROR: Data packet does not start with expected "
            "b'START\\n' sequence. Data alignment error."
        )

    data = data[9:]  # Remove b'START\n' + 3 bytes of header (total 9 bytes)
    frame_mask = data[0]
    tx_rx_id = data[1]
    acq_nr = data[2]
    sync_signal = data[3]
    rf_arr = np.frombuffer(data[4:], dtype="<i2")

    # logger.info(f"Wulpus Interface: {acq_nr=}, {tx_rx_id=}")
    # logger.info(f"Wulpus Interface: {rf_arr[:20]=}\n")

    accelerometer_enabled = is_accelerometer_enabled_from_config(wulpus_config)
    num_us_samples = get_num_us_samples_from_config(wulpus_config)

    # Split frame depending on measurement mode.
    us_samples = rf_arr[:num_us_samples]
    imu_samples = None
    if accelerometer_enabled:
        imu_samples = rf_arr[num_us_samples : num_us_samples + NUM_IMU_SAMPLES]

    # Build result dictionary with all signals
    result = {}

    for signal_name in sigInfo.keys():
        if signal_name == "acquisition_number":
            # Store acquisition number to track packet sequence numbers (for loss detection)
            result[signal_name] = np.array([[acq_nr]], dtype=np.uint16)

        elif signal_name == "tx_rx_id":
            # Store config ID to track which TX/RX configuration is active
            result[signal_name] = np.array([[tx_rx_id]], dtype=np.uint8)

        elif signal_name == "imu":
            if imu_samples is None:
                result[signal_name] = np.empty((0, 3), dtype=np.int16)
            else:
                result[signal_name] = imu_samples.reshape(1, 3)

        elif signal_name == "synchronization_signal":
            # Forward synchronization signal from HW (e.g. for BIOGAP synchronization)
            result[signal_name] = np.array([[sync_signal]], dtype=np.uint8)
        else:
            # Ultrasound signal: check if this config is active in current frame
            if config_to_signal_name.get(tx_rx_id) == signal_name:
                result[signal_name] = us_samples.reshape(-1, 1)
            else:
                # Config not active in this frame
                result[signal_name] = np.empty((0, 1), dtype=np.int16)

    return result
