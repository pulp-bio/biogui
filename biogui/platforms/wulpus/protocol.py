# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
WULPUS hardware protocol: frame layout, configuration bytes, and USS config.

Frame structure:
----------------
Hardware sends 400 int16 values per acquisition frame:
    - IMU enabled (meas_mode=101): 397 ultrasound + 3 IMU samples
    - IMU disabled (meas_mode=0): 400 ultrasound samples
"""

import numpy as np

# ============================================================================
# WULPUS Frame Structure
# ============================================================================
ACQ_LENGTH_SAMPLES = 400
NUM_US_SAMPLES = 397
NUM_IMU_SAMPLES = 3

assert (
    ACQ_LENGTH_SAMPLES == NUM_US_SAMPLES + NUM_IMU_SAMPLES
), "Frame structure constants are inconsistent"


# Protocol related
START_BYTE_CONF_PACK = 250
START_BYTE_RESTART = 251  # stops acquisition loop on WULPUS and waits for a new valid config
PACKAGE_LEN = 68


# Measurement mode values encoded in the firmware transFreq field.
MEAS_MODE_ACCELEROMETER_ENABLED = 101
MEAS_MODE_ULTRASOUND_ONLY = 0


def is_accelerometer_enabled_from_mode(meas_mode: int) -> bool:
    """Return True if accelerometer bytes are enabled for the given measurement mode."""
    return int(meas_mode) == MEAS_MODE_ACCELEROMETER_ENABLED


def get_num_us_samples_from_mode(meas_mode: int) -> int:
    """Return number of ultrasound samples in each frame for the selected mode."""
    if is_accelerometer_enabled_from_mode(meas_mode):
        return ACQ_LENGTH_SAMPLES - NUM_IMU_SAMPLES
    return ACQ_LENGTH_SAMPLES


def is_accelerometer_enabled_from_config(config: "WulpusUssConfig") -> bool:
    """Return True if accelerometer data is enabled in the provided configuration."""
    return is_accelerometer_enabled_from_mode(config.meas_mode)


def get_num_us_samples_from_config(config: "WulpusUssConfig") -> int:
    """Return number of ultrasound samples for the provided configuration."""
    return get_num_us_samples_from_mode(config.meas_mode)


USS_CAPTURE_OVER_SAMPLE_RATES = (10, 20, 40, 80, 160)
USS_CAPT_OVER_SAMPLE_RATES_REG = (0, 1, 2, 3, 4)
USS_CAPTURE_ACQ_RATES = [80e6 / x for x in USS_CAPTURE_OVER_SAMPLE_RATES]

PGA_GAIN = (
    -6.5,
    -5.5,
    -4.6,
    -4.1,
    -3.3,
    -2.3,
    -1.4,
    -0.8,
    0.1,
    1.0,
    1.9,
    2.6,
    3.5,
    4.4,
    5.2,
    6.0,
    6.8,
    7.7,
    8.7,
    9.0,
    9.8,
    10.7,
    11.7,
    12.2,
    13,
    13.9,
    14.9,
    15.5,
    16.3,
    17.2,
    18.2,
    18.8,
    19.6,
    20.5,
    21.5,
    22,
    22.8,
    23.6,
    24.6,
    25.0,
    25.8,
    26.7,
    27.7,
    28.1,
    28.9,
    29.8,
    30.8,
)

PGA_GAIN_REG = tuple(np.arange(17, 64))


us_to_ticks = {
    "dcdc_turnon": 65535 / 2000000,
    "meas_period": 65535 / 2000000,
    "start_hvmuxrx": 8,
    "start_ppg": 5,
    "turnon_adc": 5,
    "start_pgainbias": 5,
    "start_adcsampl": 5,
    "restart_capt": 5 / 16,
    "capt_timeout": 5 / 4,
}


class _ConfigBytes:
    """Represents a configuration parameter."""

    def __init__(self, config_name, friendly_name, limit_type, min_val, max_val, format):
        self.config_name = config_name
        self.friendly_name = friendly_name
        self.limit_type = limit_type
        self.min_val = min_val
        self.max_val = max_val
        self.format = format

    def get_as_bytes(self, value):
        if self.limit_type == "limit":
            if (value < self.min_val) or (value > self.max_val):
                raise ValueError(
                    self.friendly_name
                    + " equal to "
                    + str(value)
                    + " exceeds the allowed range ["
                    + str(self.min_val)
                    + ", "
                    + str(self.max_val)
                    + "]."
                )
        elif self.limit_type == "list":
            if value not in self.min_val:
                raise ValueError(
                    self.friendly_name
                    + " equal to "
                    + str(value)
                    + " is not allowed. Allowed values are: "
                    + str(self.min_val)
                )

        return np.array([value]).astype(self.format).tobytes()


configuration_package = [
    [
        _ConfigBytes("dcdc_turnon", "DC-DC turn on time [us]", "limit", 0, 65535, "<u2"),
        _ConfigBytes("meas_period", "Acquisition Period [us]", "limit", 655, 65535, "<u2"),
        _ConfigBytes("meas_mode", "Measurement mode", "limit", 0, 5000000, "<u4"),
        _ConfigBytes("pulse_freq", "Pulse frequency [Hz]", "limit", 0, 5000000, "<u4"),
        _ConfigBytes("num_pulses", "Number of pulses", "limit", 0, 30, "<u1"),
        _ConfigBytes(
            "sampling_freq",
            "Sampling frequency [Hz]",
            "list",
            USS_CAPT_OVER_SAMPLE_RATES_REG,
            USS_CAPTURE_ACQ_RATES,
            "<u2",
        ),
        _ConfigBytes("num_samples", "Number of samples", "limit", 0, 800, "<u2"),
        _ConfigBytes("rx_gain", "Receive (RX) gain [dB]", "list", PGA_GAIN_REG, PGA_GAIN, "<u1"),
        _ConfigBytes("num_txrx_configs", "Number of TX/RX configs", "limit", 0, 16, "<u1"),
    ],
    [
        _ConfigBytes("start_hvmuxrx", "HV-MUX RX start time [us]", "limit", 0, 65535, "<u2"),
        _ConfigBytes("start_ppg", "PPG start time [us]", "limit", 0, 65535, "<u2"),
        _ConfigBytes("turnon_adc", "ADC turn on time [us]", "limit", 0, 65535, "<u2"),
        _ConfigBytes("start_pgainbias", "PGA in bias start time [us]", "limit", 0, 65535, "<u2"),
        _ConfigBytes("start_adcsampl", "ADC sampling start time [us]", "limit", 0, 65535, "<u2"),
        _ConfigBytes("restart_capt", "Capture restart time [us]", "limit", 0, 65535, "<u2"),
        _ConfigBytes("capt_timeout", "Capture timeout time [us]", "limit", 0, 65535, "<u2"),
    ],
]


TX_RX_MAX_NUM_OF_CONFIGS = 16
MAX_CH_ID = 7

RX_MAP = np.array([0, 2, 4, 6, 8, 10, 12, 14])
TX_MAP = np.array([1, 3, 5, 7, 9, 11, 13, 15])


class WulpusRxTxConfigGen:
    def __init__(self):
        self.rx_configs = np.zeros(TX_RX_MAX_NUM_OF_CONFIGS, dtype="<u2")
        self.tx_configs = np.zeros(TX_RX_MAX_NUM_OF_CONFIGS, dtype="<u2")
        self.tx_rx_len = 0

    def add_config(self, tx_channels, rx_channels, optimized_switching=False):
        """Add a new configuration to the list of configurations."""
        if self.tx_rx_len >= TX_RX_MAX_NUM_OF_CONFIGS:
            raise ValueError(f"Maximum number of configs is {TX_RX_MAX_NUM_OF_CONFIGS}")

        if any(channel > MAX_CH_ID for channel in tx_channels) or any(
            channel > MAX_CH_ID for channel in rx_channels
        ):
            raise ValueError(f"RX and TX channel ID must be less than {MAX_CH_ID}")

        if any(channel < 0 for channel in tx_channels) or any(
            channel < 0 for channel in rx_channels
        ):
            raise ValueError("RX and TX channel ID must be positive.")

        if len(tx_channels) == 0:
            self.tx_configs[self.tx_rx_len] = 0
        else:
            self.tx_configs[self.tx_rx_len] = np.bitwise_or.reduce(
                np.left_shift(1, TX_MAP[tx_channels])
            )

        if len(rx_channels) == 0:
            self.rx_configs[self.tx_rx_len] = 0
        else:
            self.rx_configs[self.tx_rx_len] = np.bitwise_or.reduce(
                np.left_shift(1, RX_MAP[rx_channels])
            )

        if optimized_switching:
            rx_tx_intersect_ch = list(set(tx_channels) & set(rx_channels))
            rx_only_ch = list(set(rx_tx_intersect_ch) ^ set(rx_channels))

            if len(rx_tx_intersect_ch) > len(rx_only_ch):
                temp_switch_config = np.bitwise_or.reduce(
                    np.left_shift(1, RX_MAP[rx_tx_intersect_ch])
                )
                self.tx_configs[self.tx_rx_len] = np.bitwise_or(
                    self.tx_configs[self.tx_rx_len], temp_switch_config
                )
            elif len(rx_only_ch) > 0:
                temp_switch_config = np.bitwise_or.reduce(np.left_shift(1, RX_MAP[rx_only_ch]))
                self.tx_configs[self.tx_rx_len] = np.bitwise_or(
                    self.tx_configs[self.tx_rx_len], temp_switch_config
                )

        self.tx_rx_len += 1

    def get_tx_configs(self):
        return self.tx_configs[: self.tx_rx_len]

    def get_rx_configs(self):
        return self.rx_configs[: self.tx_rx_len]


class WulpusUssConfig:
    def __init__(
        self,
        dcdc_turnon=195300,
        meas_period=321965,
        meas_mode=MEAS_MODE_ACCELEROMETER_ENABLED,
        pulse_freq=225e4,
        num_pulses=2,
        sampling_freq=USS_CAPTURE_ACQ_RATES[0],
        num_samples=ACQ_LENGTH_SAMPLES,
        rx_gain=PGA_GAIN[-10],
        num_txrx_configs=1,
        tx_configs=[0],
        rx_configs=[0],
        start_hvmuxrx=500,
        start_ppg=500,
        turnon_adc=5,
        start_pgainbias=5,
        start_adcsampl=503,
        restart_capt=3000,
        capt_timeout=3000,
    ):
        if sampling_freq not in USS_CAPTURE_ACQ_RATES:
            raise ValueError(f"Invalid sampling frequency. Must be one of {USS_CAPTURE_ACQ_RATES}")

        if rx_gain not in PGA_GAIN:
            raise ValueError(f"Invalid RX gain. Must be one of {PGA_GAIN}")

        self.dcdc_turnon = int(dcdc_turnon)
        self.meas_period = int(meas_period)
        self.meas_mode = int(meas_mode)
        self.pulse_freq = int(pulse_freq)
        self.num_pulses = int(num_pulses)
        self.sampling_freq = int(sampling_freq)
        self.num_samples = int(num_samples)
        self.rx_gain = float(rx_gain)
        self.num_txrx_configs = int(num_txrx_configs)
        self.tx_configs = np.array(tx_configs).astype("<u2")
        self.rx_configs = np.array(rx_configs).astype("<u2")

        self.start_hvmuxrx = int(start_hvmuxrx)
        self.start_ppg = int(start_ppg)
        self.turnon_adc = int(turnon_adc)
        self.start_pgainbias = int(start_pgainbias)
        self.start_adcsampl = int(start_adcsampl)
        self.restart_capt = int(restart_capt)
        self.capt_timeout = int(capt_timeout)

        self.convert_to_registers()
        _ = self.get_conf_package()

    def convert_to_registers(self):
        self.dcdc_turnon_reg = int(self.dcdc_turnon * us_to_ticks["dcdc_turnon"])
        self.meas_period_reg = int(self.meas_period * us_to_ticks["meas_period"])
        self.meas_mode_reg = int(self.meas_mode)
        self.pulse_freq_reg = int(self.pulse_freq)
        self.num_pulses_reg = int(self.num_pulses)
        self.sampling_freq_reg = int(
            USS_CAPT_OVER_SAMPLE_RATES_REG[USS_CAPTURE_ACQ_RATES.index(self.sampling_freq)]
        )
        self.num_samples_reg = int(self.num_samples * 2)
        self.rx_gain_reg = int(PGA_GAIN_REG[PGA_GAIN.index(self.rx_gain)])
        self.num_txrx_configs_reg = int(self.num_txrx_configs)
        self.start_hvmuxrx_reg = int(self.start_hvmuxrx * us_to_ticks["start_hvmuxrx"])
        self.start_ppg_reg = int(self.start_ppg * us_to_ticks["start_ppg"])
        self.turnon_adc_reg = int(self.turnon_adc * us_to_ticks["turnon_adc"])
        self.start_pgainbias_reg = int(self.start_pgainbias * us_to_ticks["start_pgainbias"])
        self.start_adcsampl_reg = int(self.start_adcsampl * us_to_ticks["start_adcsampl"])
        self.restart_capt_reg = int(self.restart_capt * us_to_ticks["restart_capt"])
        self.capt_timeout_reg = int(self.capt_timeout * us_to_ticks["capt_timeout"])

    def get_conf_package(self):
        bytes_arr = np.array([START_BYTE_CONF_PACK]).astype("<u1").tobytes()

        self.convert_to_registers()

        for param in configuration_package[0]:
            value = getattr(self, param.config_name + "_reg")
            bytes_arr += param.get_as_bytes(value)

        for i in range(self.num_txrx_configs):
            bytes_arr += self.tx_configs[i].astype("<u2").tobytes()
            bytes_arr += self.rx_configs[i].astype("<u2").tobytes()

        for param in configuration_package[1]:
            value = getattr(self, param.config_name + "_reg")
            bytes_arr += param.get_as_bytes(value)

        if len(bytes_arr) < PACKAGE_LEN:
            bytes_arr += np.zeros(PACKAGE_LEN - len(bytes_arr)).astype("<u1").tobytes()

        return bytes_arr

    def get_restart_package(self):
        bytes_arr = np.array([START_BYTE_RESTART], dtype="<u1").tobytes()
        bytes_arr += np.zeros(PACKAGE_LEN - len(bytes_arr), dtype="<u1").tobytes()
        return bytes_arr
