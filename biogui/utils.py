# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

"""
Utility functions.
"""

from dataclasses import dataclass
from typing import Any, Callable, TypeAlias

import numpy as np
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QWidget

DecodeFn: TypeAlias = Callable[[bytes], dict[str, np.ndarray]]
"""Type representing the decode function that translates the binary data received from the device into signals."""

ConfigureInterfaceModuleFn: TypeAlias = Callable[
    [QWidget, "InterfaceModule"], "InterfaceModule | None"
]


@dataclass(frozen=True)
class PlatformConfig:
    """Optional curated-platform metadata attached to an interface module."""

    id: str
    configureInterfaceModule: ConfigureInterfaceModuleFn
    configWidgetClass: type[QWidget] | None = None
    hasInlineConfigAction: bool = True
    inlineActionIconName: str = "preferences-system"
    inlineActionToolTip: str = "Configure platform"


@dataclass(frozen=True)
class InterfaceModule:
    """Interface module used to communicate with the data source."""

    packetSize: int
    startSeq: list[bytes | float]
    stopSeq: list[bytes | float]
    sigInfo: dict[str, dict[str, Any]]
    decodeFn: DecodeFn
    platformConfig: PlatformConfig | None = None


@dataclass
class SigData:
    """
    Dataclass describing a signal.

    Attributes
    ----------
    sigName : str
        Signal name.
    data : ndarray
        Data with shape (nSamp, nCh).
    acq_ts : float
        Timestamp denoting the time of acquisition.
    """

    sigName: str
    data: np.ndarray
    acq_ts: float


def detectTheme():
    """Determine whether the system theme is light or dark."""
    # Get palette of QApplication
    palette = QApplication.palette()

    # Compare the color of the background and text to infer theme
    textColor = palette.color(QPalette.Text)  # type: ignore
    backgroundColor = palette.color(QPalette.Window)  # type: ignore

    # Simple heuristic to determine if the theme is light or dark
    isDark = backgroundColor.lightness() < textColor.lightness()
    return "dark" if isDark else "light"
