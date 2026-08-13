# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Generic modal-dialog shell shared by every BioGAP-Ultra shield settings
dialog: stack N pre-built, pre-loaded widgets vertically under one Ok/Cancel
button box. Used standalone (one widget) by radar_config_widget.py and the
ADS-only interfaces, and with two widgets by the combined EEG/EMG + mmWave
and EEG/EMG + WULPUS PRO interfaces.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)


def openDialogShell(
    parent: QWidget,
    widgets: list[QWidget],
    title: str,
    onAccept: Callable[[], None] | None = None,
) -> bool:
    """
    Show one modal dialog stacking ``widgets`` vertically under an Ok/Cancel
    box. No forced resize: the dialog is sized from the stacked widgets' own
    size hints, same as radar's dialog today.

    Parameters
    ----------
    parent : QWidget
        Dialog parent.
    widgets : list of QWidget
        Pre-built, pre-loaded settings widgets to stack, in order.
    title : str
        Window title.
    onAccept : callable or None
        If given, called when Ok is clicked, before the dialog closes. If it
        raises, a message box reports the error and the dialog stays open
        (mirrors WulpusConfigWidget's existing validate-before-close
        behaviour); if it returns normally the dialog accepts and closes. If
        None, clicking Ok accepts unconditionally.

    Returns
    -------
    bool
        True if the dialog was accepted, False if cancelled.
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setModal(True)

    layout = QVBoxLayout(dialog)
    for widget in widgets:
        layout.addWidget(widget)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        dialog,
    )

    def _tryAccept() -> None:
        if onAccept is not None:
            try:
                onAccept()
            except Exception as err:
                QMessageBox.critical(dialog, "Configuration Error", str(err))
                return
        dialog.accept()

    buttons.accepted.connect(_tryAccept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    return dialog.exec() == QDialog.DialogCode.Accepted
