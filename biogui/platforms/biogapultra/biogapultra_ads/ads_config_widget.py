# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Settings dialog for the ADS1298 analog front-end (EEG/EMG shields).

Built in code rather than from a .ui file, mirroring
biogapultra_mmwave/radar_config_widget.py.
"""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QWidget

from biogui.platforms.biogapultra.biogapultra_ads import ads_config


class AdsConfigWidget(QWidget):
    """
    Editor for :class:`ads_config.AdsConfig`.

    Parameters
    ----------
    parent : QWidget or None
        Parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        form = QFormLayout(self)

        self.sampleRateComboBox = QComboBox(self)
        for byte, label in ads_config.SAMPLE_RATE_OPTIONS.items():
            self.sampleRateComboBox.addItem(label, byte)
        self.sampleRateComboBox.setToolTip(ads_config.HELP["sample_rate"])
        sampleRateLabel = QLabel("Sample rate:", self)
        sampleRateLabel.setToolTip(ads_config.HELP["sample_rate"])
        form.addRow(sampleRateLabel, self.sampleRateComboBox)

        self.adsModeComboBox = QComboBox(self)
        for byte, label in ads_config.ADS_MODE_OPTIONS.items():
            self.adsModeComboBox.addItem(label, byte)
        self.adsModeComboBox.setToolTip(ads_config.HELP["ads_mode"])
        adsModeLabel = QLabel("Mode:", self)
        adsModeLabel.setToolTip(ads_config.HELP["ads_mode"])
        form.addRow(adsModeLabel, self.adsModeComboBox)

        self.gainComboBox = QComboBox(self)
        for byte, label in ads_config.GAIN_OPTIONS.items():
            self.gainComboBox.addItem(label, byte)
        self.gainComboBox.setToolTip(ads_config.HELP["gain"])
        gainLabel = QLabel("Gain:", self)
        gainLabel.setToolTip(ads_config.HELP["gain"])
        form.addRow(gainLabel, self.gainComboBox)

        self.adsModeComboBox.currentIndexChanged.connect(self._onModeChanged)

        self.loadSettings(ads_config.DEFAULT_CONFIG)

    def _onModeChanged(self) -> None:
        """Force/lock gain to the firmware-required value while the test
        signal mode is selected."""
        isTestSignal = self.adsModeComboBox.currentData() == ads_config.TEST_SIGNAL_MODE
        if isTestSignal:
            self.gainComboBox.setCurrentIndex(
                self.gainComboBox.findData(ads_config.TEST_SIGNAL_FORCED_GAIN)
            )
        self.gainComboBox.setEnabled(not isTestSignal)

    def loadSettings(self, settings: ads_config.AdsConfig) -> None:
        """Prefill the fields from ``settings``."""
        s = settings.validated()
        self.sampleRateComboBox.setCurrentIndex(
            self.sampleRateComboBox.findData(s.sample_rate)
        )
        self.adsModeComboBox.setCurrentIndex(
            self.adsModeComboBox.findData(s.ads_mode)
        )
        self.gainComboBox.setCurrentIndex(self.gainComboBox.findData(s.gain))
        self._onModeChanged()

    def currentSettings(self) -> ads_config.AdsConfig:
        """Read the fields back into a settings object."""
        return ads_config.AdsConfig(
            sample_rate=self.sampleRateComboBox.currentData(),
            ads_mode=self.adsModeComboBox.currentData(),
            gain=self.gainComboBox.currentData(),
        ).validated()
