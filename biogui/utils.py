# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Utility functions.

"""

from collections import namedtuple
from dataclasses import dataclass
from typing import Callable, TypeAlias

import numpy as np
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

DecodeFn: TypeAlias = Callable[[bytes], dict[str, np.ndarray]]
"""Type representing the decode function that translates the binary data received from the device into signals."""

InterfaceModule = namedtuple("InterfaceModule", "packetSize, startSeq, stopSeq, sigInfo, decodeFn")
"""Type representing the interface module to communicate with the data source."""


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
