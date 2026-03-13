"""
Gesture recognition module for BioBridge middleware.

Provides classes for predicting gestures from ultrasound data.
"""

from .buffer import USDataBuffer, IMUDataBuffer
from .predictor import GesturePredictor

__all__ = [
    "GesturePredictor",
    "USDataBuffer",
    "IMUDataBuffer"
]
