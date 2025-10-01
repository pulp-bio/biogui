import logging
import numpy as np

# baudrate = 4000000
ACQ_LENGTH_SAMPLES = 400

# Protocol related
START_BYTE_CONF_PACK = 250
START_BYTE_RESTART = 251
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
            raise ValueError(
                "Maximum number of configs is " + str(TX_RX_MAX_NUM_OF_CONFIGS)
            )

        if any(channel > MAX_CH_ID for channel in tx_channels) or any(
            channel > MAX_CH_ID for channel in rx_channels
        ):
            raise ValueError("RX and TX channel ID must be less than " + str(MAX_CH_ID))

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
rx_tx_config = WulpusRxTxConfigGen()
rx_tx_config.add_config(tx_channels=[7], rx_channels=[7], optimized_switching=True)


# ! number of samples is hardcoded in the wulpus firmware at the moment to 400
wulpus_config = WulpusUssConfig(
    num_acqs=100,
    dcdc_turnon=100,
    meas_period=228885,
    trans_freq=2250000,
    pulse_freq=1000000,
    num_pulses=11,
    sampling_freq=4000000.0,
    num_samples=400,
    rx_gain=6.8,
    num_txrx_configs=1,
    tx_configs=rx_tx_config.get_tx_configs(),  # only channel 7 with optimized switching
    rx_configs=rx_tx_config.get_rx_configs(),  # only channel 7 with optimized switching
    start_hvmuxrx=500,
    start_ppg=500,
    turnon_adc=5,
    start_pgainbias=5,
    start_adcsampl=503,
    restart_capt=3000,
    capt_timeout=3000,
)


packetSize: int = wulpus_config.num_samples * 2 + 7 + 6
"""Number of bytes in each package."""

startSeq: list[bytes | float] = [
    wulpus_config.get_restart_package(),  # Send restart first
    2.5,  # Wait 2.5 seconds (biogui convention: floats are delays)
    wulpus_config.get_conf_package(),  # Send configuration,
]
"""
Sequence of commands (as bytes) to start the device; floats are
interpreted as delays (in seconds) between commands.
"""


# startSeq = [
#     b"\xfb\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
#     2.5,
#     b'\xfa\x03\x00K\x1d\x10U"\x00@B\x0f\x00\x0b\x01\x00 \x03!\x01\x00\xc0\x00@\xa0\x0f\xc4\t\x19\x00\x19\x00\xd3\t\xa9\x03\xa6\x0e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
# ]


stopSeq: list[bytes | float] = [
    wulpus_config.get_restart_package(),  # Send restart command aka stop command,
    # 1.0,
]
"""
Sequence of commands (as bytes) to stop the device; floats are
interpreted as delays (in seconds) between commands.
"""

sigInfo: dict = {
    "ultrasound": {
        "fs": int(wulpus_config.sampling_freq / 1000),  # Convert to kHz
        "nCh": 1,  # Single channel A-mode data
    }
}
"""Dictionary containing the signals information."""


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """
    Function to decode the binary data received from the device into signals.

    Parameters
    ----------
    data : bytes
        A packet of bytes.

    Returns
    -------
    dict of (str: ndarray)
        Dictionary containing the signal data packets, each with shape (nSamp, nCh);
        the keys must match with those of the "sigInfo" dictionary.
    """

    logging.info(f"Wulpus Interface: {data[:20]=}")

    # Check if data starts with b'START\n' start sequence (i.e. if the data is aligned)
    if data[:6] != b'START\n':
        raise ValueError("WULPUS INTERFACE ERROR: Data packet does not start with expected b'START\\n' sequence. Hence, the data is not aligned.")

    # remove b'START\n' from data
    data = data[6:]

    rf_arr = np.frombuffer(data[7:], dtype="<i2")
    acq_nr = data[4]
    tx_rx_id = np.frombuffer(data[5:7], dtype="<u2")[0]

    # print(f"acq_nr: {acq_nr}, tx_rx_id: {tx_rx_id}")
    # print(f"rf_arr: {rf_arr}")

    return {"ultrasound": rf_arr.reshape(-1, 1)}


print(f"{packetSize=}")
# print(f"{startSeq}")
# print(f"{stopSeq}")
