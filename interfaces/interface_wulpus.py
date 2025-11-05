"""
This module contains the WULPUS interface for ultrasound.

Portions derived from code by ETH Zurich (Apache-2.0).

Copyright 2025 Enzo Baraldi
Copyright 2023 ETH Zurich. All rights reserved.
Authors (upstream portions): Sergei Vostrikov, Cedric Hirschi, ETH Zurich

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging

import numpy as np

# baudrate = 4000000
ACQ_LENGTH_SAMPLES = 400

# Protocol related
START_BYTE_CONF_PACK = 250
START_BYTE_RESTART = 251  # stops acquisition loop on WULPUS and WULPUS will wait for a new valid configuration package
# Maximum length of the configuration package
PACKAGE_LEN = 68


# Oversampling rate
# Rates value
USS_CAPTURE_OVER_SAMPLE_RATES = (10, 20, 40, 80, 160)
# Corresponding register values to be sent to HW
USS_CAPT_OVER_SAMPLE_RATES_REG = (0, 1, 2, 3, 4)
# Corresponding acquisition rates
USS_CAPTURE_ACQ_RATES = [80e6 / x for x in USS_CAPTURE_OVER_SAMPLE_RATES]

# PGA RX gain
# Gain in dB
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

# Register value to write to HW
PGA_GAIN_REG = tuple(np.arange(17, 64))


# Lookup table for us to ticks conversion
# Where HSPLL_CLOCK_FREQ = 80MHz
us_to_ticks = {
    "dcdc_turnon": 65535 / 2000000,  # cycles of LFXT (655 - 20ms, 65535 - 2s)
    "meas_period": 65535 / 2000000,  # same as above
    "start_hvmuxrx": 8,  # delay in s * 8MHz
    "start_ppg": 5,  # delay in s * (HSPLL_CLOCK_FREQ / 16) = delay in s * (80MHz / 16)
    "turnon_adc": 5,  # same as above
    "start_pgainbias": 5,  # same as above
    "start_adcsampl": 5,  # same as above
    "restart_capt": 5 / 16,  # delay in s * (HSPLL_CLOCK_FREQ / 256)
    "capt_timeout": 5 / 4,  # delay in s * (HSPLL_CLOCK_FREQ / 64)
}


class _ConfigBytes:
    """
    Represents a configuration parameter.

    Attributes:
        config_name (str):      Name of the configuration parameter.
        friendly_name (str):    Reader friendly name of the configuration parameter.
        limit_type (str):       Type of the limit. Can be 'limit' or 'list'.
        min_val (int):          Minimum value of the configuration parameter or list of allowed register values.
        max_val (int):          Maximum value of the configuration parameter or list of allowed friendly values.
        format (str):           Format of the configuration parameter. (e.g. '<u2')
    """

    def __init__(
        self, config_name, friendly_name, limit_type, min_val, max_val, format
    ):
        self.config_name = config_name
        self.friendly_name = friendly_name
        self.limit_type = limit_type
        self.min_val = min_val
        self.max_val = max_val
        self.format = format

    def get_as_bytes(self, value):
        # Get configuration parameter as bytes

        if self.limit_type == "limit":
            # Check if value is within the allowed range
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
            # Check if value is located in the list of allowed values
            if value not in self.min_val:
                raise ValueError(
                    self.friendly_name
                    + " equal to "
                    + str(value)
                    + " is not allowed. Allowed values are: "
                    + str(self.min_val)
                )

        return np.array([value]).astype(self.format).tobytes()


# Configuration package representation
# The first list contains basic settings
# The second list contains advanced settings
# The third list contains GUI settings which are not sent to the HW
# Between the two lists there is a list of TX/RX configurations
#   config_name, friendly_name, limit_type, min_val, max_val, format
configuration_package = [
    [
        _ConfigBytes(
            "dcdc_turnon", "DC-DC turn on time [us]", "limit", 0, 65535, "<u2"
        ),
        _ConfigBytes(
            "meas_period", "Acquisition Period [us]", "limit", 655, 65535, "<u2"
        ),
        _ConfigBytes(
            "trans_freq", "Transmitter frequency [Hz]", "limit", 0, 5000000, "<u4"
        ),
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
        _ConfigBytes(
            "rx_gain", "Receive (RX) gain [dB]", "list", PGA_GAIN_REG, PGA_GAIN, "<u1"
        ),
        _ConfigBytes(
            "num_txrx_configs", "Number of TX/RX configs", "limit", 0, 16, "<u1"
        ),
    ],
    [
        _ConfigBytes(
            "start_hvmuxrx", "HV-MUX RX start time [us]", "limit", 0, 65535, "<u2"
        ),
        _ConfigBytes("start_ppg", "PPG start time [us]", "limit", 0, 65535, "<u2"),
        _ConfigBytes("turnon_adc", "ADC turn on time [us]", "limit", 0, 65535, "<u2"),
        _ConfigBytes(
            "start_pgainbias", "PGA in bias start time [us]", "limit", 0, 65535, "<u2"
        ),
        _ConfigBytes(
            "start_adcsampl", "ADC sampling start time [us]", "limit", 0, 65535, "<u2"
        ),
        _ConfigBytes(
            "restart_capt", "Capture restart time [us]", "limit", 0, 65535, "<u2"
        ),
        _ConfigBytes(
            "capt_timeout", "Capture timeout time [us]", "limit", 0, 65535, "<u2"
        ),
    ],
    [_ConfigBytes("num_acqs", "Number of acquisitions", "limit", 0, 10000000, None)],
]


# TX RX Configs
TX_RX_MAX_NUM_OF_CONFIGS = 16
MAX_CH_ID = 7

# TX RX is configured by activating the
# switches of HV multiplexer
# The arrays below maps transducer channels (0...7)
# to switches IDs (0..15) which we need to activate

RX_MAP = np.array([0, 2, 4, 6, 8, 10, 12, 14])
TX_MAP = np.array([1, 3, 5, 7, 9, 11, 13, 15])


class WulpusRxTxConfigGen:
    def __init__(self):
        self.rx_configs = np.zeros(TX_RX_MAX_NUM_OF_CONFIGS, dtype="<u2")
        self.tx_configs = np.zeros(TX_RX_MAX_NUM_OF_CONFIGS, dtype="<u2")
        self.tx_rx_len = 0

    def add_config(self, tx_channels, rx_channels, optimized_switching=False):
        """
        Add a new configuration to the list of configurations.

        Args:
            tx_channels: List of TX channel IDs (0...7)
            rx_channels: List of RX channel IDs (0...7)
            optimized_switching: Bool value to activate an algorithm for minimizing switching artifacts
        """
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
            # Shift 1 left by the provided switch TX indices and then apply OR bitwise operation along the array
            self.tx_configs[self.tx_rx_len] = np.bitwise_or.reduce(
                np.left_shift(1, TX_MAP[tx_channels])
            )

        if len(rx_channels) == 0:
            self.rx_configs[self.tx_rx_len] = 0
        else:
            # Shift 1 left by the provided switch RX indices and then apply OR bitwise operation along the array
            self.rx_configs[self.tx_rx_len] = np.bitwise_or.reduce(
                np.left_shift(1, RX_MAP[rx_channels])
            )

        if optimized_switching:
            # Optimize switching artifacts (less switching MUX activity after TX (pulsing) -> better SNR)
            # Find which channels are active both for TX and RX.
            rx_tx_intersect_ch = list(set(tx_channels) & set(rx_channels))
            # Find which channels are only active for RX but not in TX.
            rx_only_ch = list(set(rx_tx_intersect_ch) ^ set(rx_channels))
            # Find which channels are only active for TX but not in RX.
            tx_only_ch = list(set(rx_tx_intersect_ch) ^ set(tx_channels))

            # Compare the number of channels in the sets
            if len(rx_tx_intersect_ch) > len(rx_only_ch):
                # Activate the channels from the rx_tx_intersect_ch set for RX already before the TX event
                temp_switch_config = np.bitwise_or.reduce(
                    np.left_shift(1, RX_MAP[rx_tx_intersect_ch])
                )
                self.tx_configs[self.tx_rx_len] = np.bitwise_or(
                    self.tx_configs[self.tx_rx_len], temp_switch_config
                )
            elif len(rx_only_ch) > 0:
                # Create a group of receive only channels and enable them for RX already before the TX event
                temp_switch_config = np.bitwise_or.reduce(
                    np.left_shift(1, RX_MAP[rx_only_ch])
                )
                self.tx_configs[self.tx_rx_len] = np.bitwise_or(
                    self.tx_configs[self.tx_rx_len], temp_switch_config
                )

            # # Leave TX only channels on after the HV MUX switches to RX
            # if len(tx_only_ch) > 0:
            #     self.rx_configs[self.tx_rx_len] = np.bitwise_or.reduce(np.left_shift(1, TX_MAP[tx_only_ch]))

        self.tx_rx_len += 1

    def get_tx_configs(self):
        return self.tx_configs[: self.tx_rx_len]

    def get_rx_configs(self):
        return self.rx_configs[: self.tx_rx_len]


class WulpusUssConfig:
    def __init__(
        self,
        num_acqs=100,
        dcdc_turnon=195300,
        meas_period=321965,
        trans_freq=225e4,
        pulse_freq=225e4,
        num_pulses=2,
        sampling_freq=USS_CAPTURE_ACQ_RATES[0],
        num_samples=400,
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
        # check if sampling freq is valid
        if sampling_freq not in USS_CAPTURE_ACQ_RATES:
            raise ValueError(
                f"Invalid sampling frequency. Must be one of {USS_CAPTURE_ACQ_RATES}"
            )

        # check if rx gain is valid
        if rx_gain not in PGA_GAIN:
            raise ValueError(f"Invalid RX gain. Must be one of {PGA_GAIN}")

        # Parse basic settings
        self.num_acqs = int(num_acqs)
        self.dcdc_turnon = int(dcdc_turnon)
        self.meas_period = int(meas_period)
        self.trans_freq = int(trans_freq)
        self.pulse_freq = int(pulse_freq)
        self.num_pulses = int(num_pulses)
        self.sampling_freq = int(sampling_freq)
        self.num_samples = int(num_samples)
        self.rx_gain = float(rx_gain)
        self.num_txrx_configs = int(num_txrx_configs)
        self.tx_configs = np.array(tx_configs).astype("<u2")
        self.rx_configs = np.array(rx_configs).astype("<u2")

        # Parse advanced settings
        self.start_hvmuxrx = int(start_hvmuxrx)
        self.start_ppg = int(start_ppg)
        self.turnon_adc = int(turnon_adc)
        self.start_pgainbias = int(start_pgainbias)
        self.start_adcsampl = int(start_adcsampl)
        self.restart_capt = int(restart_capt)
        self.capt_timeout = int(capt_timeout)

        # check if configuration is valid
        self.convert_to_registers()  # convert to register saveable values
        _ = self.get_conf_package()  # use this to check if the configuration is valid

    def convert_to_registers(self):
        # convert to register saveable values

        self.dcdc_turnon_reg = int(self.dcdc_turnon * us_to_ticks["dcdc_turnon"])
        self.meas_period_reg = int(self.meas_period * us_to_ticks["meas_period"])
        self.trans_freq_reg = int(self.trans_freq)
        self.pulse_freq_reg = int(self.pulse_freq)
        self.num_pulses_reg = int(self.num_pulses)
        self.sampling_freq_reg = int(
            USS_CAPT_OVER_SAMPLE_RATES_REG[
                USS_CAPTURE_ACQ_RATES.index(self.sampling_freq)
            ]
        )  # converted to oversampling rate, thus name is misleading
        self.num_samples_reg = int(self.num_samples * 2)
        self.rx_gain_reg = int(PGA_GAIN_REG[PGA_GAIN.index(self.rx_gain)])
        self.num_txrx_configs_reg = int(self.num_txrx_configs)
        self.start_hvmuxrx_reg = int(self.start_hvmuxrx * us_to_ticks["start_hvmuxrx"])
        self.start_ppg_reg = int(self.start_ppg * us_to_ticks["start_ppg"])
        self.turnon_adc_reg = int(self.turnon_adc * us_to_ticks["turnon_adc"])
        self.start_pgainbias_reg = int(
            self.start_pgainbias * us_to_ticks["start_pgainbias"]
        )
        self.start_adcsampl_reg = int(
            self.start_adcsampl * us_to_ticks["start_adcsampl"]
        )
        self.restart_capt_reg = int(self.restart_capt * us_to_ticks["restart_capt"])
        self.capt_timeout_reg = int(self.capt_timeout * us_to_ticks["capt_timeout"])

    def get_conf_package(self):
        # Start byte fixed
        bytes_arr = np.array([START_BYTE_CONF_PACK]).astype("<u1").tobytes()

        # Make sure the values are converted to register saveable values
        self.convert_to_registers()

        # Write basic settings
        for param in configuration_package[0]:
            value = getattr(self, param.config_name + "_reg")
            bytes_arr += param.get_as_bytes(value)

        # Write TX and RX configurations
        for i in range(self.num_txrx_configs):
            bytes_arr += self.tx_configs[i].astype("<u2").tobytes()
            bytes_arr += self.rx_configs[i].astype("<u2").tobytes()

        # Write advanced settings
        for param in configuration_package[1]:
            value = getattr(self, param.config_name + "_reg")
            bytes_arr += param.get_as_bytes(value)

        # Add zeros to match the expected package legth if needed
        if len(bytes_arr) < PACKAGE_LEN:
            bytes_arr += np.zeros(PACKAGE_LEN - len(bytes_arr)).astype("<u1").tobytes()

        # Debug print the package
        # for byte in bytes_arr:
        #     # print hex value
        #     print(f'{byte:02x}', end=' ')
        # print()

        return bytes_arr

    def get_restart_package(self):
        bytes_arr = np.array([START_BYTE_RESTART], dtype="<u1").tobytes()

        # Add zeros to reach PACKAGE_LEN
        bytes_arr += np.zeros(PACKAGE_LEN - len(bytes_arr), dtype="<u1").tobytes()

        return bytes_arr


"""                          WULPUS related Code
-----------------------------------------------------------------------------------------
                             BIOGUI INTERFACE PARAMETERS
"""


# Create waterbath wulpus configuration
rx_tx_waterbath_config = WulpusRxTxConfigGen()
rx_tx_waterbath_config.add_config(
    tx_channels=[7], rx_channels=[7], optimized_switching=True
)


# ! number of samples is hardcoded in the wulpus firmware at the moment to 400
waterbath_config = WulpusUssConfig(
    num_acqs=100,
    dcdc_turnon=100,
    meas_period=228885,
    trans_freq=2250000,
    pulse_freq=1000000,
    num_pulses=11,
    sampling_freq=4000000.0,
    num_samples=400,
    rx_gain=6.8,
    num_txrx_configs=rx_tx_waterbath_config.tx_rx_len,
    tx_configs=rx_tx_waterbath_config.get_tx_configs(),  # only channel 7 with optimized switching
    rx_configs=rx_tx_waterbath_config.get_rx_configs(),  # only channel 7 with optimized switching
    start_hvmuxrx=500,
    start_ppg=500,
    turnon_adc=5,
    start_pgainbias=5,
    start_adcsampl=503,
    restart_capt=3000,
    capt_timeout=3000,
)


# Create biceps exercise wulpus configuration
rx_tx_biceps_config = WulpusRxTxConfigGen()
rx_tx_biceps_config.add_config(
    tx_channels=[3],
    rx_channels=[3],
    optimized_switching=False,
)
rx_tx_biceps_config.add_config(
    tx_channels=[7],
    rx_channels=[7],
    optimized_switching=False,
)


biceps_exercise_config = WulpusUssConfig(
    num_acqs=2000,
    dcdc_turnon=19530,
    meas_period=20000,
    trans_freq=2250000,
    pulse_freq=2250000,
    num_pulses=2,
    sampling_freq=8000000.0,
    num_samples=400,
    rx_gain=30.8,
    num_txrx_configs=rx_tx_biceps_config.tx_rx_len,
    tx_configs=rx_tx_biceps_config.get_tx_configs(),  # only channel 7 with optimized switching
    rx_configs=rx_tx_biceps_config.get_rx_configs(),  # only channel 7 with optimized switching
    start_hvmuxrx=498,
    start_ppg=500,
    turnon_adc=5,
    start_pgainbias=5,
    start_adcsampl=509,
    restart_capt=3000,
    capt_timeout=3000,
)

wulpus_config = waterbath_config

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


# Each configuration gets data every (num_txrx_configs * meas_period) due to round-robin
meas_period_s = wulpus_config.meas_period / 1e6  # Convert to seconds
period_per_config_s = meas_period_s * wulpus_config.num_txrx_configs

# Effective sampling rate: samples delivered per second for each configuration
samples_per_second_per_config = wulpus_config.num_samples / period_per_config_s

# ADC start delay relative to pulse generation
adc_start_delay = (wulpus_config.start_adcsampl - wulpus_config.start_ppg) * 1e-6

# Build sigInfo and mapping: one signal per active configuration
sigInfo: dict = {}
config_to_signal_name: dict[int, str] = {}  # Maps config_id -> signal_name

for config_id in range(wulpus_config.num_txrx_configs):
    rx_channel = get_rx_channel_for_config(wulpus_config, config_id)

    if rx_channel is None:
        # TX-only config, skip
        logging.info(f"WULPUS Config {config_id}: TX-only, skipping")
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
        "signal_type": {
            "type": "ultrasound",
            "config_id": config_id,
            "rx_channel": rx_channel,
            "num_samples": wulpus_config.num_samples,
            "meas_period": wulpus_config.meas_period,
            "adc_sampling_freq": wulpus_config.sampling_freq,
            "adc_start_delay": adc_start_delay,
        },
    }

    logging.info(
        f"WULPUS Config {config_id}: Created signal '{signal_name}' "
        f"(RX Ch{rx_channel}, fs={samples_per_second_per_config:.2f} Hz)"
    )

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

    # remove b'START\n' from data
    data = data[6:]

    rf_arr = np.frombuffer(data[7:], dtype="<i2")
    tx_rx_id = data[4]
    acq_nr = np.frombuffer(data[5:7], dtype="<u2")[0]

    # logging.info(f"Wulpus Interface: {acq_nr=}, {tx_rx_id=}")
    # logging.info(f"Wulpus Interface: {rf_arr[:20]=}\n")

    # Build result dictionary with all signals
    result = {}

    for signal_name in sigInfo.keys():
        # Check if this signal corresponds to the current config_id
        if config_to_signal_name.get(tx_rx_id) == signal_name:
            # This signal is active in this acquisition
            result[signal_name] = rf_arr.reshape(-1, 1)
        else:
            # This signal is not active in this acquisition - return empty array
            result[signal_name] = np.empty((0, 1), dtype=np.int16)

    return result
