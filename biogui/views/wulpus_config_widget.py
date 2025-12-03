"""WULPUS hardware configuration widget with preset management."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QTableWidgetItem,
    QWidget,
)

from biogui.ui.wulpus_config_widget_ui import Ui_WulpusConfigWidget
from interfaces.interface_wulpus import (
    PGA_GAIN,
    RX_MAP,
    TX_MAP,
    USS_CAPTURE_ACQ_RATES,
    WulpusRxTxConfigGen,
    WulpusUssConfig,
)

logger = logging.getLogger(__name__)


class WulpusConfigWidget(QWidget, Ui_WulpusConfigWidget):
    """Configuration widget for WULPUS ultrasound hardware parameters."""

    configChanged = Signal(WulpusUssConfig)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self._current_config: WulpusUssConfig | None = None
        self._tx_rx_configs: list[dict[str, Any]] = []
        self._presets_dir = self._get_presets_directory()
        self._loading_preset = False  # Flag to prevent marking as custom while loading

        self._setup_validators()
        self._populate_combo_boxes()
        self._populate_presets()
        self._connect_signals()

        logger.info("WulpusConfigWidget initialized")

    def _get_presets_directory(self) -> Path:
        """Get the presets directory path, creating it if necessary."""
        # Get the biogui root directory (two levels up from this file)
        biogui_root = Path(__file__).parent.parent.parent
        presets_dir = biogui_root / "presets" / "wulpus"

        # Create directory if it doesn't exist
        presets_dir.mkdir(parents=True, exist_ok=True)

        return presets_dir

    def _populate_presets(self) -> None:
        """Populate the preset combo box from JSON files in the presets directory."""
        self.presetComboBox.clear()

        # Add "Custom" as the first item
        self.presetComboBox.addItem("Custom")

        # Scan for JSON files in the presets directory
        if self._presets_dir.exists():
            preset_files = sorted(self._presets_dir.glob("*.json"))
            for preset_file in preset_files:
                # Use filename without extension as preset name
                preset_name = preset_file.stem
                self.presetComboBox.addItem(preset_name)

        # Set default to first preset if available, otherwise Custom
        if self.presetComboBox.count() > 1:
            self.presetComboBox.setCurrentIndex(1)  # First preset after "Custom"
            self._load_preset(self.presetComboBox.currentText())
        else:
            self.presetComboBox.setCurrentIndex(0)  # "Custom"

    def _setup_validators(self) -> None:
        self.dcdcTurnonLineEdit.setValidator(QIntValidator(0, 1000000))
        self.measPeriodLineEdit.setValidator(QIntValidator(0, 1000000))  # No minimum
        self.transFreqLineEdit.setValidator(QIntValidator(0, 10000000))
        self.pulseFreqLineEdit.setValidator(QIntValidator(0, 10000000))
        self.numPulsesLineEdit.setValidator(QIntValidator(0, 100))
        self.numSamplesLineEdit.setValidator(QIntValidator(0, 10000))

        # Advanced settings validators
        self.startHvmuxrxLineEdit.setValidator(QIntValidator(0, 1000000))
        self.startPpgLineEdit.setValidator(QIntValidator(0, 1000000))
        self.turnonAdcLineEdit.setValidator(QIntValidator(0, 1000000))
        self.startPgainbiasLineEdit.setValidator(QIntValidator(0, 1000000))
        self.startAdcsampleLineEdit.setValidator(QIntValidator(0, 1000000))
        self.restartCaptLineEdit.setValidator(QIntValidator(0, 1000000))
        self.captTimeoutLineEdit.setValidator(QIntValidator(0, 1000000))

    def _populate_combo_boxes(self) -> None:
        self.samplingFreqComboBox.clear()
        for freq in USS_CAPTURE_ACQ_RATES:
            self.samplingFreqComboBox.addItem(f"{freq:,.0f} Hz", freq)
        self.rxGainComboBox.clear()
        for gain in PGA_GAIN:
            self.rxGainComboBox.addItem(f"{gain:.1f} dB", gain)

    def _connect_signals(self) -> None:
        self.presetComboBox.currentTextChanged.connect(self._on_preset_changed)
        self.saveConfigButton.clicked.connect(self._save_to_json)
        self.addTxRxConfigButton.clicked.connect(self._add_tx_rx_config)
        self.removeTxRxConfigButton.clicked.connect(self._remove_tx_rx_config)
        self.clearTxRxConfigButton.clicked.connect(self._clear_tx_rx_configs)

        # Enable double-click to edit TX/RX configs
        self.txRxTableWidget.doubleClicked.connect(lambda: self._edit_tx_rx_config())
        for widget in [
            self.dcdcTurnonLineEdit,
            self.measPeriodLineEdit,
            self.transFreqLineEdit,
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

    def _mark_as_custom(self) -> None:
        # Don't mark as custom if we're currently loading a preset
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
        """Load a preset from a JSON file in the presets directory."""
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
            # Set flag to prevent marking as custom during load
            self._loading_preset = True

            with open(preset_file, "r") as f:
                config_data = json.load(f)
            self._apply_config_dict(config_data)
            self.statusLabel.setText(f"Status: Loaded preset '{preset_name}'")
            logger.info(f"Loaded preset from {preset_file}")

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load preset: {str(e)}")
            logger.error(f"Failed to load preset from {preset_file}: {e}")
        finally:
            # Reset flag after loading
            self._loading_preset = False

    def load_config(self, config: WulpusUssConfig) -> None:
        """Load an existing configuration into the widget."""
        # Set flag to prevent marking as custom during load
        self._loading_preset = True

        try:
            self.dcdcTurnonLineEdit.setText(str(config.dcdc_turnon))
            self.measPeriodLineEdit.setText(str(config.meas_period))
            self.transFreqLineEdit.setText(str(config.trans_freq))
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

                tx_channels = [ch for ch in range(8) if (tx_bits >> TX_MAP[ch]) & 1]
                rx_channels = [ch for ch in range(8) if (rx_bits >> RX_MAP[ch]) & 1]

                # Try to detect optimized switching by checking if RX bits appear in TX config
                # This happens when optimized switching pre-activates RX channels during TX
                optimized = False
                for ch in rx_channels:
                    if (tx_bits >> RX_MAP[ch]) & 1:
                        optimized = True
                        break

                self._tx_rx_configs.append(
                    {
                        "tx_channels": tx_channels if tx_channels else [0],
                        "rx_channels": rx_channels if rx_channels else [0],
                        "optimized_switching": optimized,
                    }
                )

            self._update_tx_rx_table()
            self.presetComboBox.setCurrentText("Custom")
            self.statusLabel.setText("Status: Loaded current configuration")
            logger.info("Loaded existing config into widget")
        finally:
            # Reset flag after loading
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
        selected_rows = self.txRxTableWidget.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(
                self, "No Selection", "Please select a configuration to remove."
            )
            return
        for index in sorted(selected_rows, reverse=True):
            row = index.row()
            del self._tx_rx_configs[row]

        self._update_tx_rx_table()
        self._mark_as_custom()
        logger.info(f"Removed {len(selected_rows)} TX/RX config(s)")

    def _edit_tx_rx_config(self) -> None:
        """Edit the selected TX/RX configuration."""
        selected_rows = self.txRxTableWidget.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(
                self, "No Selection", "Please select a configuration to edit."
            )
            return

        row = selected_rows[0].row()
        if row >= len(self._tx_rx_configs):
            return

        current_config = self._tx_rx_configs[row]
        dialog = TxRxConfigDialog(self)

        # Pre-fill with current values
        dialog.tx_channels_edit.setText(
            ",".join(str(ch) for ch in current_config["tx_channels"])
        )
        dialog.rx_channels_edit.setText(
            ",".join(str(ch) for ch in current_config["rx_channels"])
        )
        dialog.optimized_checkbox.setChecked(current_config["optimized_switching"])

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._tx_rx_configs[row] = dialog.get_config()
            self._update_tx_rx_table()
            self._mark_as_custom()
            logger.info(f"Edited TX/RX config at row {row}: {self._tx_rx_configs[row]}")

    def _clear_tx_rx_configs(self) -> None:
        self._tx_rx_configs.clear()
        self._update_tx_rx_table()
        logger.info("Cleared all TX/RX configs")

    def _update_tx_rx_table(self) -> None:
        self.txRxTableWidget.setRowCount(len(self._tx_rx_configs))

        for i, config in enumerate(self._tx_rx_configs):
            self.txRxTableWidget.setItem(i, 0, QTableWidgetItem(str(i)))
            tx_str = ", ".join(str(ch) for ch in config["tx_channels"])
            self.txRxTableWidget.setItem(i, 1, QTableWidgetItem(tx_str))
            rx_str = ", ".join(str(ch) for ch in config["rx_channels"])
            self.txRxTableWidget.setItem(i, 2, QTableWidgetItem(rx_str))

            # Add checkbox for optimized switching
            checkbox_widget = QWidget()
            checkbox = QCheckBox()
            checkbox.setChecked(config["optimized_switching"])
            checkbox.stateChanged.connect(
                lambda state, row=i: self._on_optimized_checkbox_changed(row, state)
            )
            layout = QHBoxLayout(checkbox_widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.txRxTableWidget.setIndexWidget(
                self.txRxTableWidget.model().index(i, 3), checkbox_widget
            )

    def _on_optimized_checkbox_changed(self, row: int, state: int) -> None:
        """Update optimized switching setting when checkbox changes."""
        if row < len(self._tx_rx_configs):
            self._tx_rx_configs[row]["optimized_switching"] = bool(state)
            self._mark_as_custom()

    def _save_to_json(self) -> None:
        """Save current configuration as a preset in the presets directory."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Preset", str(self._presets_dir), "JSON Files (*.json)"
        )
        if not file_path:
            return

        # Auto-add .json extension if not present
        if not file_path.endswith(".json"):
            file_path += ".json"

        try:
            config_dict = self._get_config_dict()
            with open(file_path, "w") as f:
                json.dump(config_dict, f, indent=2)

            self.statusLabel.setText(f"Status: Saved to {Path(file_path).name}")
            logger.info(f"Saved configuration to {file_path}")

            # Refresh presets dropdown if saved in presets directory
            if Path(file_path).parent == self._presets_dir:
                current_text = self.presetComboBox.currentText()
                self._populate_presets()
                # Try to select the newly saved preset
                preset_name = Path(file_path).stem
                idx = self.presetComboBox.findText(preset_name)
                if idx >= 0:
                    self.presetComboBox.setCurrentIndex(idx)
                else:
                    # Restore previous selection if possible
                    idx = self.presetComboBox.findText(current_text)
                    if idx >= 0:
                        self.presetComboBox.setCurrentIndex(idx)

        except Exception as e:
            QMessageBox.critical(
                self, "Save Error", f"Failed to save configuration: {str(e)}"
            )
            logger.error(f"Failed to save config to {file_path}: {e}")

    def get_current_config(self) -> WulpusUssConfig:
        """Create and validate WulpusUssConfig from current widget values."""
        rx_tx_config = WulpusRxTxConfigGen()
        for config in self._tx_rx_configs:
            rx_tx_config.add_config(
                tx_channels=config["tx_channels"],
                rx_channels=config["rx_channels"],
                optimized_switching=config["optimized_switching"],
            )
        return WulpusUssConfig(
            dcdc_turnon=int(self.dcdcTurnonLineEdit.text()),
            meas_period=int(self.measPeriodLineEdit.text()),
            trans_freq=int(self.transFreqLineEdit.text()),
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
        return {
            "dcdc_turnon": int(self.dcdcTurnonLineEdit.text()),
            "meas_period": int(self.measPeriodLineEdit.text()),
            "trans_freq": int(self.transFreqLineEdit.text()),
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
        # Note: _loading_preset flag should be set by caller
        self.dcdcTurnonLineEdit.setText(str(config_dict["dcdc_turnon"]))
        self.measPeriodLineEdit.setText(str(config_dict["meas_period"]))
        self.transFreqLineEdit.setText(str(config_dict["trans_freq"]))
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


class TxRxConfigDialog(QDialog):
    """Dialog for configuring TX/RX channels."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TX/RX Configuration")

        layout = QFormLayout(self)
        self.tx_channels_edit = QLineEdit()
        self.tx_channels_edit.setPlaceholderText("e.g., 3 or 1,2,3")
        layout.addRow("TX Channels (0-7):", self.tx_channels_edit)
        self.rx_channels_edit = QLineEdit()
        self.rx_channels_edit.setPlaceholderText("e.g., 3 or 1,2,3")
        layout.addRow("RX Channels (0-7):", self.rx_channels_edit)
        self.optimized_checkbox = QCheckBox()
        layout.addRow("Optimized Switching:", self.optimized_checkbox)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def accept(self):
        try:
            self._parse_channels()
            super().accept()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))

    def _parse_channels(self) -> tuple[list[int], list[int]]:
        def parse_channel_str(s: str) -> list[int]:
            channels = [int(x.strip()) for x in s.split(",") if x.strip()]
            for ch in channels:
                if not 0 <= ch <= 7:
                    raise ValueError(f"Channel {ch} out of range (0-7)")
            return channels

        tx = parse_channel_str(self.tx_channels_edit.text())
        rx = parse_channel_str(self.rx_channels_edit.text())
        if not tx:
            raise ValueError("At least one TX channel required")
        if not rx:
            raise ValueError("At least one RX channel required")
        return tx, rx

    def get_config(self) -> dict:
        tx, rx = self._parse_channels()
        return {
            "tx_channels": tx,
            "rx_channels": rx,
            "optimized_switching": self.optimized_checkbox.isChecked(),
        }
