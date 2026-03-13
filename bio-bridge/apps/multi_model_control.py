"""
Multi-Model Control for Unity
=============================

Pose (7 gestures) + Position (3 positions) + IMU rotation → Unity.

INPUT:  BioGUI TCP (6 US channels + IMU)
OUTPUT: Unity UDP (gesture, position, rotationIMU)

Controls: C=Calibrate, Q=Quit

Usage:
    python -m apps.multi_model_control
    python -m apps.multi_model_control --smoothing 10
    python -m apps.multi_model_control --debug
"""

import argparse
import curses
import socket
import threading
import time
from collections import Counter
from pathlib import Path
import numpy as np

from core import (
    BIOGUI_HOST,
    BIOGUI_PORT,
    CALIBRATION_SAMPLES,
    PREDICTION_SMOOTHING,
    SEND_RATE,
    WULPUS_PACKET_FORMAT,
    decode_packet,
    recv_exact,
)
from gesture import GesturePredictor, USDataBuffer, IMUDataBuffer
from imu.gravity_rotation import GravityRotationTracker
from nn.nn_utils import * 
from unity import UnityController

# =============================================================================
# Configuration
# =============================================================================

MODEL_DIR = Path(__file__).parent.parent / "nn" / "models"
NUM_TRANSDUCERS = 6
NUM_IMU_CHANNELS = 3


MODELS = {
    "6class": {
        "pose_path": MODEL_DIR / "ft_1" /  "pose_model_final_ft_1_1rep.pth",
        "pose_meta_path": MODEL_DIR / "ft_1" / "additional_info_pose_ft.json",
        "pose_num_classes": 6,
        "pose_classes": {
            0: "open",
            1: "pinch",
            2: "pour",
            3: "rest",
            4: "rotclosed",
            5: "rotopen",
        },
        "position_path": MODEL_DIR  / "ft_1" /  "position_model_final_ft_1_1rep.pth",
        "position_meta_path": MODEL_DIR / "ft_1" / "additional_info_position_ft.json",
        "position_classes": {0: "start", 1: "forward", 2: "right"},
    },
        "6class_zero_shot": {
        "pose_path": MODEL_DIR / "zero_shot" /  "pose_model_final.pth",
        "pose_meta_path": MODEL_DIR / "zero_shot" / "additional_info_pose.json",
        "pose_num_classes": 6,
        "pose_classes": {
            0: "open",
            1: "pinch",
            2: "pour",
            3: "rest",
            4: "rotclosed",
            5: "rotopen",
        },
        "position_path": MODEL_DIR  / "zero_shot" /  "position_model_final.pth",
        "position_meta_path": MODEL_DIR / "zero_shot" / "additional_info_position.json",
        "position_classes": {0: "start", 1: "forward", 2: "right"},
    },
    "7class": {
        "pose_path": MODEL_DIR / "ft_3_4tasks" /  "pose_model_final_ft_2_3rep.pth",
        "pose_meta_path": MODEL_DIR / "ft_3_4tasks" / "additional_info_pose_ft.json",
        "pose_num_classes": 7,
        "pose_classes": {
            0: "rest",
            1: "open",
            2: "rotopen",
            3: "close",
            4: "rotclosed",
            5: "pinch",
            6: "pour",
        },
        "position_path": MODEL_DIR  / "ft_3_4tasks" /  "position_model_final_ft_2_3rep.pth",
        "position_meta_path": MODEL_DIR / "ft_3_4tasks" / "additional_info_position_ft.json",
        "position_classes": {0: "start", 1: "forward", 2: "right"},
    },
    "3class": {
        "pose_path": MODEL_DIR / "3class" / "fold_1_pose_model.pth",
        "pose_meta_path": MODEL_DIR / "3class" / "additional_info_pose_ft.json",
        "pose_num_classes": 3,
        "pose_classes": {0: "rest", 1: "open", 2: "close"},
        "position_path": MODEL_DIR / "3class" / "fold_1_position_model.pth",
        "position_meta_path": MODEL_DIR / "3class" / "additional_info_position_ft.json",
        "position_classes": {0: "start", 1: "forward", 2: "right"},
    },
}

# Mapping from 7 pose classes to 4 Unity gestures
POSE_TO_UNITY = {
    "rest": "rest",
    "open": "open",
    "rotopen": "open",  # rotopen → open
    "close": "close",
    "rotclosed": "close",  # rotclosed → close
    "pinch": "pinch",
    "pour": "close",  # pour → close
}


# =============================================================================
# Shared State
# =============================================================================


class State:
    def __init__(self, smoothing: int, config: dict):
        self.gesture = "rest"
        self.gesture_idx = 0
        self.gesture_conf = 0.0
        self.position = "start"
        self.position_idx = 0
        self.position_conf = 0.0
        self.imu_angle = 0.0
        self.connected = False
        self.packets = 0
        self.calibrating = False
        self.cal_progress = 0
        self.gesture_history: list[int] = []
        self.position_history: list[int] = []
        self.smoothing = smoothing
        self.config = config
        self.debug_msg = ""
        self.lock = threading.Lock()


# =============================================================================
# BioGUI Receiver Thread
# =============================================================================


def receiver_thread(
    state, 
    us_buffer, 
    imu_buffer, 

    pose_model, 
    use_imu_pose_model, 

    position_model, 
    use_imu_position_model, 

    imu_tracker, 
    running, 
    debug
):
    print("Receiver thread started")  # Log when the thread starts

    packet_size = WULPUS_PACKET_FORMAT.packet_size

    while running["active"]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((BIOGUI_HOST, BIOGUI_PORT))
                server.listen(1)
                server.settimeout(1.0)

                while running["active"]:
                    try:
                        conn, addr = server.accept()
                        with state.lock:
                            state.connected = True
                            state.debug_msg = f"Connected: {addr}"

                        try:
                            while running["active"]:
                                data = recv_exact(conn, packet_size)
                                #print(f"Data received: {data}")  # Log received data
                                if not data:
                                    break

                                packet = decode_packet(data)
                                config_id = int(packet["tx_rx_id"])
                                us_data = packet["ultrasound"]
                                imu_data = packet["imu"]
                                
                                


                                with state.lock:
                                    state.packets += 1

                                # IMU
                                imu_array = None
                                if imu_data is not None:
                                    if state.calibrating:
                                        imu_tracker.add_calibration_sample(imu_data)
                                        state.cal_progress = len(
                                            imu_tracker.cal_samples
                                        )
                                        if state.cal_progress >= CALIBRATION_SAMPLES:
                                            imu_tracker.finish_calibration()
                                            state.calibrating = False
                                    else:
                                        # Update rotation estimate. 
                                        # Note: this takes into account the calibration 
                                        imu_tracker.update(imu_data)

                                    imu_array = np.asarray(imu_data, dtype=np.float32)

                                # US buffer
                                if config_id < NUM_TRANSDUCERS:
                                    # Append new US sample to the channel
                                    us_buffer.add_sample_to_channel(us_data, config_id)
                                    # Append newly received IMU sample to the buffer
                                    if imu_array is not None: 
                                        imu_buffer.push_imu_sample(imu_array)

                                # Inference
                                if us_buffer.is_ready():
                                    us_array = us_buffer.get_data()
                                    # Get Current IMU data.
                                    # TO-DO: Implement Circular Buffer, as for US data. Smooth every NUM_TRANSDUCERS frames
                                    

                                    if use_imu_pose_model:
                                        imu_smooth = imu_buffer.get_imu_samples().mean(axis=1)
                                        pose_idx, _, pose_probs = pose_model.predict(us_array, pose_model.us_idx_to_consider, imu_smooth)
                                    else: 
                                        pose_idx, _, pose_probs = pose_model.predict(us_array, pose_model.us_idx_to_consider, None)
                                    if use_imu_position_model:
                                        imu_smooth = imu_buffer.get_imu_samples().mean(axis=1)
                                        pos_idx, _, pos_probs = position_model.predict(us_array, position_model.us_idx_to_consider, imu_smooth)
                                    else:
                                        pos_idx, _, pos_probs = position_model.predict(us_array, position_model.us_idx_to_consider, None)

                                    print(f"US buffer ready: {us_buffer.is_ready()}")  # Log if US buffer is ready
                                    print(f"US data shape: {us_array.shape}")  # Log shape of US data
                                    if use_imu_position_model or use_imu_pose_model:
                                        print(f"IMU data:", imu_smooth)
                                    print(f"Pose index: {pose_idx}, Position index: {pos_idx}")  # Log pose and position indices

                                    with state.lock:
                                        state.gesture_history.append(pose_idx)
                                        state.position_history.append(pos_idx)
                                        if (
                                            len(state.gesture_history)
                                            >= state.smoothing
                                        ):
                                            state.gesture_history.pop(0)
                                        if (
                                            len(state.position_history)
                                            >= state.smoothing
                                        ):
                                            state.position_history.pop(0)
                                        state.gesture_idx = Counter(
                                            state.gesture_history
                                        ).most_common(1)[0][0]
                                        state.position_idx = Counter(
                                            state.position_history
                                        ).most_common(1)[0][0]
                                        state.gesture = state.config[
                                            "pose_classes"
                                        ].get(state.gesture_idx, "rest")
                                        state.position = state.config[
                                            "position_classes"
                                        ].get(state.position_idx, "start")
                                        state.gesture_conf = pose_probs[pose_idx] * 100
                                        state.position_conf = pos_probs[pos_idx] * 100

                        except Exception as e:
                            with state.lock:
                                state.debug_msg = f"Error: {e}"
                        finally:
                            conn.close()
                            with state.lock:
                                state.connected = False

                    except socket.timeout:
                        continue

        except Exception as e:
            with state.lock:
                state.debug_msg = f"Server error: {e}"
            time.sleep(1)


# =============================================================================
# Main
# =============================================================================


def main_curses(stdscr, args, config):
    print("main_curses started")  # Log entry
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)

    # Load models
    try:
        pose_model = GesturePredictor(
            config["pose_path"],
            config["pose_model_metadata"],
            len(config["transducers_pose"]),
            config["pose_num_classes"],
            config["pose_classes"],
        )
        use_imu_pose = config["pose_model_metadata"].get("use_imu", False)
        print("POSE MODEL LOADED SUCCESSFULLY")
        

        
        
        position_model = GesturePredictor(
            config["position_path"],
            config["position_model_metadata"],
            len(config["transducers_position"]),
            len(config["position_classes"]),
            config["position_classes"],
        )
        use_imu_position = config["position_model_metadata"].get("use_imu", False)
        print("POSITION MODEL loaded successfully")  # Log success
    except Exception as e:
        print(f"Failed to load models: {e}")  # Log to console
        import traceback
        traceback.print_exc()
        stdscr.addstr(0, 0, f"Failed to load models: {e}")
        stdscr.addstr(2, 0, "Press any key to exit.")
        stdscr.refresh()
        stdscr.nodelay(False)
        stdscr.getch()
        return

    print("Initializing state and buffers")  # Log initialization
    state = State(smoothing=args.smoothing, config=config)
    us_buffer = USDataBuffer(num_channels=NUM_TRANSDUCERS)
    imu_buffer = IMUDataBuffer(num_imu_channels=NUM_IMU_CHANNELS, imu_samples_to_buffer=NUM_TRANSDUCERS)
    flip_imu = args.flip_imu

    imu_tracker = GravityRotationTracker(
        smoothing=args.imu_smoothing, 
        flip_imu=flip_imu)
    unity = UnityController(thread_safe=True)

    running = {"active": True}
    thread = threading.Thread(
        target=receiver_thread,
        args=(
            state,
            us_buffer,
            imu_buffer, 

            pose_model,
            use_imu_pose, 

            position_model,
            use_imu_position, 

            imu_tracker,
            running,

            args.debug,
        ),
        daemon=True,
    )
    thread.start()
    print("Receiver thread started")  # Log thread start

    last_send = time.perf_counter()
    print("Entering main loop")  # Log before entering loop

    try:
        while True:
            try:
                key = stdscr.getch()
                if key in (ord("q"), ord("Q"), 27):
                    break
                elif key in (ord("c"), ord("C")):
                    imu_tracker.start_calibration()
                    state.calibrating = True
                    state.cal_progress = 0
            except Exception as e:
                print(f"Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                break

            state.imu_angle = imu_tracker.get_angle()

            now = time.perf_counter()
            if now - last_send >= 1.0 / SEND_RATE:
                last_send = now
                with state.lock:
                    # Map 7 pose classes to 4 Unity gestures
                    unity_gesture = POSE_TO_UNITY.get(state.gesture, "rest")
                    unity.set_gesture(unity_gesture)
                    unity.set_position_state(state.position)
                    unity.set_rotation(0.0, 0.0, state.imu_angle)
                    unity.send()

            # UI
            stdscr.clear()
            stdscr.addstr(0, 0, "Multi-Model Control")
            stdscr.addstr(1, 0, "-" * 40)

            with state.lock:
                status = "CONNECTED" if state.connected else "Waiting..."
                stdscr.addstr(3, 0, f"Status: {status}  Packets: {state.packets}")

                if state.calibrating:
                    bar = "#" * (state.cal_progress * 20 // CALIBRATION_SAMPLES)
                    stdscr.addstr(4, 0, f"IMU: Calibrating [{bar:<20}]")
                elif imu_tracker.is_calibrated:
                    stdscr.addstr(4, 0, "IMU: Calibrated ✓")
                else:
                    stdscr.addstr(4, 0, "IMU: Press C to calibrate")

                unity_gesture = POSE_TO_UNITY.get(state.gesture, "rest")
                stdscr.addstr(
                    6,
                    0,
                    f"Pose:     {state.gesture:<12} → {unity_gesture:<8} ({state.gesture_conf:5.1f}%)",
                )
                stdscr.addstr(
                    7,
                    0,
                    f"Position: {state.position:<12}   ({state.position_conf:5.1f}%)",
                )
                stdscr.addstr(8, 0, f"IMU:      {state.imu_angle:+.1f}°")

                if args.debug:
                    stdscr.addstr(10, 0, f"Debug: {state.debug_msg[:50]}")
                    stdscr.addstr(12, 0, "C=Calibrate  Q=Quit")
                else:
                    stdscr.addstr(10, 0, "C=Calibrate  Q=Quit")

            stdscr.refresh()

    finally:
        running["active"] = False
        thread.join(timeout=1.0)


def main():
    parser = argparse.ArgumentParser(description="Multi-Model Control")
    parser.add_argument("--model", default="7class")
    parser.add_argument(
        "--smoothing",
        type=int,
        default=PREDICTION_SMOOTHING,
        help="Majority vote window size",
    )
    parser.add_argument(
        "--imu-smoothing", type=float, default=0.0, help="IMU smoothing (0.0-1.0)"
    )
    parser.add_argument("--debug", action="store_true", help="Debug output")
    parser.add_argument(
        "--flip-imu",
        action="store_true",
        help="Set to flip imu angle rotation",
    )
    args = parser.parse_args()

    config = MODELS[args.model]

    pose_model_metadata = load_json(config["pose_meta_path"])
    position_model_metadata = load_json(config["position_meta_path"])

    config["pose_model_metadata"] = pose_model_metadata
    config["transducers_pose"] = pose_model_metadata.get("transducers_used")
    print("Retrieved pose transducwers", config["transducers_pose"])
    config["use_imu_pose_nn"] = pose_model_metadata.get("use_imu", False)

    config["position_model_metadata"] = position_model_metadata
    config["use_imu_position_nn"] = position_model_metadata.get("use_imu", False)
    config["transducers_position"] = position_model_metadata.get("transducers_used")
    print("Retrieved position transducerd", config["transducers_position"])


    print(f"Model:     {args.model}")
    print(
        f"Pose:      {config['pose_path'].name} ({config['pose_num_classes']} classes) - IMU input: {config['use_imu_pose_nn']}"
    )
    print(
        f"Position:  {config['position_path'].name} ({len(config['position_classes'])} classes) - IMU input: {config['use_imu_position_nn']}"
    )
    print(f"Smoothing: {args.smoothing}")
    print(f"Flip IMU:  {args.flip_imu}")
    print()

    try:
        curses.wrapper(main_curses, args, config)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"ERROR in main_curses: {e}")
        import traceback
        traceback.print_exc()
    print("Stopped.")


if __name__ == "__main__":
    main()
