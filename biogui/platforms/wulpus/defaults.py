# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Default WulpusUssConfig factory for bundled WULPUS interface modules."""

from .protocol import (
    ACQ_LENGTH_SAMPLES,
    MEAS_MODE_ACCELEROMETER_ENABLED,
    WulpusRxTxConfigGen,
    WulpusUssConfig,
)


def create_default_biceps_wulpus_uss_config() -> WulpusUssConfig:
    """Biceps-exercise default used by the stock WULPUS interface .py files."""
    rx_tx_config = WulpusRxTxConfigGen()
    rx_tx_config.add_config(
        tx_channels=[3],
        rx_channels=[3],
        optimized_switching=False,
    )
    return WulpusUssConfig(
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
