# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Unity communication module for BioBridge middleware.

Provides classes for controlling hand visualization in Unity.
"""

from .controller import UnityController

__all__ = [
    "UnityController",
]
