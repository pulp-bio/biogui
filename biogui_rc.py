# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Compatibility wrapper for generated Qt UI modules.

Some pyside6-uic versions generate ``import biogui_rc`` instead of a
package-relative import. Re-exporting here keeps those files importable.
"""

from biogui.ui.biogui_rc import *  # noqa: F401,F403
