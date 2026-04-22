# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
WULPUS hardware configuration widget with preset management.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QRadioButton,
    QStyle,
    QTableWidgetItem,
    QToolButton,
    QWidget,
)

from biogui.hardware.wulpus import (
    MEAS_MODE_ACCELEROMETER_ENABLED,
    MEAS_MODE_ULTRASOUND_ONLY,
    is_accelerometer_enabled_from_mode,
)
from biogui.paths import APP_DIR
from biogui.ui.ui_wulpus_config_widget import Ui_WulpusConfigWidget
from biogui.views.help_dialog import HelpDialog

from ..interfaces import interface_wulpus

logger = logging.getLogger(__name__)


def _is_accelerometer_enabled_from_meas_mode(meas_mode: int) -> bool:
    return is_accelerometer_enabled_from_mode(int(meas_mode))


def _meas_mode_from_accelerometer_enabled(accelerometer_enabled: bool) -> int:
    if accelerometer_enabled:
        return MEAS_MODE_ACCELEROMETER_ENABLED
    return MEAS_MODE_ULTRASOUND_ONLY


def _get_imu_active_from_config_dict(config_dict: dict) -> bool:
    """Extract IMU activity from a preset dictionary."""
    if "imu_active" in config_dict:
        return bool(config_dict["imu_active"])

    meas_mode = int(config_dict.get("meas_mode", MEAS_MODE_ULTRASOUND_ONLY))
    return _is_accelerometer_enabled_from_meas_mode(meas_mode)


class TxRxConfigDialog(QDialog):
    """Dialog for configuring TX/RX channels."""

    CHANNEL_COUNT = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TX/RX Configuration")

        layout = QFormLayout(self)

        tx_widget = QWidget(self)
        tx_layout = QGridLayout(tx_widget)
        tx_layout.setContentsMargins(0, 0, 0, 0)
        self.tx_checkboxes: list[QCheckBox] = []
        for ch in range(self.CHANNEL_COUNT):
            checkbox = QCheckBox(str(ch), tx_widget)
            self.tx_checkboxes.append(checkbox)
            tx_layout.addWidget(checkbox, ch // 4, ch % 4)
        layout.addRow("TX Channels (0-7):", tx_widget)

        rx_widget = QWidget(self)
        rx_layout = QGridLayout(rx_widget)
        rx_layout.setContentsMargins(0, 0, 0, 0)
        self.rx_button_group = QButtonGroup(self)
        self.rx_button_group.setExclusive(True)
        self.rx_radio_buttons: list[QRadioButton] = []
        for ch in range(self.CHANNEL_COUNT):
            radio = QRadioButton(str(ch), rx_widget)
            self.rx_button_group.addButton(radio, ch)
            self.rx_radio_buttons.append(radio)
            rx_layout.addWidget(radio, ch // 4, ch % 4)
        self.rx_radio_buttons[0].setChecked(True)
        layout.addRow("RX Channel (0-7):", rx_widget)

        helper_label = QLabel("TX: multiple channels possible, RX: exactly one channel.", self)
        layout.addRow("", helper_label)

        self.optimized_checkbox = QCheckBox()
        layout.addRow("Optimized Switching:", self.optimized_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)  # type: ignore
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def accept(self):
        try:
            self._parse_channels()
            super().accept()
        except ValueError as err:
            QMessageBox.warning(self, "Invalid Input", str(err))

    def _parse_channels(self) -> tuple[list[int], list[int]]:
        tx = [index for index, checkbox in enumerate(self.tx_checkboxes) if checkbox.isChecked()]
        rx_id = self.rx_button_group.checkedId()
        rx = [rx_id] if 0 <= rx_id < self.CHANNEL_COUNT else []

        if not tx:
            raise ValueError("At least one TX channel required")
        if not rx:
            raise ValueError("Exactly one RX channel must be selected")
        return tx, rx

    def set_config(self, config: dict[str, Any]) -> None:
        tx_channels = config.get("tx_channels", [])
        rx_channels = config.get("rx_channels", [])

        for checkbox in self.tx_checkboxes:
            checkbox.setChecked(False)
        for ch in tx_channels:
            if 0 <= ch < self.CHANNEL_COUNT:
                self.tx_checkboxes[ch].setChecked(True)

        if rx_channels:
            rx_channel = rx_channels[0]
            if 0 <= rx_channel < self.CHANNEL_COUNT:
                self.rx_radio_buttons[rx_channel].setChecked(True)
            else:
                self.rx_radio_buttons[0].setChecked(True)
        else:
            self.rx_radio_buttons[0].setChecked(True)

        self.optimized_checkbox.setChecked(bool(config.get("optimized_switching", False)))

    def get_config(self) -> dict:
        tx, rx = self._parse_channels()
        return {
            "tx_channels": tx,
            "rx_channels": rx,
            "optimized_switching": self.optimized_checkbox.isChecked(),
        }


class WulpusConfigWidget(QWidget, Ui_WulpusConfigWidget):
    """Configuration widget for WULPUS ultrasound hardware parameters."""

    configChanged = Signal(interface_wulpus.WulpusUssConfig)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.configTabWidget.setCurrentIndex(0)

        self._current_config: interface_wulpus.WulpusUssConfig | None = None
        self._tx_rx_configs: list[dict[str, Any]] = []
        self._presets_dir = self._get_presets_directory()
        self._loading_preset = False
        self._updating_tx_rx_table = False
        self._help_content = self._load_help_content()

        self._setup_validators()
        self._populate_combo_boxes()
        self._populate_presets()
        self._setup_help_buttons()
        self._connect_signals()

        logger.info("WulpusConfigWidget initialized")

    def _get_presets_directory(self) -> Path:
        biogui_root = Path(__file__).parent.parent.parent
        presets_dir = biogui_root / "presets" / "wulpus"
        presets_dir.mkdir(parents=True, exist_ok=True)
        return presets_dir

    def _load_help_content(self) -> dict[str, dict]:
        help_file = APP_DIR / "resources" / "help" / "wulpus_settings_help.json"
        if not help_file.exists():
            logger.warning(f"WULPUS help file not found: {help_file}")
            return {}

        try:
            with open(help_file, "r") as file:
                data = json.load(file)
            if isinstance(data, dict):
                return data
        except Exception as err:
            logger.warning(f"Failed to load WULPUS help content: {err}")

        return {}

    def _setup_help_buttons(self) -> None:
        self._attach_help_button(self.basicFormLayout, self.dcdcTurnonLabel, "dcdc_turnon")
        self._attach_help_button(self.basicFormLayout, self.measPeriodLabel, "meas_period")
        self._attach_help_button(self.basicFormLayout, self.transFreqLabel, "imu_active")
        self._attach_help_button(self.basicFormLayout, self.pulseFreqLabel, "pulse_freq")
        self._attach_help_button(self.basicFormLayout, self.numPulsesLabel, "num_pulses")
        self._attach_help_button(self.basicFormLayout, self.samplingFreqLabel, "sampling_freq")
        self._attach_help_button(self.basicFormLayout, self.numSamplesLabel, "num_samples")
        self._attach_help_button(self.basicFormLayout, self.rxGainLabel, "rx_gain")
        self._attach_help_button(self.advancedFormLayout, self.startHvmuxrxLabel, "start_hvmuxrx")
        self._attach_help_button(self.advancedFormLayout, self.startPpgLabel, "start_ppg")
        self._attach_help_button(self.advancedFormLayout, self.turnonAdcLabel, "turnon_adc")
        self._attach_help_button(
            self.advancedFormLayout,
            self.startPgainbiasLabel,
            "start_pgainbias",
        )
        self._attach_help_button(
            self.advancedFormLayout,
            self.startAdcsampleLabel,
            "start_adcsampl",
        )
        self._attach_help_button(self.advancedFormLayout, self.restartCaptLabel, "restart_capt")
        self._attach_help_button(self.advancedFormLayout, self.captTimeoutLabel, "capt_timeout")
        self.txRxInfoLabel.setToolTip(self._help_content.get("tx_rx_configs", {}).get("short", ""))

    def _attach_help_button(self, form_layout: QFormLayout, label: QLabel, help_key: str) -> None:
        row = -1
        for i in range(form_layout.rowCount()):
            item = form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
            if item is None or item.widget() is None:
                continue
            if item.widget() is label:
                row = i
                break

        if row < 0:
            return

        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label.setParent(container)
        layout.addWidget(label, 0, Qt.AlignmentFlag.AlignVCenter)

        info_button = QToolButton(container)
        info_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        )
        info_button.setIconSize(self.style().pixelMetric(QStyle.PixelMetric.PM_SmallIconSize))
        info_button.setText("")
        info_button.setAutoRaise(True)
        info_button.setCursor(Qt.PointingHandCursor)  # type: ignore
        info_button.setToolTip(self._help_content.get(help_key, {}).get("short", "More info"))
        info_button.setFixedSize(18, 18)
        info_button.setStyleSheet(
            """
            QToolButton {
                border: none;
                border-radius: 9px;
                background: transparent;
            }
            QToolButton:hover {
                background: #e9edf5;
            }
            """
        )
        info_button.clicked.connect(lambda _=False, key=help_key: self._show_help_dialog(key))
        layout.addWidget(info_button, 0, Qt.AlignmentFlag.AlignVCenter)

        form_layout.setWidget(row, QFormLayout.ItemRole.LabelRole, container)

    def _show_help_dialog(self, help_key: str) -> None:
        content = self._help_content.get(help_key)
        if content is None:
            QMessageBox.information(self, "Help", "No help available for this parameter yet.")
            return

        title = content.get("title", help_key)
        dialog = HelpDialog(title, content, parent=self)
        dialog.exec()

    def _populate_presets(self) -> None:
        self.presetComboBox.clear()
        self.presetComboBox.addItem("Custom")

        if self._presets_dir.exists():
            preset_files = sorted(self._presets_dir.glob("*.json"))
            for preset_file in preset_files:
                self.presetComboBox.addItem(preset_file.stem)

        self.presetComboBox.setCurrentText("Custom")

    def _normalized_config_dict(self, config_dict: dict) -> dict:
        normalized = dict(config_dict)
        normalized["imu_active"] = _get_imu_active_from_config_dict(normalized)
        normalized.pop("meas_mode", None)

        if "tx_rx_configs" in normalized:
            normalized["tx_rx_configs"] = [
                {
                    "tx_channels": list(cfg.get("tx_channels", [])),
                    "rx_channels": list(cfg.get("rx_channels", [])),
                    "optimized_switching": bool(cfg.get("optimized_switching", False)),
                }
                for cfg in normalized["tx_rx_configs"]
            ]

        return normalized

    def _sync_preset_selection_with_current_config(self) -> None:
        current_config = self._normalized_config_dict(self._get_config_dict())

        matched_preset_name = None
        if self._presets_dir.exists():
            for preset_file in sorted(self._presets_dir.glob("*.json")):
                try:
                    with open(preset_file, "r") as file:
                        preset_config = json.load(file)
                except Exception:
                    continue

                if self._normalized_config_dict(preset_config) == current_config:
                    matched_preset_name = preset_file.stem
                    break

        self.presetComboBox.blockSignals(True)
        if (
            matched_preset_name is not None
            and self.presetComboBox.findText(matched_preset_name) >= 0
        ):
            self.presetComboBox.setCurrentText(matched_preset_name)
        else:
            self.presetComboBox.setCurrentText("Custom")
        self.presetComboBox.blockSignals(False)

    def _setup_validators(self) -> None:
        self.dcdcTurnonLineEdit.setValidator(QIntValidator(0, 1000000))
        self.measPeriodLineEdit.setValidator(QIntValidator(0, 1000000))
        self.pulseFreqLineEdit.setValidator(QIntValidator(0, 10000000))
        self.numPulsesLineEdit.setValidator(QIntValidator(0, 100))
        self.numSamplesLineEdit.setValidator(QIntValidator(0, 10000))
        self.startHvmuxrxLineEdit.setValidator(QIntValidator(0, 1000000))
        self.startPpgLineEdit.setValidator(QIntValidator(0, 1000000))
        self.turnonAdcLineEdit.setValidator(QIntValidator(0, 1000000))
        self.startPgainbiasLineEdit.setValidator(QIntValidator(0, 1000000))
        self.startAdcsampleLineEdit.setValidator(QIntValidator(0, 1000000))
        self.restartCaptLineEdit.setValidator(QIntValidator(0, 1000000))
        self.captTimeoutLineEdit.setValidator(QIntValidator(0, 1000000))

    def _populate_combo_boxes(self) -> None:
        self.samplingFreqComboBox.clear()
        for freq in interface_wulpus.USS_CAPTURE_ACQ_RATES:
            self.samplingFreqComboBox.addItem(f"{freq:,.0f} Hz", freq)

        self.rxGainComboBox.clear()
        for gain in interface_wulpus.PGA_GAIN:
            self.rxGainComboBox.addItem(f"{gain:.1f} dB", gain)

    def _connect_signals(self) -> None:
        self.txRxTableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.txRxTableWidget.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.presetComboBox.currentTextChanged.connect(self._on_preset_changed)
        self.saveConfigButton.clicked.connect(self._save_to_json)
        self.addTxRxConfigButton.clicked.connect(self._add_tx_rx_config)
        self.removeTxRxConfigButton.clicked.connect(self._remove_tx_rx_config)
        self.clearTxRxConfigButton.clicked.connect(self._clear_tx_rx_configs)
        self.moveTxRxUpButton.clicked.connect(self._move_tx_rx_config_up)
        self.moveTxRxDownButton.clicked.connect(self._move_tx_rx_config_down)
        self.txRxTableWidget.itemChanged.connect(self._on_tx_rx_item_changed)
        self.txRxTableWidget.doubleClicked.connect(lambda: self._edit_tx_rx_config())

        for widget in [
            self.dcdcTurnonLineEdit,
            self.measPeriodLineEdit,
            self.pulseFreqLineEdit,
            self.numPulsesLineEdit,
            self.numSamplesLineEdit,
            self.startHvmuxrxLineEdit,
            self.startPpgLineEdit,
            self.turnonAdcLineEdit,
            self.startPgainbiasLineEdit,
            self.startAdcsampleLineEdit,
            self.restartCaptLineEdit,
            self.captTimeoutLineEdit,
        ]:
            widget.textChanged.connect(self._mark_as_custom)

        self.samplingFreqComboBox.currentIndexChanged.connect(self._mark_as_custom)
        self.rxGainComboBox.currentIndexChanged.connect(self._mark_as_custom)
        self.imuActiveCheckBox.stateChanged.connect(self._mark_as_custom)

    def _mark_as_custom(self) -> None:
        if self._loading_preset:
            return

        if self.presetComboBox.currentText() != "Custom":
            self.presetComboBox.blockSignals(True)
            self.presetComboBox.setCurrentText("Custom")
            self.presetComboBox.blockSignals(False)

    def _on_preset_changed(self, preset_name: str) -> None:
        if preset_name != "Custom":
            self._load_preset(preset_name)

    def _load_preset(self, preset_name: str) -> None:
        logger.info(f"Loading preset: {preset_name}")
        preset_file = self._presets_dir / f"{preset_name}.json"

        if not preset_file.exists():
            QMessageBox.warning(
                self,
                "Preset Not Found",
                f"Preset file '{preset_name}.json' not found in presets directory.",
            )
            return

        try:
            self._loading_preset = True
            with open(preset_file, "r") as file:
                config_data = json.load(file)
            self._apply_config_dict(config_data)
            self.statusLabel.setText(f"Status: Loaded preset '{preset_name}'")
            logger.info(f"Loaded preset from {preset_file}")
        except Exception as err:
            QMessageBox.critical(self, "Load Error", f"Failed to load preset: {str(err)}")
            logger.error(f"Failed to load preset from {preset_file}: {err}")
        finally:
            self._loading_preset = False

    def load_config(self, config: interface_wulpus.WulpusUssConfig) -> None:
        self._loading_preset = True

        try:
            self.dcdcTurnonLineEdit.setText(str(config.dcdc_turnon))
            self.measPeriodLineEdit.setText(str(config.meas_period))
            self.imuActiveCheckBox.setChecked(
                _is_accelerometer_enabled_from_meas_mode(config.meas_mode)
            )
            self.pulseFreqLineEdit.setText(str(config.pulse_freq))
            self.numPulsesLineEdit.setText(str(config.num_pulses))
            self.numSamplesLineEdit.setText(str(config.num_samples))

            idx = self.samplingFreqComboBox.findData(config.sampling_freq)
            if idx >= 0:
                self.samplingFreqComboBox.setCurrentIndex(idx)

            idx = self.rxGainComboBox.findData(config.rx_gain)
            if idx >= 0:
                self.rxGainComboBox.setCurrentIndex(idx)

            self.startHvmuxrxLineEdit.setText(str(config.start_hvmuxrx))
            self.startPpgLineEdit.setText(str(config.start_ppg))
            self.turnonAdcLineEdit.setText(str(config.turnon_adc))
            self.startPgainbiasLineEdit.setText(str(config.start_pgainbias))
            self.startAdcsampleLineEdit.setText(str(config.start_adcsampl))
            self.restartCaptLineEdit.setText(str(config.restart_capt))
            self.captTimeoutLineEdit.setText(str(config.capt_timeout))

            self._tx_rx_configs.clear()
            for i in range(config.num_txrx_configs):
                tx_bits = int(config.tx_configs[i])
                rx_bits = int(config.rx_configs[i])

                tx_channels = [
                    ch for ch in range(8) if (tx_bits >> interface_wulpus.TX_MAP[ch]) & 1
                ]
                rx_channels = [
                    ch for ch in range(8) if (rx_bits >> interface_wulpus.RX_MAP[ch]) & 1
                ]

                optimized = any((tx_bits >> interface_wulpus.RX_MAP[ch]) & 1 for ch in rx_channels)

                self._tx_rx_configs.append(
                    {
                        "tx_channels": tx_channels if tx_channels else [0],
                        "rx_channels": rx_channels if rx_channels else [0],
                        "optimized_switching": optimized,
                    }
                )

            self._update_tx_rx_table()
            self._sync_preset_selection_with_current_config()
            self.statusLabel.setText("Status: Loaded current configuration")
            logger.info("Loaded existing config into widget")
        finally:
            self._loading_preset = False

    def _add_tx_rx_config(self) -> None:
        dialog = TxRxConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            self._tx_rx_configs.append(config)
            self._update_tx_rx_table()
            self._mark_as_custom()
            logger.info(f"Added TX/RX config: {config}")

    def _remove_tx_rx_config(self) -> None:
        self._sync_tx_rx_configs_from_table()
        selected_rows = self.txRxTableWidget.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a configuration to remove.")
            return

        for index in sorted(selected_rows, reverse=True):
            del self._tx_rx_configs[index.row()]

        self._update_tx_rx_table()
        self._mark_as_custom()
        logger.info(f"Removed {len(selected_rows)} TX/RX config(s)")

    def _edit_tx_rx_config(self) -> None:
        self._sync_tx_rx_configs_from_table()
        selected_rows = self.txRxTableWidget.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a configuration to edit.")
            return

        row = selected_rows[0].row()
        if row >= len(self._tx_rx_configs):
            return

        dialog = TxRxConfigDialog(self)
        dialog.set_config(self._tx_rx_configs[row])

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._tx_rx_configs[row] = dialog.get_config()
            self._update_tx_rx_table()
            self._mark_as_custom()
            logger.info(f"Edited TX/RX config at row {row}: {self._tx_rx_configs[row]}")

    def _clear_tx_rx_configs(self) -> None:
        self._tx_rx_configs.clear()
        self._update_tx_rx_table()
        logger.info("Cleared all TX/RX configs")

    def _move_tx_rx_config_up(self) -> None:
        self._sync_tx_rx_configs_from_table()
        selected_rows = self.txRxTableWidget.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a configuration to move.")
            return

        row = selected_rows[0].row()
        if row <= 0 or row >= len(self._tx_rx_configs):
            return

        self._tx_rx_configs[row - 1], self._tx_rx_configs[row] = (
            self._tx_rx_configs[row],
            self._tx_rx_configs[row - 1],
        )
        self._update_tx_rx_table()
        self.txRxTableWidget.selectRow(row - 1)
        self._mark_as_custom()

    def _move_tx_rx_config_down(self) -> None:
        self._sync_tx_rx_configs_from_table()
        selected_rows = self.txRxTableWidget.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a configuration to move.")
            return

        row = selected_rows[0].row()
        if row < 0 or row >= len(self._tx_rx_configs) - 1:
            return

        self._tx_rx_configs[row], self._tx_rx_configs[row + 1] = (
            self._tx_rx_configs[row + 1],
            self._tx_rx_configs[row],
        )
        self._update_tx_rx_table()
        self.txRxTableWidget.selectRow(row + 1)
        self._mark_as_custom()

    def _update_tx_rx_table(self) -> None:
        self._updating_tx_rx_table = True
        self.txRxTableWidget.blockSignals(True)
        self.txRxTableWidget.clearContents()
        self.txRxTableWidget.setRowCount(len(self._tx_rx_configs))

        for row, config in enumerate(self._tx_rx_configs):
            tx_item = QTableWidgetItem(", ".join(str(ch) for ch in config["tx_channels"]))
            tx_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.txRxTableWidget.setItem(row, 0, tx_item)

            rx_item = QTableWidgetItem(", ".join(str(ch) for ch in config["rx_channels"]))
            rx_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.txRxTableWidget.setItem(row, 1, rx_item)

            optimized_item = QTableWidgetItem()
            optimized_item.setFlags(
                Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            optimized_item.setCheckState(
                Qt.CheckState.Checked if config["optimized_switching"] else Qt.CheckState.Unchecked
            )
            self.txRxTableWidget.setItem(row, 2, optimized_item)

        self.txRxTableWidget.blockSignals(False)
        self._updating_tx_rx_table = False

    def _sync_tx_rx_configs_from_table(self) -> None:
        synced_configs: list[dict[str, Any]] = []

        for row in range(self.txRxTableWidget.rowCount()):
            tx_item = self.txRxTableWidget.item(row, 0)
            rx_item = self.txRxTableWidget.item(row, 1)
            if tx_item is None or rx_item is None:
                continue

            try:
                tx_channels = [int(ch.strip()) for ch in tx_item.text().split(",") if ch.strip()]
                rx_channels = [int(ch.strip()) for ch in rx_item.text().split(",") if ch.strip()]
            except ValueError:
                continue

            if not tx_channels or not rx_channels:
                continue

            optimized_item = self.txRxTableWidget.item(row, 2)
            optimized_switching = (
                optimized_item is not None and optimized_item.checkState() == Qt.CheckState.Checked
            )

            synced_configs.append(
                {
                    "tx_channels": tx_channels,
                    "rx_channels": rx_channels,
                    "optimized_switching": optimized_switching,
                }
            )

        self._tx_rx_configs = synced_configs

    def _on_tx_rx_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating_tx_rx_table or item.column() != 2:
            return

        self._sync_tx_rx_configs_from_table()
        self._mark_as_custom()

    def _save_to_json(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Preset", str(self._presets_dir), "JSON Files (*.json)"
        )
        if not file_path:
            return

        if not file_path.endswith(".json"):
            file_path += ".json"

        try:
            config_dict = self._get_config_dict()
            with open(file_path, "w") as file:
                json.dump(config_dict, file, indent=2)

            self.statusLabel.setText(f"Status: Saved to {Path(file_path).name}")
            logger.info(f"Saved configuration to {file_path}")

            if Path(file_path).parent == self._presets_dir:
                current_text = self.presetComboBox.currentText()
                self._populate_presets()
                preset_name = Path(file_path).stem
                idx = self.presetComboBox.findText(preset_name)
                if idx >= 0:
                    self.presetComboBox.setCurrentIndex(idx)
                else:
                    idx = self.presetComboBox.findText(current_text)
                    if idx >= 0:
                        self.presetComboBox.setCurrentIndex(idx)
        except Exception as err:
            QMessageBox.critical(self, "Save Error", f"Failed to save configuration: {str(err)}")
            logger.error(f"Failed to save config to {file_path}: {err}")

    def get_current_config(self) -> interface_wulpus.WulpusUssConfig:
        self._sync_tx_rx_configs_from_table()
        rx_tx_config = interface_wulpus.WulpusRxTxConfigGen()
        for config in self._tx_rx_configs:
            rx_tx_config.add_config(
                tx_channels=config["tx_channels"],
                rx_channels=config["rx_channels"],
                optimized_switching=config["optimized_switching"],
            )

        return interface_wulpus.WulpusUssConfig(
            dcdc_turnon=int(self.dcdcTurnonLineEdit.text()),
            meas_period=int(self.measPeriodLineEdit.text()),
            meas_mode=_meas_mode_from_accelerometer_enabled(self.imuActiveCheckBox.isChecked()),
            pulse_freq=int(self.pulseFreqLineEdit.text()),
            num_pulses=int(self.numPulsesLineEdit.text()),
            sampling_freq=self.samplingFreqComboBox.currentData(),
            num_samples=int(self.numSamplesLineEdit.text()),
            rx_gain=self.rxGainComboBox.currentData(),
            num_txrx_configs=rx_tx_config.tx_rx_len,
            tx_configs=rx_tx_config.get_tx_configs(),
            rx_configs=rx_tx_config.get_rx_configs(),
            start_hvmuxrx=int(self.startHvmuxrxLineEdit.text()),
            start_ppg=int(self.startPpgLineEdit.text()),
            turnon_adc=int(self.turnonAdcLineEdit.text()),
            start_pgainbias=int(self.startPgainbiasLineEdit.text()),
            start_adcsampl=int(self.startAdcsampleLineEdit.text()),
            restart_capt=int(self.restartCaptLineEdit.text()),
            capt_timeout=int(self.captTimeoutLineEdit.text()),
        )

    def _get_config_dict(self) -> dict:
        self._sync_tx_rx_configs_from_table()
        accelerometer_enabled = self.imuActiveCheckBox.isChecked()
        return {
            "dcdc_turnon": int(self.dcdcTurnonLineEdit.text()),
            "meas_period": int(self.measPeriodLineEdit.text()),
            "imu_active": accelerometer_enabled,
            "pulse_freq": int(self.pulseFreqLineEdit.text()),
            "num_pulses": int(self.numPulsesLineEdit.text()),
            "sampling_freq": self.samplingFreqComboBox.currentData(),
            "num_samples": int(self.numSamplesLineEdit.text()),
            "rx_gain": self.rxGainComboBox.currentData(),
            "start_hvmuxrx": int(self.startHvmuxrxLineEdit.text()),
            "start_ppg": int(self.startPpgLineEdit.text()),
            "turnon_adc": int(self.turnonAdcLineEdit.text()),
            "start_pgainbias": int(self.startPgainbiasLineEdit.text()),
            "start_adcsampl": int(self.startAdcsampleLineEdit.text()),
            "restart_capt": int(self.restartCaptLineEdit.text()),
            "capt_timeout": int(self.captTimeoutLineEdit.text()),
            "tx_rx_configs": self._tx_rx_configs,
        }

    def _apply_config_dict(self, config_dict: dict) -> None:
        self.dcdcTurnonLineEdit.setText(str(config_dict["dcdc_turnon"]))
        self.measPeriodLineEdit.setText(str(config_dict["meas_period"]))
        self.imuActiveCheckBox.setChecked(_get_imu_active_from_config_dict(config_dict))
        self.pulseFreqLineEdit.setText(str(config_dict["pulse_freq"]))
        self.numPulsesLineEdit.setText(str(config_dict["num_pulses"]))
        self.numSamplesLineEdit.setText(str(config_dict["num_samples"]))

        idx = self.samplingFreqComboBox.findData(config_dict["sampling_freq"])
        if idx >= 0:
            self.samplingFreqComboBox.setCurrentIndex(idx)

        idx = self.rxGainComboBox.findData(config_dict["rx_gain"])
        if idx >= 0:
            self.rxGainComboBox.setCurrentIndex(idx)

        self.startHvmuxrxLineEdit.setText(str(config_dict["start_hvmuxrx"]))
        self.startPpgLineEdit.setText(str(config_dict["start_ppg"]))
        self.turnonAdcLineEdit.setText(str(config_dict["turnon_adc"]))
        self.startPgainbiasLineEdit.setText(str(config_dict["start_pgainbias"]))
        self.startAdcsampleLineEdit.setText(str(config_dict["start_adcsampl"]))
        self.restartCaptLineEdit.setText(str(config_dict["restart_capt"]))
        self.captTimeoutLineEdit.setText(str(config_dict["capt_timeout"]))

        if "tx_rx_configs" in config_dict:
            self._tx_rx_configs = config_dict["tx_rx_configs"]
            self._update_tx_rx_table()
