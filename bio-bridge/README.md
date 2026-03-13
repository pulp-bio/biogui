# BioBridge Middleware

Middleware for real-time gesture recognition from ultrasound data, connecting BioGUI to Unity for hand visualization.

TO-DO: add how to interface with Unity environment


## Set-up

Clone the project directory 
```bash
git clone </bio-bridge.git>
```

To run the bio-bridge, you need to install uv.

Note: the bio-bridge will run on his own environment, which is authomatically installed with the uv sync command 

Open a new terminal
```bash
# Check if uv is present
uv --version
# If uv is not yet installed, run
pip install uv 
# Then
uv sync
```

Go to project's directory
```bash
cd bio-bridge
```

Create a new folder called "models" under "nn", which will store the pre-trained Pytorch models, as well as additional info. 
```bash
cd nn
mkdir models
```
Note: the models folder will be automatically ignored by .gitignore. 
**TO-DO**: Discuss if we want to add some pre-trained models for reference. 




## Project Structure

The project has been refactored into a modular architecture following the DRY (Don't Repeat Yourself) principle:

```
bio-bridge/
├── core/                      # Shared configuration and utilities
│   ├── __init__.py
│   ├── config.py             # All constants, ports, paths
│   ├── signal.py             # Packet format definitions
│   └── utils.py              # Shared utility functions
├── gesture/                   # Gesture recognition components
│   ├── __init__.py
│   ├── predictor.py          # GesturePredictor class
│   └── buffer.py             # USDataBuffer class
├── unity/                     # Unity communication
│   ├── __init__.py
│   └── controller.py         # UnityController class
├── nn/                        # Neural network models
│   ├── __init__.py
│   ├── models/               # Saved model checkpoints
│   ├── us_encoder.py         # Network architecture
│   ├── train_utils.py        # Training utilities
│   └── seeds.py              # Reproducibility
├── imu/                       # IMU analysis and tracking
│   ├── __init__.py           # Shared IMU utilities
│   ├── data/                 # Recorded IMU data
│   ├── tracker.py            # PositionTracker class
│   ├── record.py             # Data recording tool
│   ├── plot.py               # Data visualization
│   ├── freq.py               # Frequency analysis
│   ├── freq_snr.py           # SNR-based analysis
│   └── integration_test.py   # Integration accuracy test
├── apps/                      # Application entry points
│   ├── __init__.py
│   ├── gesture_control.py    # Live gesture recognition → Unity
│   ├── keyboard_control.py   # Keyboard-only Unity control
│   ├── imu_control.py        # IMU position tracking → Unity
│   ├── inference.py          # CLI gesture inference
│   └── test_receiver.py      # BioGUI packet debugging
└── pyproject.toml            # Project configuration
```


## Quick Start

### Run Live HGR with US

1. Start the bio-bridge
To run the experiment of the paper, open one terminal. 
This will run the bio-bridge. 
```bash
uv run -m apps.multi_model_control --model 7class --flip-imu
```

Note: 
\bio-bridge\apps\multi_model_control.py
Here, we define the model that will be used. 


2. Set up data acquisition with biogui

```bash
# Activate the biogui virtual environment
conda activate <your_env>
# Launch the biogui
cd biogui
python main.py
```

Connect to WULPUS and Set the Forwarding mode. 

TO-DO:
Add detailed instructions here, with pictures!

3. Calibrate the IMU before starting the experiment
In the bio-bridge terminal, press -C to calibrate the IMU
```bash


### Other Applications

TO-DO: check what this is used for 

```bash

# Live gesture recognition with Unity control
python -m apps.gesture_control

# Keyboard-only control for testing
python -m apps.keyboard_control

# IMU-based position tracking
python -m apps.imu_control

# Command-line inference (no Unity)
python -m apps.inference

# Debug BioGUI packets
python -m apps.test_receiver
```

## Configuration

All configuration is centralized in `core/config.py`:

| Category | Constants                                                |
| -------- | -------------------------------------------------------- |
| Network  | `BIOGUI_HOST`, `BIOGUI_PORT`, `UNITY_HOST`, `UNITY_PORT` |
| Hardware | `NUM_US_SAMPLES`, `NUM_US_CHANNELS`, `MEAS_PERIOD`       |
| Model    | `DEFAULT_MODEL_PATH`, `NUM_CLASSES`, `GESTURE_MAP`       |
| Control  | `SEND_RATE`, `MOVE_SPEED_XZ`, `ROT_STEP`                 |
| Training | `DEFAULT_EPOCHS`, `DEFAULT_BATCH_SIZE`                   |
| IMU      | `CALIBRATION_SAMPLES`, `DEFAULT_VELOCITY_DECAY`          |

