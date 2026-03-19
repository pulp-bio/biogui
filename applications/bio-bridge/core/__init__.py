# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Core module for BioBridge middleware.

Provides shared configuration, utilities, and signal processing.
"""

from .config import (
    # Network
    BIOGUI_HOST,
    BIOGUI_PORT,
    # IMU
    CALIBRATION_SAMPLES,
    DEFAULT_BATCH_SIZE,
    DEFAULT_EPOCHS,
    DEFAULT_HAND_ROTATION,
    DEFAULT_LEARNING_RATE,
    DEFAULT_MODEL_PATH,
    DEFAULT_POSITION_SCALE,
    DEFAULT_START_THRESHOLD,
    DEFAULT_STOP_THRESHOLD,
    DEFAULT_VELOCITY_DECAY,
    EXTENSION_MAX,
    # Limits
    FLEXION_MAX,
    GESTURE_MAP,
    GESTURE_TO_LABEL,
    MEAS_PERIOD,
    MEAS_PERIOD_US,
    MEAS_RATE_HZ,
    # Model
    MODEL_DIR,
    MOVE_STEP_XZ,
    MOVE_STEP_Y,
    NUM_CLASSES,
    NUM_IMU_CHANNELS,
    NUM_US_CHANNELS,
    # Hardware
    NUM_US_SAMPLES,
    PREDICTION_SMOOTHING,
    PRONATION_MAX,
    ROT_STEP,
    # Control
    SEND_RATE,
    # Training
    SKIP_PACKETS_AFTER_CHANGE,
    SUPINATION_MAX,
    TARGET_SAMPLES_PER_CLASS,
    UNITY_HOST,
    UNITY_PORT,
    UNITY_TRIGGER_HOST,
    UNITY_TRIGGER_PORT,
    US_WINDOW_SIZE,
    # Rotation States
    ROTATION_STATE_NEUTRAL,
    ROTATION_STATE_SUPINATED,
    ROTATION_STATE_PRONATED,
    # Classes
    Mode,
)
from .signal import (
    DTYPE_ACQUISITION_NUMBER,
    DTYPE_IMU,
    DTYPE_TX_RX_ID,
    DTYPE_US,
    PACKET_SIZE,
    US_BYTES,
    WULPUS_PACKET_FORMAT,
    PacketFormat,
    SignalInfo,
    decode_packet,
)
from .utils import (
    clamp,
    clamp01,
    clamp_flexion,
    clamp_supination,
    recv_exact,
    softmax,
)

__all__ = [
    # Config - Network
    "BIOGUI_HOST",
    "BIOGUI_PORT",
    "UNITY_HOST",
    "UNITY_PORT",
    "UNITY_TRIGGER_HOST",
    "UNITY_TRIGGER_PORT",
    # Config - Hardware
    "NUM_US_SAMPLES",
    "NUM_US_CHANNELS",
    "NUM_IMU_CHANNELS",
    "MEAS_PERIOD",
    "MEAS_PERIOD_US",
    "MEAS_RATE_HZ",
    # Config - Model
    "MODEL_DIR",
    "DEFAULT_MODEL_PATH",
    "NUM_CLASSES",
    "US_WINDOW_SIZE",
    "GESTURE_MAP",
    "GESTURE_TO_LABEL",
    # Config - Control
    "SEND_RATE",
    "MOVE_STEP_XZ",
    "MOVE_STEP_Y",
    "ROT_STEP",
    "DEFAULT_HAND_ROTATION",
    "PREDICTION_SMOOTHING",
    # Config - Limits
    "FLEXION_MAX",
    "EXTENSION_MAX",
    "PRONATION_MAX",
    "SUPINATION_MAX",
    # Config - Rotation States
    "ROTATION_STATE_NEUTRAL",
    "ROTATION_STATE_SUPINATED",
    "ROTATION_STATE_PRONATED",
    # Config - Training
    "SKIP_PACKETS_AFTER_CHANGE",
    "TARGET_SAMPLES_PER_CLASS",
    "DEFAULT_EPOCHS",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_LEARNING_RATE",
    # Config - IMU
    "CALIBRATION_SAMPLES",
    "DEFAULT_START_THRESHOLD",
    "DEFAULT_STOP_THRESHOLD",
    "DEFAULT_POSITION_SCALE",
    "DEFAULT_VELOCITY_DECAY",
    # Config - Classes
    "Mode",
    # Utils
    "clamp",
    "clamp01",
    "clamp_flexion",
    "clamp_supination",
    "recv_exact",
    "softmax",
    # Signal
    "SignalInfo",
    "PacketFormat",
    "WULPUS_PACKET_FORMAT",
    "PACKET_SIZE",
    "US_BYTES",
    "decode_packet",
    "DTYPE_US",
    "DTYPE_IMU",
    "DTYPE_ACQUISITION_NUMBER",
    "DTYPE_TX_RX_ID",
]
