# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""WULPUS ultrasound hardware: protocol constants and USS configuration."""

from .protocol import (
    ACQ_LENGTH_SAMPLES,
    MAX_CH_ID,
    NUM_IMU_SAMPLES,
    NUM_US_SAMPLES,
    PACKAGE_LEN,
    PGA_GAIN,
    PGA_GAIN_REG,
    RX_MAP,
    START_BYTE_CONF_PACK,
    START_BYTE_RESTART,
    TX_MAP,
    TX_RX_MAX_NUM_OF_CONFIGS,
    USS_CAPTURE_ACQ_RATES,
    USS_CAPTURE_OVER_SAMPLE_RATES,
    USS_CAPT_OVER_SAMPLE_RATES_REG,
    WulpusRxTxConfigGen,
    WulpusUssConfig,
)

__all__ = [
    "ACQ_LENGTH_SAMPLES",
    "MAX_CH_ID",
    "NUM_IMU_SAMPLES",
    "NUM_US_SAMPLES",
    "PACKAGE_LEN",
    "PGA_GAIN",
    "PGA_GAIN_REG",
    "RX_MAP",
    "START_BYTE_CONF_PACK",
    "START_BYTE_RESTART",
    "TX_MAP",
    "TX_RX_MAX_NUM_OF_CONFIGS",
    "USS_CAPTURE_ACQ_RATES",
    "USS_CAPTURE_OVER_SAMPLE_RATES",
    "USS_CAPT_OVER_SAMPLE_RATES_REG",
    "WulpusRxTxConfigGen",
    "WulpusUssConfig",
]
