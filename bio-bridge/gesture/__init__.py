# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Gesture recognition module for BioBridge middleware.

Provides classes for predicting gestures from ultrasound data.
"""

from .buffer import USDataBuffer, IMUDataBuffer
from .predictor import GesturePredictor

__all__ = ["GesturePredictor", "USDataBuffer", "IMUDataBuffer"]
