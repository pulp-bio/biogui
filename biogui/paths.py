# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Define paths used by BioGUI.
"""

from pathlib import Path

APP_DIR = Path(__file__).parent.resolve()
# All bundled interface_*.py files live in per-platform subfolders (recursive).
PLATFORMS_DIR = APP_DIR / "platforms"
INTERFACES_DIR = PLATFORMS_DIR
