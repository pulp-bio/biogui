"""
Application entry points for BioBridge middleware.

Each module in this package is a standalone application that can be run
directly from the command line.

Available applications:
- gesture_control: Live gesture recognition with Unity control
- keyboard_control: Keyboard-only Unity control for testing
- imu_control: IMU-based position tracking with gesture control
- multi_gesture_control: Multi-class gestures → curls + position + IMU rotation
- inference: Command-line gesture inference without Unity
- test_receiver: Debug tool for BioGUI packet inspection
- training: Online training for gesture recognition models
- trigger_monitor: Debug tool for Unity trigger messages
"""

__all__ = [
    "gesture_control",
    "keyboard_control",
    "imu_position_control",
    "multi_gesture_control",
    "inference",
    "test_receiver",
    "training",
    "trigger_monitor",
]
