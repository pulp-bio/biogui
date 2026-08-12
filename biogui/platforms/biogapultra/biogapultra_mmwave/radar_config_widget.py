# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Settings dialog for the mmWave radar shield.

Exposes the four things that are worth changing between recordings without
rebuilding firmware: the three radar registers the firmware accepts commands for
(IF gain, TX power, frame rate) and the host-side choice of which range bin the
pulse waveform comes from.

Built in code rather than from a .ui file so it needs no pyside6-uic step, unlike
biogui/resources/*.ui.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from biogui.platforms.biogapultra.biogapultra_mmwave import radar


class RadarConfigWidget(QWidget):
    """
    Editor for :class:`radar.RadarSettings`.

    Parameters
    ----------
    parent : QWidget or None
        Parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        form = QFormLayout(self)

        # --- host-side processing ------------------------------------------
        self.rangeBinComboBox = QComboBox(self)
        for b, mm in enumerate(radar.rangeAxisMm()):
            label = f"bin {b}  (~{mm:.0f} mm)"
            if b == 0:
                label += "  - DC, not usable"
            self.rangeBinComboBox.addItem(label, b)
        form.addRow("Phase range bin:", self.rangeBinComboBox)

        # --- sent to the firmware at start-up ------------------------------
        self.ifGainComboBox = QComboBox(self)
        for g in radar.VALID_IF_GAINS_DB:
            self.ifGainComboBox.addItem(f"{g} dB", g)
        form.addRow("IF gain:", self.ifGainComboBox)

        self.txPowerSpinBox = QSpinBox(self)
        self.txPowerSpinBox.setRange(*radar.TX_POWER_RANGE)
        form.addRow("TX power:", self.txPowerSpinBox)

        self.frameRateComboBox = QComboBox(self)
        for r in radar.VALID_FRAME_RATES:
            self.frameRateComboBox.addItem(f"{r} fps", r)
        form.addRow("Frame rate:", self.frameRateComboBox)

        hint = QLabel(
            "The range bin is a processing choice and can be changed between\n"
            "recordings; every bin's phase is recorded in <name>_phase_bins\n"
            "regardless, so it can also be revisited afterwards. Watch\n"
            "<name>_level: if it reaches 0 or "
            f"{radar.ADC_MAX_CODE} the IF gain is clipping.",
            self,
        )
        hint.setWordWrap(True)
        form.addRow(hint)

        self.loadSettings(radar.DEFAULT_SETTINGS)

    def loadSettings(self, settings: radar.RadarSettings) -> None:
        """Prefill the fields from ``settings``."""
        s = settings.validated()
        self.rangeBinComboBox.setCurrentIndex(
            self.rangeBinComboBox.findData(s.rangeBin)
        )
        self.ifGainComboBox.setCurrentIndex(self.ifGainComboBox.findData(s.ifGainDb))
        self.txPowerSpinBox.setValue(s.txPower)
        self.frameRateComboBox.setCurrentIndex(
            self.frameRateComboBox.findData(s.frameRate)
        )

    def currentSettings(self) -> radar.RadarSettings:
        """Read the fields back into a settings object."""
        return radar.RadarSettings(
            ifGainDb=self.ifGainComboBox.currentData(),
            txPower=self.txPowerSpinBox.value(),
            frameRate=self.frameRateComboBox.currentData(),
            rangeBin=self.rangeBinComboBox.currentData(),
            rxIndex=radar.DEFAULT_SETTINGS.rxIndex,
        ).validated()


def openConfigDialog(
    parent: QWidget,
    settings: radar.RadarSettings,
    title: str = "mmWave Radar Configuration",
) -> radar.RadarSettings | None:
    """
    Show the radar settings dialog.

    Parameters
    ----------
    parent : QWidget
        Dialog parent.
    settings : RadarSettings
        Values to prefill.
    title : str
        Window title.

    Returns
    -------
    RadarSettings or None
        The edited settings, or None if the dialog was cancelled.
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setModal(True)

    layout = QVBoxLayout(dialog)
    widget = RadarConfigWidget(dialog)
    widget.loadSettings(settings)
    layout.addWidget(widget)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        dialog,
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return widget.currentSettings()


def makeConfigureFn(title: str, buildModule, prefix: str = "mmwave"):
    """
    Build a ``PlatformConfig.configureInterfaceModule`` callable.

    The settings currently in effect are recovered from the module's ``sigInfo``
    extras, so the dialog opens showing what is actually running rather than the
    defaults. On accept, ``buildModule`` is asked for a completely fresh
    InterfaceModule -- new startSeq (the radar commands carry the new gain, power
    and frame rate), new sigInfo (``fs`` follows the frame rate) and a new
    decodeFn closing over a new RadarDecoder, so no phase-unwrap state survives
    a settings change.

    Parameters
    ----------
    title : str
        Dialog window title.
    buildModule : callable
        ``(RadarSettings) -> InterfaceModule``.
    prefix : str
        Radar signal-name prefix, for locating the stored settings.

    Returns
    -------
    callable
        ``(QWidget, InterfaceModule) -> InterfaceModule | None``
    """

    def _configure(parent, interfaceModule):
        current = radar.settingsFromSigInfo(interfaceModule.sigInfo, prefix)
        newSettings = openConfigDialog(parent, current, title)
        if newSettings is None:
            return None
        return buildModule(newSettings)

    return _configure
