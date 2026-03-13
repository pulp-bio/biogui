# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Rotation Control for Unity (Legacy 2-Class)
============================================

BioGUI IMU → rotation + BioGUI US → 2-class gesture → Unity.

INPUT:  BioGUI TCP (Ultrasound + IMU data)
OUTPUT: Unity UDP (gesture + IMU rotation)
TERMINAL: ncurses UI showing rotation angle, gesture, calibration

Use Case:
- 2-class gesture model (fist/open) + IMU rotation
- For rotationTask in Unity (CylinderDelivery, BottlePouring)
- Position NOT controlled (stays at start)

Setup:
    1. BioGUI: Lowpass filter (Order 2, Cutoff 3 Hz)

Controls:
- C:   Calibrate neutral rotation (hold probe still)
- R:   Reset angle to zero
- 1/2: Adjust rotation smoothing
- 3/4: Adjust gesture smoothing
- Q:   Quit

Model: Uses DEFAULT_MODEL_PATH (must be 2-class)

Usage:
    python -m apps.rotation_control
    python -m apps.rotation_control --smoothing 0.4
"""

import argparse
import curses
import socket
import threading
import time

from core import (
    BIOGUI_HOST,
    BIOGUI_PORT,
    DEFAULT_MODEL_PATH,
    PREDICTION_SMOOTHING,
    WULPUS_PACKET_FORMAT,
    decode_packet,
    recv_exact,
)
from gesture import GesturePredictor, USDataBuffer
from imu.gravity_rotation import GravityRotationTracker
from unity import UnityController


class State:
    """Shared state between threads."""

    def __init__(
        self,
        rotation_tracker: GravityRotationTracker,
        predictor: GesturePredictor,
        unity: UnityController,
    ):
        self.rotation_tracker = rotation_tracker
        self.predictor = predictor
        self.us_buffer = USDataBuffer()
        self.unity = unity

        self.connected = False
        self.packets = 0
        self.calibrating = False

        # Gesture state
        self.current_gesture = "Open"
        self.current_class_idx = 1  # 0=Fist, 1=Open
        self.gesture_confidence = 0.0

        self.lock = threading.Lock()


def receiver_thread(state: State):
    """
    Background thread to receive WULPUS packets from BioGUI.
    Processes IMU for rotation and ultrasound for gestures.
    """
    packet_size = WULPUS_PACKET_FORMAT.packet_size

    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
                srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                srv.bind((BIOGUI_HOST, BIOGUI_PORT))
                srv.listen(1)

                conn, _ = srv.accept()
                with state.lock:
                    state.connected = True

                with conn:
                    conn.settimeout(2.0)
                    while True:
                        try:
                            # Receive full WULPUS packet
                            packet = recv_exact(conn, packet_size)
                            decoded = decode_packet(packet)

                            imu = decoded["imu"]
                            us = decoded["ultrasound"]
                            config_id = int(decoded["tx_rx_id"][0])

                            with state.lock:
                                # Update IMU rotation tracking
                                if state.calibrating:
                                    state.rotation_tracker.add_calibration_sample(imu)
                                else:
                                    state.rotation_tracker.update(imu)

                                # Update ultrasound buffer
                                state.us_buffer.add_sample_to_channel(us, config_id)

                                # Run gesture prediction when buffer ready
                                if state.us_buffer.is_ready() and config_id == 0:
                                    us_data = state.us_buffer.get_data()
                                    class_idx, gesture_name, probs = state.predictor.predict(
                                        us_data
                                    )

                                    state.current_gesture = gesture_name
                                    state.current_class_idx = class_idx
                                    confidence = state.predictor.get_confidence(probs, class_idx)
                                    state.gesture_confidence = confidence / 100.0

                                state.packets += 1

                        except socket.timeout:
                            continue
                        except ConnectionError:
                            break

        except Exception:
            pass

        with state.lock:
            state.connected = False
        time.sleep(1)


def main_curses(stdscr, args):
    """Main curses loop."""

    # Check model exists
    if not DEFAULT_MODEL_PATH.exists():
        print(f"ERROR: Model not found at {DEFAULT_MODEL_PATH}")
        print("Please train a model first: python -m apps.training")
        return

    # Initialize components
    rotation_tracker = GravityRotationTracker(smoothing=args.rotation_smoothing)
    predictor = GesturePredictor(model_path=DEFAULT_MODEL_PATH)
    unity = UnityController(thread_safe=False, smoothing=args.gesture_smoothing)
    unity.reset()

    state = State(rotation_tracker, predictor, unity)

    # Start receiver thread
    thread = threading.Thread(target=receiver_thread, args=(state,), daemon=True)
    thread.start()

    curses.curs_set(0)
    stdscr.nodelay(True)

    last_send = time.time()
    status = ""
    status_time = 0

    while True:
        ch = stdscr.getch()
        if ch != -1:
            if ch in (ord("q"), ord("Q"), 27):
                break

            elif ch in (ord("c"), ord("C")):
                with state.lock:
                    state.rotation_tracker.start_calibration()
                    state.calibrating = True
                status = "CALIBRATING... keep arm in neutral position!"
                status_time = time.time()

            elif ch in (ord("r"), ord("R")):
                with state.lock:
                    state.rotation_tracker.reset()
                status = "Angle reset to zero"
                status_time = time.time()

            # Rotation smoothing
            elif ch == ord("1"):
                state.rotation_tracker.smoothing = max(0.0, state.rotation_tracker.smoothing - 0.05)
                status = f"Rotation smoothing: {state.rotation_tracker.smoothing:.2f}"
                status_time = time.time()

            elif ch == ord("2"):
                state.rotation_tracker.smoothing = min(
                    0.99, state.rotation_tracker.smoothing + 0.05
                )
                status = f"Rotation smoothing: {state.rotation_tracker.smoothing:.2f}"
                status_time = time.time()

            # Gesture smoothing
            elif ch == ord("3"):
                state.unity.smoothing = max(1, state.unity.smoothing - 1)
                status = f"Gesture smoothing: {state.unity.smoothing}"
                status_time = time.time()

            elif ch == ord("4"):
                state.unity.smoothing = min(20, state.unity.smoothing + 1)
                status = f"Gesture smoothing: {state.unity.smoothing}"
                status_time = time.time()

        # Check calibration completion
        with state.lock:
            cal_progress, cal_required = state.rotation_tracker.get_calibration_progress()
            if state.calibrating:
                if cal_progress >= cal_required:
                    if state.rotation_tracker.finish_calibration():
                        status = "Calibration complete!"
                    else:
                        status = "Calibration failed"
                    state.calibrating = False
                    status_time = time.time()

        # Send to Unity at ~30 Hz
        if time.time() - last_send > 0.033:
            with state.lock:
                # Get rotation angle
                angle = state.rotation_tracker.get_angle()
                abs_angle = abs(angle)

                # Send absolute value so Unity always shows positive rotation
                unity.set_rotation([0.0, 0.0, abs_angle])

                # Update gesture with smoothing
                unity.update_gesture(state.current_class_idx, state.gesture_confidence)

            unity.send()
            last_send = time.time()

        # Clear old status
        if status and time.time() - status_time > 3:
            status = ""

        # === Display ===
        stdscr.clear()
        rt = state.rotation_tracker

        stdscr.addstr(0, 0, "=== ROTATION UNITY CONTROL ===")
        stdscr.addstr(1, 0, "C:calibrate  R:reset  1/2:rot smooth  3/4:gest smooth  Q:quit")

        # Connection
        conn_str = "CONNECTED" if state.connected else "waiting..."
        stdscr.addstr(3, 0, f"BioGUI: {conn_str} ({state.packets} packets)")

        # Calibration
        if state.calibrating:
            pct = cal_progress * 100 // cal_required
            stdscr.addstr(
                4,
                0,
                f"CALIBRATING: {pct}% ({cal_progress}/{cal_required})",
                curses.A_BOLD,
            )
        else:
            cal_str = "YES" if rt.is_calibrated() else "NO (press C)"
            stdscr.addstr(4, 0, f"Calibrated: {cal_str}")

        # === Rotation ===
        stdscr.addstr(6, 0, "--- ROTATION ---")
        if rt.is_calibrated():
            angle = rt.get_angle()
            abs_angle = abs(angle)

            # Visual bar
            bar_center = 40
            bar_width = 30
            bar_pos = int(bar_center + (angle / 90.0) * bar_width)
            bar_pos = max(10, min(70, bar_pos))

            bar = ""
            for i in range(10, 71):
                if i == bar_center:
                    bar += "|"
                elif abs(i - bar_pos) <= 1:
                    bar += "█"
                elif i % 10 == 0:
                    bar += "·"
                else:
                    bar += " "

            stdscr.addstr(7, 0, f"Angle:       {angle:+7.1f}°")
            stdscr.addstr(8, 0, f"To Unity:    {abs_angle:7.1f}° (absolute)")
            stdscr.addstr(9, 0, f"            -90°{bar}+90°")
        else:
            stdscr.addstr(7, 0, "Angle: --- (not calibrated)")

        # === Gesture ===
        stdscr.addstr(11, 0, "--- GESTURE ---")
        with state.lock:
            gesture = state.current_gesture
            confidence = state.gesture_confidence

        stdscr.addstr(12, 0, f"Detected:   {gesture:8s}")
        stdscr.addstr(13, 0, f"Confidence: {confidence * 100:5.1f}%")

        # Confidence bar
        conf_bar_len = int(confidence * 40)
        conf_bar = "█" * conf_bar_len + "·" * (40 - conf_bar_len)
        stdscr.addstr(14, 0, f"[{conf_bar}]")

        # === Parameters ===
        stdscr.addstr(16, 0, "--- PARAMETERS ---")
        stdscr.addstr(17, 0, f"[1/2] Rotation smoothing: {rt.smoothing:.2f}")
        stdscr.addstr(18, 0, f"[3/4] Gesture smoothing:  {unity.smoothing}")
        stdscr.addstr(19, 0, f"Model: {DEFAULT_MODEL_PATH.name}")

        # Status
        if status:
            stdscr.addstr(22, 0, f">>> {status}", curses.A_BOLD)

        stdscr.refresh()
        time.sleep(0.02)

    unity.close()


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Rotation Unity Control - Send rotation + gestures to Unity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Sends absolute rotation angle and gesture predictions to Unity.

Examples:
  python -m apps.rotation_control
  python apps/rotation_control.py --rotation-smoothing 0.4 --gesture-smoothing 5
""",
    )
    parser.add_argument(
        "--rotation-smoothing",
        type=float,
        default=0.0,
        help="Rotation angle smoothing (0-1). Default: 0.0 (no smoothing)",
    )
    parser.add_argument(
        "--gesture-smoothing",
        type=int,
        default=PREDICTION_SMOOTHING,
        help=f"Gesture prediction smoothing window. Default: {PREDICTION_SMOOTHING}",
    )
    return parser.parse_args()


def main():
    """Entry point."""
    args = parse_args()

    print("=" * 70)
    print("Rotation Unity Control")
    print("=" * 70)
    print(f"BioGUI: {BIOGUI_HOST}:{BIOGUI_PORT}")
    print(f"Model: {DEFAULT_MODEL_PATH}")
    print(f"Rotation smoothing: {args.rotation_smoothing}")
    print(f"Gesture smoothing:  {args.gesture_smoothing}")
    print("=" * 70)
    print()

    try:
        curses.wrapper(main_curses, args)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
