"""
Core configuration for BioBridge middleware.

Centralizes all constants, ports, and paths to avoid duplication.
"""

from pathlib import Path

# =============================================================================
# Network Configuration
# =============================================================================

# BioGUI TCP connection (receives ultrasound/IMU data)
BIOGUI_HOST = "127.0.0.1"
BIOGUI_PORT = 12345

# Unity UDP connection (sends hand control commands)
UNITY_HOST = "127.0.0.1"
UNITY_PORT = 5055

# Unity trigger UDP connection (receives gesture labels for training)
UNITY_TRIGGER_HOST = "127.0.0.1"
UNITY_TRIGGER_PORT = 5056

# =============================================================================
# Hardware Configuration
# =============================================================================

# Ultrasound
NUM_US_SAMPLES = 397  # Samples per frame
NUM_US_CHANNELS = 6  # Number of TX/RX configurations

# IMU
NUM_IMU_CHANNELS = 3  # ax, ay, az
MEAS_RATE_HZ = 30  # Measurement rate in Hz
MEAS_PERIOD_US = int(1e6 / MEAS_RATE_HZ)  # Period in microseconds (33333 µs)
MEAS_PERIOD = MEAS_PERIOD_US / 1e6  # Period in seconds (for integration)

# Acquisition Number
NUM_ACQUISITION_NUMBER_CHANNELS = 1

# TX/RX Config ID
NUM_TX_RX_ID_CHANNELS = 1

# =============================================================================
# Model Configuration
# =============================================================================

# Paths
MODEL_DIR = Path(__file__).parent.parent / "nn" / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "2-gesture-model.pt"

# Architecture
US_WINDOW_SIZE = NUM_US_SAMPLES  # 397 samples per channel

# Gesture label mapping
# Model outputs: 0=Fist (closed hand), 1=Open (open hand), 2=MoveForward, 3=MoveRight
GESTURE_MAP = {0: "Fist", 1: "Open", 2: "MoveForward", 3: "MoveRight"}
NUM_CLASSES = len(GESTURE_MAP)


# Reverse mapping for live training with Unity
GESTURE_TO_LABEL = {
    "rest": 0,  # Not collected, but needed for protocol
    "fist": 1,  # Closed hand
    "open": 2,  # Open hand
}

# =============================================================================
# Control Parameters
# =============================================================================

# Send rate to Unity
SEND_RATE = 20.0  # Hz

# Movement speeds
MOVE_STEP_XZ = 0.2
MOVE_STEP_Y = 0.1
ROT_STEP = 5.0  # Degrees per key press

# Default hand rotation
DEFAULT_HAND_ROTATION = [0.0, 0.0, 0.0]  # flexion/extension, unused, supination

# Rotation limits (degrees)
FLEXION_MAX = -89.0
EXTENSION_MAX = 89.0
PRONATION_MAX = -35.0  # Maximum pronation (matches Unity HandRotationLimits.cs)
SUPINATION_MAX = 149.0

# Rotation state angles (for ultrasound-based rotation)
# Matches Unity HandRotationLimits.cs
ROTATION_STATE_NEUTRAL = 0.0
ROTATION_STATE_SUPINATED = 90.0
ROTATION_STATE_PRONATED = PRONATION_MAX  # -35°


# =============================================================================
# Training Parameters
# =============================================================================

# Transition handling
SKIP_PACKETS_AFTER_CHANGE = 12  # Skip ~3 model samples after gesture change

# Data collection targets
TARGET_SAMPLES_PER_CLASS = 200

# Training hyperparameters
DEFAULT_EPOCHS = 50
DEFAULT_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 0.001

# Prediction smoothing
PREDICTION_SMOOTHING = 30  # Number of predictions to average

# =============================================================================
# IMU Tracking Parameters
# =============================================================================

CALIBRATION_SAMPLES = 60  # 3 seconds at 40 Hz

# Default position tracker settings
DEFAULT_START_THRESHOLD = 0.40  # m/s² to start moving
DEFAULT_STOP_THRESHOLD = 0.25  # m/s² to stop moving
DEFAULT_POSITION_SCALE = 20.0  # Adjusted for 30 Hz measurement rate
DEFAULT_VELOCITY_DECAY = 0.92

# =============================================================================
# Control Modes
# =============================================================================


class Mode:
    """Hand control modes for Unity."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
