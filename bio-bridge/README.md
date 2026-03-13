# BioBridge

Middleware connecting BioGUI to MotionLab (Unity). Receives ultrasound and IMU data from BioGUI over TCP, runs real-time gesture recognition, and sends hand control commands to Unity over UDP.

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.11)
- Pre-trained PyTorch model file placed in `nn/models/`

## Setup

From the `bio-bridge/` directory:

```bash
uv sync
mkdir -p nn/models
```

Place your pre-trained .pt model files in `nn/models/`.

## Run

The main entry point for the paper experiment:

```bash
uv run -m apps.multi_model_control --model <modelname> [--flip-imu]
```

During the run, press C in the terminal to calibrate the IMU.

### Other entry points (WIP)

| Module                    | Description                               |
| ------------------------- | ----------------------------------------- |
| apps.gesture_control      | Live gesture recognition to Unity         |
| apps.imu_position_control | IMU-based position tracking to Unity      |
| apps.keyboard_control     | Keyboard-only Unity control (for testing) |
| apps.rotation_control     | Wrist rotation control                    |
| apps.test_receiver        | Debug raw BioGUI packets                  |
| apps.prediction_monitor   | Monitor live predictions                  |

```bash
uv run -m apps.<module_name> [args]
```

## Configuration

All constant are in `core/config.py`:

| Category | Key constants                                                     |
| -------- | ----------------------------------------------------------------- |
| Network  | BIOGUI_PORT (12345), UNITY_PORT (5055), UNITY_TRIGGER_PORT (5056) |
| Hardware | NUM_US_SAMPLES (397), NUM_US_CHANNELS (6), MEAS_RATE_HZ (30)      |
| Model    | MODEL_DIR, DEFAULT_MODEL_PATH, GESTURE_MAP                        |
| Control  | SEND_RATE (20 Hz), MOVE_STEP_XZ, ROT_STEP                         |
| IMU      | CALIBRATION_SAMPLES (60), DEFAULT_VELOCITY_DECAY (0.92)           |

## Project Structure

```
bio-bridge/
├── apps/        Application entry points
├── core/        Shared configuration and utilities
├── gesture/     Gesture recognition (predictor, buffer)
├── imu/         IMU tracking and analysis
├── nn/          Neural network architectures and training utilities
│   └── models/  Model checkpoints (not tracked by git)
└── unity/       Unity communication
```
