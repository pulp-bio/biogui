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

The gear-icon dialog exposes both the ADS1298 settings (see
biogapultra_ads.ads_config.AdsConfig) and the WULPUS PRO settings in one
window; accepting rebuilds both.
"""

import copy
import logging
import types

import numpy as np
from PySide6.QtWidgets import QWidget

from biogui.platforms.biogapultra.biogapultra_ads import ads_config
from biogui.platforms.biogapultra.biogapultra_ads.ads_config_widget import (
    AdsConfigWidget,
)
from biogui.platforms.biogapultra.connectivity_commands import START_EMG_STREAMING, STOP_EMG_STREAMING, START_WULPUS_STREAMING, STOP_WULPUS_STREAMING
from biogui.platforms.biogapultra.shared_config_dialog import openDialogShell
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
_N_CH           = 8
_BYTES_CH       = 3
_N_SAMPLES      = 4
_ADS_BYTES      = _N_CH * _BYTES_CH
_SAMPLE_OFFSETS = [7 + i * 50 for i in range(_N_SAMPLES)]

_ads_config = ads_config.DEFAULT_CONFIG
_SCALE = ads_config.scale_uv(_ads_config)   # ADC → µV; rebuilt on reconfiguration

# ── WULPUS configuration ───────────────────────────────────────────────────
wulpus_config = create_default_biceps_wulpus_uss_config()

# ── BLE framing constants ──────────────────────────────────────────────────
_BLE_PACKET_SIZE    = 211
_BLE_WULPUS_HEADERS = (0x10, 0x11, 0x12, 0x13)
_EXG_HEADER         = 0x55
_WULPUS_SPI_BYTES   = 201  # SPI payload bytes per chunk; starts at byte 7
# Each WULPUS chunk carries the header/counter/timestamp prefix (harmonized with
# ExG/MIC/PPG); metadata is mirrored into every chunk (see firmware WULPUS_META_*):
_WULPUS_SPI_OFF      = 7    # SPI payload starts here in each chunk
_WULPUS_META_CNT_OFF = 1    # frame counter (uint16 LE)
_WULPUS_META_TS_OFF  = 3    # microsecond timestamp (uint32 LE)


packetSize: int = _BLE_PACKET_SIZE

headerByte: int = 0x55
"""Expected first byte of each packet when using TCP client data source to detect and resync from a misaligned stream."""

tailerByte: int = 0xAA
"""Expected last byte of each packet when using TCP client data source to detect and resync from a misaligned stream."""


def _build_sig_info(wulpus_cfg: WulpusUssConfig, ads: ads_config.AdsConfig) -> tuple[dict, dict[int, str]]:
    """Build sigInfo + config_to_signal_name for a given WULPUS config and ADS
    config. Shared by the module-level defaults and the reconfiguration dialog,
    so the two can never drift apart."""
    meas_period_s       = wulpus_cfg.meas_period / 1e6
    period_per_config_s = meas_period_s * wulpus_cfg.num_txrx_configs
    accel_enabled        = is_accelerometer_enabled_from_config(wulpus_cfg)
    num_us_samples       = get_num_us_samples_from_config(wulpus_cfg)
    us_fs                = num_us_samples / period_per_config_s
    adc_start_delay      = (wulpus_cfg.start_adcsampl - wulpus_cfg.start_ppg) * 1e-6

    sig_info: dict = {}
    config_to_signal_name: dict[int, str] = {}
    for cfg_id in range(wulpus_cfg.num_txrx_configs):
        rx_ch = get_rx_channel_for_config(wulpus_cfg, cfg_id)
        if rx_ch is None:
            continue
        sig_name = (
            "ultrasound" if wulpus_cfg.num_txrx_configs == 1
            else f"ultrasound_cfg{cfg_id}_rx{rx_ch}"
        )
        config_to_signal_name[cfg_id] = sig_name
        sig_info[sig_name] = {
            "fs": us_fs,
            "nCh": 1,
            "extras": {
                "type": "ultrasound",
                "config_id": cfg_id,
                "rx_channel": rx_ch,
                "num_samples": num_us_samples,
                "meas_period": wulpus_cfg.meas_period,
                "adc_sampling_freq": wulpus_cfg.sampling_freq,
                "adc_start_delay": adc_start_delay,
            },
        }

    sig_info.update(get_standard_signal_definitions_for_mode(meas_period_s, accel_enabled))

    emg_fs = ads_config.sample_rate_hz(ads)
    emg_packet_rate = emg_fs / _N_SAMPLES
    sig_info["emg_A"] = {
        "fs": emg_fs,
        "nCh": _N_CH,
        "extras": {"type": "time-series", **ads_config.extras_for(ads)},
    }
    sig_info["emg_B"]         = {"fs": emg_fs, "nCh": _N_CH, "extras": {"type": "time-series"}}
    # ExG packet counter + µs timestamp: selectable in the wizard like emg_A/emg_B,
    # but off by default (mirrors the standalone ExG interface).
    sig_info["emg_counter"]   = {"fs": emg_packet_rate, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}}
    sig_info["emg_timestamp"] = {"fs": emg_packet_rate, "nCh": 1, "extras": {"type": "time-series", "plotByDefault": False}}

    if not sig_info:
        raise ValueError("No active RX configurations in WULPUS setup.")

    return sig_info, config_to_signal_name


sigInfo, config_to_signal_name = _build_sig_info(wulpus_config, _ads_config)

startSeq: list[bytes | float] = [
    # WULPUS's own start sequence first, unmodified and uninterrupted --
    # byte-for-byte and timing-wise the same as interface_biogapultra_wulpus_pro.py's
    # standalone sequence, so WULPUS sees the same conditions here as it does
    # running alone. EMG starts only once WULPUS's sequence has fully gone out.
    bytes([START_WULPUS_STREAMING]),
    wulpus_config.get_restart_package(),    # MSP430 reset
    wulpus_config.get_conf_package(),       # MSP430 config + start
    bytes([START_EMG_STREAMING]) + ads_config.to_bytes(_ads_config),
]

stopSeq: list[bytes | float] = [
    # WULPUS's own stop sequence first, unmodified and uninterrupted -- same
    # reasoning as startSeq above.
    bytes([STOP_WULPUS_STREAMING]),
    wulpus_config.get_restart_package(),
    bytes([STOP_EMG_STREAMING]),
]

_wulpus_buf: list[bytes] = []


def decodeFn(data: bytes) -> dict[str, np.ndarray]:
    """Decode one 211-byte packet from the combined EMG+WULPUS stream."""
    global _wulpus_buf

    header = data[0]

    # Build empty result from current sigInfo so it stays correct after reconfiguration.
    result: dict[str, np.ndarray] = {}
    for _n in sigInfo:
        # Empty placeholders MUST share the dtype of the filled arrays below —
        # the file writer captures each signal's dtype from the first array it
        # sees (often an empty one), so a mismatch corrupts recordings.
        if _n in ("acquisition_number", "emg_counter", "wulpus_counter"):
            result[_n] = np.empty((0, 1), dtype=np.uint16)
        elif _n in ("emg_timestamp", "wulpus_timestamp"):
            result[_n] = np.empty((0, 1), dtype=np.uint32)
        elif _n == "tx_rx_id":
            result[_n] = np.empty((0, 1), dtype=np.uint8)
        elif _n == "imu":
            result[_n] = np.empty((0, 3), dtype=np.int16)
        elif _n in ("emg_A", "emg_B"):
            result[_n] = np.empty((0, _N_CH), dtype=np.float32)
        else:
            result[_n] = np.empty((0, 1), dtype=np.int16)

    if header == _EXG_HEADER:
        rows_A = np.empty((_N_SAMPLES, _N_CH), dtype=np.float32)
        rows_B = np.empty((_N_SAMPLES, _N_CH), dtype=np.float32)
        for s, base in enumerate(_SAMPLE_OFFSETS):
            rows_A[s] = ads_config.unpack_ads_channel_block(data, base, _SCALE, _N_CH, _BYTES_CH)
            rows_B[s] = ads_config.unpack_ads_channel_block(data, base + _ADS_BYTES, _SCALE, _N_CH, _BYTES_CH)
        counter = int.from_bytes(data[1:3], "little")
        timestamp = int.from_bytes(data[3:7], "little")
        result["emg_A"]         = rows_A
        result["emg_B"]         = rows_B
        result["emg_counter"]   = np.array([[counter]], dtype=np.uint16)
        result["emg_timestamp"] = np.array([[timestamp]], dtype=np.uint32)
        return result

    if header == 0x10:
        if _wulpus_buf:
            logger.warning("EMG+WULPUS: 0x10 before previous frame completed — resyncing")
        _wulpus_buf = [bytes(data[_WULPUS_SPI_OFF:_WULPUS_SPI_OFF + _WULPUS_SPI_BYTES])]
        return result

    if _wulpus_buf and header == _BLE_WULPUS_HEADERS[len(_wulpus_buf)]:
        _wulpus_buf.append(bytes(data[_WULPUS_SPI_OFF:_WULPUS_SPI_OFF + _WULPUS_SPI_BYTES]))
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
    # Per-frame metadata from the padding tail of the 4th chunk (`data`).
    wulpus_counter   = int.from_bytes(data[_WULPUS_META_CNT_OFF:_WULPUS_META_CNT_OFF + 2], "little")
    wulpus_timestamp = int.from_bytes(data[_WULPUS_META_TS_OFF:_WULPUS_META_TS_OFF + 4], "little")

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
    result["wulpus_counter"]     = np.array([[wulpus_counter]], dtype=np.uint16)
    result["wulpus_timestamp"]   = np.array([[wulpus_timestamp]], dtype=np.uint32)
    if _acc and imu_data is not None:
        result["imu"] = imu_data.reshape(1, 3)
    for sig_name in config_to_signal_name.values():
        if config_to_signal_name.get(tx_rx_id) == sig_name:
            result[sig_name] = us_data.reshape(-1, 1)

    return result


# ── ADS1298 + WULPUS reconfiguration support ──────────────────────────────

def _configure_emg_wulpus_module(
    parent: QWidget,
    interface_module: InterfaceModule,
) -> InterfaceModule | None:
    """Open the ADS1298 + WULPUS PRO config dialogs and return an updated
    EMG+WULPUS module."""
    decode_globals = getattr(interface_module.decodeFn, "__globals__", {})
    current_wulpus_config = decode_globals.get("wulpus_config")
    current_ads = ads_config.settings_from_sig_info(interface_module.sigInfo, "emg_A")

    ads_widget = AdsConfigWidget(parent)
    ads_widget.loadSettings(current_ads)

    wulpus_widget = WulpusConfigWidget(parent)
    if isinstance(current_wulpus_config, WulpusUssConfig):
        wulpus_widget.load_config(copy.deepcopy(current_wulpus_config))
    # The shell's own Ok button now drives acceptance for both sections.
    wulpus_widget.applyConfigButton.setVisible(False)

    configured: list[InterfaceModule | None] = [None]

    def _apply() -> None:
        new_ads = ads_widget.currentSettings()
        new_cfg = wulpus_widget.get_current_config()

        new_sig, new_c2s = _build_sig_info(new_cfg, new_ads)

        new_start = [
            # See startSeq's comment: WULPUS's own sequence first, unmodified.
            bytes([START_WULPUS_STREAMING]),
            new_cfg.get_restart_package(),
            new_cfg.get_conf_package(),
            bytes([START_EMG_STREAMING]) + ads_config.to_bytes(new_ads),
        ]
        new_stop = [bytes([STOP_WULPUS_STREAMING]),
                    new_cfg.get_restart_package(),
                    bytes([STOP_EMG_STREAMING])]

        g = dict(interface_module.decodeFn.__globals__)
        g["wulpus_config"]         = new_cfg
        g["sigInfo"]               = new_sig
        g["config_to_signal_name"] = new_c2s
        g["_SCALE"]                = ads_config.scale_uv(new_ads)
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

    if not openDialogShell(
        parent, [ads_widget, wulpus_widget], "EMG + WULPUS PRO Configuration", onAccept=_apply
    ):
        return None
    return configured[0]


platformConfig = PlatformConfig(
    id="emg_wulpus",
    configureInterfaceModule=_configure_emg_wulpus_module,
    configWidgetClass=WulpusConfigWidget,
    hasInlineConfigAction=True,
    inlineActionIconName="preferences-system",
    inlineActionToolTip="Configure ADS1298 + WULPUS PRO",
)
