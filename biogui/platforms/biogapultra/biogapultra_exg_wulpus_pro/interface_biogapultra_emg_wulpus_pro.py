# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Combined EMG (ADS1298) + WULPUS PRO interface for BioGAP (nRF5340).

Identical to interface_eeg_wulpus.py except:
  - BLE start command: 37 (START_EMG_STREAMING)  instead of 18
  - BLE stop  command: 38 (STOP_EMG_STREAMING)   instead of 19
  - Signal names: emg_A / emg_B                  instead of eeg_A / eeg_B
"""

import copy
import logging
import types

import numpy as np
from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QWidget

from biogui.platforms.wulpus_pro.defaults import create_default_biceps_wulpus_uss_config
from biogui.platforms.wulpus_pro.protocol import (
    NUM_IMU_SAMPLES,
    WulpusUssConfig,
    get_num_us_samples_from_config,
    is_accelerometer_enabled_from_config,
)
from biogui.platforms.wulpus_pro.runtime import (
    get_rx_channel_for_config,
    get_standard_signal_definitions_for_mode,
)
from biogui.platforms.wulpus_pro.wulpus_pro_config_widget import WulpusConfigWidget
from biogui.utils import InterfaceModule, PlatformConfig

logger = logging.getLogger(__name__)

# ── ADS1298 decode constants ───────────────────────────────────────────────
_VREF  = 2.5
_GAIN  = 6
_NBIT  = 24
_SCALE = _VREF / (_GAIN * (2 ** (_NBIT - 1) - 1)) * 1e6

_N_SAMPLES      = 4
_N_CH           = 8
_BYTES_CH       = 3
_ADS_BYTES      = _N_CH * _BYTES_CH
_SAMPLE_OFFSETS = [7 + i * 50 for i in range(_N_SAMPLES)]

# ── WULPUS configuration ───────────────────────────────────────────────────
wulpus_config = create_default_biceps_wulpus_uss_config()

# ── BLE framing constants ──────────────────────────────────────────────────
_BLE_PACKET_SIZE    = 211
_BLE_WULPUS_HEADERS = (0x10, 0x11, 0x12, 0x13)
_EXG_HEADER         = 0x55
_WULPUS_SPI_BYTES   = 201  # real bytes per BLE chunk; strip 9-byte zero-padding tail

packetSize: int = _BLE_PACKET_SIZE

startSeq: list[bytes | float] = [
    bytes([20, 1, 0]),                       # SET_BOARD_STATE → Nordic streaming
    0.2,
    bytes([37]),                             # START_EMG_STREAMING
    0.2,
    wulpus_config.get_restart_package(),
    0.5,
    wulpus_config.get_conf_package(),
]

stopSeq: list[bytes | float] = [
    bytes([38]),                             # STOP_EMG_STREAMING
    wulpus_config.get_restart_package(),
]

# ── Build sigInfo ──────────────────────────────────────────────────────────
_meas_period_s       = wulpus_config.meas_period / 1e6
_period_per_config_s = _meas_period_s * wulpus_config.num_txrx_configs
_accel_enabled       = is_accelerometer_enabled_from_config(wulpus_config)
_num_us_samples      = get_num_us_samples_from_config(wulpus_config)
_us_fs               = _num_us_samples / _period_per_config_s
_adc_start_delay     = (wulpus_config.start_adcsampl - wulpus_config.start_ppg) * 1e-6

sigInfo: dict = {}

config_to_signal_name: dict[int, str] = {}
for _cfg_id in range(wulpus_config.num_txrx_configs):
    _rx_ch = get_rx_channel_for_config(wulpus_config, _cfg_id)
    if _rx_ch is None:
        continue
    _sig = (
        "ultrasound" if wulpus_config.num_txrx_configs == 1
        else f"ultrasound_cfg{_cfg_id}_rx{_rx_ch}"
    )
    config_to_signal_name[_cfg_id] = _sig
    sigInfo[_sig] = {
        "fs": _us_fs,
        "nCh": 1,
        "extras": {
            "type": "ultrasound",
            "config_id": _cfg_id,
            "rx_channel": _rx_ch,
            "num_samples": _num_us_samples,
            "meas_period": wulpus_config.meas_period,
            "adc_sampling_freq": wulpus_config.sampling_freq,
            "adc_start_delay": _adc_start_delay,
        },
    }

sigInfo.update(get_standard_signal_definitions_for_mode(_meas_period_s, _accel_enabled))
sigInfo["emg_A"]       = {"fs": 250.0, "nCh": _N_CH, "extras": {"type": "time-series"}}
sigInfo["emg_B"]       = {"fs": 250.0, "nCh": _N_CH, "extras": {"type": "time-series"}}
sigInfo["emg_counter"] = {"fs": 62.5, "nCh": 1, "hidden": True}

if not sigInfo:
    raise ValueError("No active RX configurations in WULPUS setup.")

_wulpus_buf: list[bytes] = []


def _unpack_ads_block(data: bytes, offset: int) -> np.ndarray:
    arr = np.empty(_N_CH, dtype=np.float32)
    for ch in range(_N_CH):
        b = offset + ch * _BYTES_CH
        raw = (data[b] << 16) | (data[b + 1] << 8) | data[b + 2]
        if raw >= 0x800000:
            raw -= 0x1000000
        arr[ch] = raw * _SCALE
    return arr


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """Decode one 211-byte packet from the combined EMG+WULPUS stream."""
    global _wulpus_buf

    header = data[0]

    # Build empty result from current sigInfo so it stays correct after reconfiguration.
    result: dict[str, np.ndarray] = {}
    for _n in sigInfo:
        if _n == "acquisition_number":
            result[_n] = np.empty((0, 1), dtype=np.uint16)
        elif _n in ("tx_rx_id", "emg_counter"):
            result[_n] = np.empty((0, 1), dtype=np.uint8)
        elif _n == "imu":
            result[_n] = np.empty((0, 3), dtype=np.int16)
        elif _n.startswith("emg_"):
            result[_n] = np.empty((0, _N_CH), dtype=np.float32)
        else:
            result[_n] = np.empty((0, 1), dtype=np.int16)

    if header == _EXG_HEADER:
        rows_A = np.empty((_N_SAMPLES, _N_CH), dtype=np.float32)
        rows_B = np.empty((_N_SAMPLES, _N_CH), dtype=np.float32)
        for s, base in enumerate(_SAMPLE_OFFSETS):
            rows_A[s] = _unpack_ads_block(data, base)
            rows_B[s] = _unpack_ads_block(data, base + _ADS_BYTES)
        counter = int.from_bytes(data[1:3], "little")
        result["emg_A"]       = rows_A
        result["emg_B"]       = rows_B
        result["emg_counter"] = np.array([[counter]], dtype=np.uint16)
        return result

    if header == 0x10:
        if _wulpus_buf:
            logger.warning("EMG+WULPUS: 0x10 before previous frame completed — resyncing")
        _wulpus_buf = [bytes(data[1:1 + _WULPUS_SPI_BYTES])]
        return result

    if _wulpus_buf and header == _BLE_WULPUS_HEADERS[len(_wulpus_buf)]:
        _wulpus_buf.append(bytes(data[1:1 + _WULPUS_SPI_BYTES]))
    else:
        logger.warning("EMG+WULPUS: unexpected header 0x%02X — resyncing", header)
        _wulpus_buf = []
        return result

    if len(_wulpus_buf) < 4:
        return result

    payload = b"".join(_wulpus_buf)
    _wulpus_buf = []

    tx_rx_id = payload[1]
    acq_nr   = int.from_bytes(payload[2:4], "little")
    rf_arr   = np.frombuffer(payload[4:], dtype="<i2")

    print(
        f"[WULPUS] SOF=0x{payload[0]:02X} tx_rx_id={tx_rx_id} acq_nr={acq_nr} "
        f"rf_samples={len(rf_arr)} raw_header_bytes={payload[:8].hex()}"
    )

    # Compute these from wulpus_config so they reflect any reconfiguration.
    _n_us = get_num_us_samples_from_config(wulpus_config)
    _acc  = is_accelerometer_enabled_from_config(wulpus_config)
    us_data  = rf_arr[:_n_us]
    imu_data = None
    if _acc:
        imu_data = rf_arr[_n_us: _n_us + NUM_IMU_SAMPLES]

    result["acquisition_number"] = np.array([[acq_nr]], dtype=np.uint16)
    result["tx_rx_id"]           = np.array([[tx_rx_id]], dtype=np.uint8)
    if _acc and imu_data is not None:
        result["imu"] = imu_data.reshape(1, 3)
    for sig_name in config_to_signal_name.values():
        if config_to_signal_name.get(tx_rx_id) == sig_name:
            result[sig_name] = us_data.reshape(-1, 1)

    return result


# ── WULPUS reconfiguration support ────────────────────────────────────────

def _configure_emg_wulpus_module(
    parent: QWidget,
    interface_module: InterfaceModule,
) -> InterfaceModule | None:
    """Open the WULPUS PRO config dialog and return an updated EMG+WULPUS module."""
    decode_globals = getattr(interface_module.decodeFn, "__globals__", {})
    current_config = decode_globals.get("wulpus_config")

    dialog = QDialog(parent)
    dialog.setWindowTitle("EMG + WULPUS PRO Configuration")
    dialog.setModal(True)
    dialog.resize(650, 750)
    layout = QVBoxLayout(dialog)
    config_widget = WulpusConfigWidget(dialog)
    layout.addWidget(config_widget)

    if isinstance(current_config, WulpusUssConfig):
        config_widget.load_config(copy.deepcopy(current_config))

    configured: list[InterfaceModule | None] = [None]

    def _apply_and_accept() -> None:
        try:
            new_cfg = config_widget.get_current_config()
            mp_s  = new_cfg.meas_period / 1e6
            ppc_s = mp_s * new_cfg.num_txrx_configs
            acc   = is_accelerometer_enabled_from_config(new_cfg)
            n_us  = get_num_us_samples_from_config(new_cfg)
            us_fs = n_us / ppc_s
            adc_delay = (new_cfg.start_adcsampl - new_cfg.start_ppg) * 1e-6

            new_c2s: dict[int, str] = {}
            new_sig: dict = {}
            for _cid in range(new_cfg.num_txrx_configs):
                rx_ch = get_rx_channel_for_config(new_cfg, _cid)
                if rx_ch is None:
                    continue
                _sname = (
                    "ultrasound" if new_cfg.num_txrx_configs == 1
                    else f"ultrasound_cfg{_cid}_rx{rx_ch}"
                )
                new_c2s[_cid] = _sname
                new_sig[_sname] = {
                    "fs": us_fs, "nCh": 1,
                    "extras": {
                        "type": "ultrasound",
                        "config_id": _cid,
                        "rx_channel": rx_ch,
                        "num_samples": n_us,
                        "meas_period": new_cfg.meas_period,
                        "adc_sampling_freq": new_cfg.sampling_freq,
                        "adc_start_delay": adc_delay,
                    },
                }
            new_sig.update(get_standard_signal_definitions_for_mode(mp_s, acc))
            new_sig["emg_A"]       = {"fs": 250.0, "nCh": _N_CH, "extras": {"type": "time-series"}}
            new_sig["emg_B"]       = {"fs": 250.0, "nCh": _N_CH, "extras": {"type": "time-series"}}
            new_sig["emg_counter"] = {"fs": 62.5, "nCh": 1, "hidden": True}

            if not new_sig:
                raise ValueError("No active RX configurations found.")

            new_start = [
                bytes([20, 1, 0]), 0.2,
                bytes([37]), 0.2,
                new_cfg.get_restart_package(), 0.5,
                new_cfg.get_conf_package(),
            ]
            new_stop = [bytes([38]), new_cfg.get_restart_package()]

            g = dict(interface_module.decodeFn.__globals__)
            g["wulpus_config"]         = new_cfg
            g["sigInfo"]               = new_sig
            g["config_to_signal_name"] = new_c2s
            new_decode = types.FunctionType(
                interface_module.decodeFn.__code__,
                g,
                interface_module.decodeFn.__name__,
                interface_module.decodeFn.__defaults__,
                interface_module.decodeFn.__closure__,
            )
            configured[0] = InterfaceModule(
                packetSize=interface_module.packetSize,
                startSeq=new_start,
                stopSeq=new_stop,
                sigInfo=new_sig,
                decodeFn=new_decode,
                platformConfig=interface_module.platformConfig,
            )
            dialog.accept()
        except Exception as err:
            QMessageBox.critical(dialog, "Configuration Error", f"Invalid configuration: {err}")

    config_widget.applyConfigButton.clicked.connect(_apply_and_accept)

    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return configured[0]


platformConfig = PlatformConfig(
    id="emg_wulpus",
    configureInterfaceModule=_configure_emg_wulpus_module,
    configWidgetClass=WulpusConfigWidget,
    hasInlineConfigAction=True,
    inlineActionIconName="preferences-system",
    inlineActionToolTip="Configure WULPUS PRO",
)
