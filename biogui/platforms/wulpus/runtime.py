# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
from typing import Any

from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QWidget

from biogui.utils import InterfaceModule

from .protocol import (
    ACQ_LENGTH_SAMPLES,
    MEAS_MODE_ACCELEROMETER_ENABLED,
    MEAS_MODE_ULTRASOUND_ONLY,
    PGA_GAIN,
    RX_MAP,
    USS_CAPTURE_ACQ_RATES,
    WulpusRxTxConfigGen,
    WulpusUssConfig,
    get_num_us_samples_from_config,
    is_accelerometer_enabled_from_config,
)
from .wulpus_config_widget import WulpusConfigWidget


def get_rx_channel_for_config(config: WulpusUssConfig, config_id: int) -> int | None:
    """Get the active RX channel for a specific TX/RX configuration."""
    if config_id >= config.num_txrx_configs:
        return None

    rx_config_bits = config.rx_configs[config_id]
    for channel_id in range(8):
        switch_id = RX_MAP[channel_id]
        if (rx_config_bits >> switch_id) & 1:
            return channel_id

    return None


def get_standard_signal_definitions_for_mode(
    meas_period_s: float,
    accelerometer_enabled: bool,
) -> dict:
    """Return the standard WULPUS metadata and optional IMU signals."""
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
    }

    if accelerometer_enabled:
        definitions["imu"] = {
            "fs": fs,
            "nCh": 3,
            "extras": {"type": "time-series"},
        }

    return definitions


def create_default_config() -> WulpusUssConfig:
    """Create the default WULPUS configuration used by the bundled interface."""
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
        sampling_freq=USS_CAPTURE_ACQ_RATES[0],
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


def read_current_config(interface_module: InterfaceModule) -> WulpusUssConfig | None:
    """Extract the current WULPUS config from an interface module when available."""
    decode_globals = getattr(interface_module.decodeFn, "__globals__", {})
    current_config = decode_globals.get("wulpus_config")
    if isinstance(current_config, WulpusUssConfig):
        return current_config
    return None


def _resolve_num_us_samples(
    decode_globals: dict[str, Any],
    wulpus_config: WulpusUssConfig,
) -> int:
    """Resolve ultrasound sample count from interface helpers or default logic."""
    get_num_us_samples = decode_globals.get("get_num_us_samples_from_config")
    if not callable(get_num_us_samples):
        get_num_us_samples = decode_globals.get("get_num_us_samples")

    if callable(get_num_us_samples):
        resolved_samples = get_num_us_samples(wulpus_config)
        if not isinstance(resolved_samples, bool):
            try:
                return int(resolved_samples)
            except (TypeError, ValueError):
                pass

    return get_num_us_samples_from_config(wulpus_config)


def build_interface_module(
    interface_module: InterfaceModule,
    wulpus_config: WulpusUssConfig,
) -> InterfaceModule:
    """Create a WULPUS interface module with parameters updated for a single source."""
    decode_fn = interface_module.decodeFn
    decode_globals = getattr(decode_fn, "__globals__", {})

    packet_size = wulpus_config.num_samples * 2 + 7 + 6
    start_seq = [
        wulpus_config.get_restart_package(),
        0.5,
        wulpus_config.get_conf_package(),
    ]
    stop_seq = [wulpus_config.get_restart_package()]

    num_us_samples = _resolve_num_us_samples(decode_globals, wulpus_config)
    accelerometer_enabled = is_accelerometer_enabled_from_config(wulpus_config)
    get_rx_channel = decode_globals.get("get_rx_channel_for_config", get_rx_channel_for_config)
    get_standard_signal_definitions = decode_globals.get("get_standard_signal_definitions")
    get_standard_signal_definitions_for_mode_fn = decode_globals.get(
        "get_standard_signal_definitions_for_mode"
    )

    meas_period_s = wulpus_config.meas_period / 1e6
    period_per_config_s = meas_period_s * wulpus_config.num_txrx_configs
    samples_per_second = num_us_samples / period_per_config_s
    adc_start_delay = (wulpus_config.start_adcsampl - wulpus_config.start_ppg) * 1e-6

    sig_info = {}
    config_to_signal_name: dict[int, str] = {}
    for config_id in range(wulpus_config.num_txrx_configs):
        rx_channel = get_rx_channel(wulpus_config, config_id)
        if rx_channel is None:
            continue

        signal_name = (
            "ultrasound"
            if wulpus_config.num_txrx_configs == 1
            else f"ultrasound_cfg{config_id}_rx{rx_channel}"
        )
        config_to_signal_name[config_id] = signal_name
        sig_info[signal_name] = {
            "fs": samples_per_second,
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

    if callable(get_standard_signal_definitions_for_mode_fn):
        standard_sig_info = get_standard_signal_definitions_for_mode_fn(
            meas_period_s,
            accelerometer_enabled,
        )
    elif callable(get_standard_signal_definitions):
        try:
            standard_sig_info = get_standard_signal_definitions(
                meas_period_s,
                accelerometer_enabled,
            )
        except TypeError:
            standard_sig_info = get_standard_signal_definitions(meas_period_s)
    else:
        standard_sig_info = get_standard_signal_definitions_for_mode(
            meas_period_s,
            accelerometer_enabled,
        )
    if isinstance(standard_sig_info, dict):
        sig_info.update(standard_sig_info)

    if not sig_info:
        raise ValueError(
            "No active RX configurations found in WULPUS setup. "
            "At least one configuration must have an active RX channel."
        )

    decode_globals["wulpus_config"] = wulpus_config
    decode_globals["packetSize"] = packet_size
    decode_globals["startSeq"] = start_seq
    decode_globals["stopSeq"] = stop_seq
    decode_globals["sigInfo"] = sig_info
    decode_globals["config_to_signal_name"] = config_to_signal_name

    return InterfaceModule(
        packetSize=packet_size,
        startSeq=start_seq,
        stopSeq=stop_seq,
        sigInfo=sig_info,
        decodeFn=decode_fn,
        platformConfig=interface_module.platformConfig,
    )


def configure_interface_module(
    parent: QWidget,
    interface_module: InterfaceModule,
) -> InterfaceModule | None:
    """Open the WULPUS configuration dialog and return an updated interface module."""
    current_config = read_current_config(interface_module)
    configured_interface_module: InterfaceModule | None = None

    dialog = QDialog(parent)
    dialog.setWindowTitle("WULPUS Configuration")
    dialog.setModal(True)
    dialog.resize(650, 750)

    layout = QVBoxLayout(dialog)
    config_widget = WulpusConfigWidget(dialog)
    layout.addWidget(config_widget)

    if current_config is not None:
        config_widget.load_config(copy.deepcopy(current_config))

    def _apply_and_accept() -> None:
        nonlocal configured_interface_module
        try:
            new_config = config_widget.get_current_config()
            configured_interface_module = build_interface_module(interface_module, new_config)
            dialog.accept()
        except Exception as err:
            QMessageBox.critical(
                dialog,
                "Configuration Error",
                f"Invalid WULPUS configuration: {err}",
            )

    config_widget.applyConfigButton.clicked.connect(_apply_and_accept)

    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None

    return configured_interface_module
