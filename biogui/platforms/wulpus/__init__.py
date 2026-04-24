# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""WULPUS curated platform integration."""

from biogui.utils import PlatformConfig

from .defaults import create_default_biceps_wulpus_uss_config
from .protocol import (
    ACQ_LENGTH_SAMPLES,
    MAX_CH_ID,
    MEAS_MODE_ACCELEROMETER_ENABLED,
    MEAS_MODE_ULTRASOUND_ONLY,
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
    get_num_us_samples_from_config,
    get_num_us_samples_from_mode,
    is_accelerometer_enabled_from_config,
    is_accelerometer_enabled_from_mode,
)
from .runtime import (
    build_interface_module,
    configure_interface_module,
    create_default_config,
    get_rx_channel_for_config,
    get_standard_signal_definitions_for_mode,
    isolate_wulpus_interface_module,
    read_current_config,
)
from .wulpus_config_widget import WulpusConfigWidget

WULPUS_PLATFORM = PlatformConfig(
    id="wulpus",
    configureInterfaceModule=configure_interface_module,
    configWidgetClass=WulpusConfigWidget,
    hasInlineConfigAction=True,
    inlineActionIconName="preferences-system",
    inlineActionToolTip="Configure WULPUS",
)

__all__ = [
    "ACQ_LENGTH_SAMPLES",
    "MAX_CH_ID",
    "MEAS_MODE_ACCELEROMETER_ENABLED",
    "MEAS_MODE_ULTRASOUND_ONLY",
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
    "WulpusConfigWidget",
    "WulpusRxTxConfigGen",
    "WulpusUssConfig",
    "WULPUS_PLATFORM",
    "create_default_biceps_wulpus_uss_config",
    "build_interface_module",
    "configure_interface_module",
    "create_default_config",
    "get_num_us_samples_from_config",
    "get_num_us_samples_from_mode",
    "get_rx_channel_for_config",
    "get_standard_signal_definitions_for_mode",
    "is_accelerometer_enabled_from_config",
    "is_accelerometer_enabled_from_mode",
    "isolate_wulpus_interface_module",
    "read_current_config",
]
