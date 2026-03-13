"""
IMU Position Control for Unity
===============================

IMU acceleration → position tracking. Keyboard for gestures.

INPUT:  BioGUI TCP (IMU acceleration data)
OUTPUT: Unity UDP (position from IMU + keyboard gestures)
TERMINAL: ncurses UI showing position, velocity, calibration

Use Case:
- Position tracking via IMU acceleration (experimental)
- Gestures controlled by keyboard (not NN)
- Does NOT do rotation tracking

Setup:
    1. BioGUI: Lowpass filter (Order 2, Cutoff 3 Hz)
    2. Do NOT use Bandpass

Controls:
- C:       Calibrate (hold probe still for 3s)
- R:       Reset position to origin
- Space:   Toggle fist/open
- F/O:     Fist/Open
- 1-8:     Adjust thresholds and scaling
- Q:       Quit

Usage:
    python -m apps.imu_control
    python -m apps.imu_control --start-threshold 0.35 --scale 0.4
"""

import argparse
import curses
import socket
import threading
import time

from core import (
    BIOGUI_HOST,
    BIOGUI_PORT,
    CALIBRATION_SAMPLES,
    DEFAULT_POSITION_SCALE,
    DEFAULT_START_THRESHOLD,
    DEFAULT_STOP_THRESHOLD,
    DEFAULT_VELOCITY_DECAY,
    WULPUS_PACKET_FORMAT,
    decode_packet,
    recv_exact,
)
from imu.tracker import MovementState, PositionTracker
from unity import UnityController


class State:
    """Shared state between threads."""

    def __init__(self, tracker: PositionTracker):
        self.tracker = tracker
        self.connected = False
        self.packets = 0
        self.is_fist = False
        self.calibrating = False
        self.lock = threading.Lock()


def receiver_thread(state: State):
    """Background thread to receive IMU data from BioGUI.

    Receives full WULPUS packets (acquisition_number + imu + tx_rx_id + ultrasound) but only
    uses the IMU data for position tracking.
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

                            # Decode packet to get acquisition_number, imu, tx_rx_id, ultrasound
                            decoded = decode_packet(packet)

                            # Extract IMU data (we ignore acquisition_number, tx_rx_id and ultrasound)
                            imu = decoded["imu"]

                            with state.lock:
                                if state.calibrating:
                                    state.tracker.add_calibration_sample(imu)
                                else:
                                    state.tracker.update(imu)
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
    """Main curses loop for IMU control."""
    # Initialize tracker with command-line arguments
    tracker = PositionTracker(
        start_threshold=args.start_threshold,
        stop_threshold=args.stop_threshold,
        scale=args.scale,
        velocity_decay=args.decay,
    )

    state = State(tracker)

    # Start receiver thread
    thread = threading.Thread(target=receiver_thread, args=(state,), daemon=True)
    thread.start()

    # Initialize Unity controller
    unity = UnityController(thread_safe=False)

    curses.curs_set(0)
    stdscr.nodelay(True)

    last_send = time.time()
    status = ""
    status_time = 0
    cal_progress = 0

    while True:
        ch = stdscr.getch()
        if ch != -1:
            if ch in (ord("q"), ord("Q"), 27):
                break

            elif ch in (ord("c"), ord("C")):
                with state.lock:
                    state.tracker.start_calibration()
                    state.calibrating = True
                status = "CALIBRATING... keep still!"
                status_time = time.time()

            elif ch in (ord("r"), ord("R")):
                with state.lock:
                    state.tracker.reset()
                status = "Position reset"
                status_time = time.time()

            elif ch == ord(" "):
                with state.lock:
                    state.is_fist = not state.is_fist

            elif ch in (ord("f"), ord("F")):
                with state.lock:
                    state.is_fist = True

            elif ch in (ord("o"), ord("O")):
                with state.lock:
                    state.is_fist = False

            # Scale adjustment
            elif ch == ord("1"):
                state.tracker.scale = max(0.1, state.tracker.scale - 0.1)
                status = f"Scale: {state.tracker.scale:.1f}"
                status_time = time.time()

            elif ch == ord("2"):
                state.tracker.scale += 0.1
                status = f"Scale: {state.tracker.scale:.1f}"
                status_time = time.time()

            # Start threshold adjustment
            elif ch == ord("3"):
                state.tracker.start_threshold = max(
                    0.1, state.tracker.start_threshold - 0.05
                )
                status = f"Start threshold: {state.tracker.start_threshold:.2f} m/s²"
                status_time = time.time()

            elif ch == ord("4"):
                state.tracker.start_threshold += 0.05
                status = f"Start threshold: {state.tracker.start_threshold:.2f} m/s²"
                status_time = time.time()

            # Stop threshold adjustment
            elif ch == ord("5"):
                state.tracker.stop_threshold = max(
                    0.05, state.tracker.stop_threshold - 0.05
                )
                status = f"Stop threshold: {state.tracker.stop_threshold:.2f} m/s²"
                status_time = time.time()

            elif ch == ord("6"):
                state.tracker.stop_threshold = min(
                    state.tracker.start_threshold - 0.05,
                    state.tracker.stop_threshold + 0.05,
                )
                status = f"Stop threshold: {state.tracker.stop_threshold:.2f} m/s²"
                status_time = time.time()

            # Velocity decay adjustment
            elif ch == ord("7"):
                state.tracker.velocity_decay = max(
                    0.8, state.tracker.velocity_decay - 0.01
                )
                status = f"Velocity decay: {state.tracker.velocity_decay:.2f}"
                status_time = time.time()

            elif ch == ord("8"):
                state.tracker.velocity_decay = min(
                    0.99, state.tracker.velocity_decay + 0.01
                )
                status = f"Velocity decay: {state.tracker.velocity_decay:.2f}"
                status_time = time.time()

        # Check calibration done
        with state.lock:
            cal_progress, cal_required = state.tracker.get_calibration_progress()
            if state.calibrating:
                if cal_progress >= cal_required:
                    if state.tracker.finish_calibration():
                        status = "Calibrated!"
                    else:
                        status = "Calibration failed"
                    state.calibrating = False
                    status_time = time.time()

        # Send to Unity
        if time.time() - last_send > 0.033:  # ~30 Hz
            with state.lock:
                pos = state.tracker.get_unity_position()
                unity.set_position(pos)
                if state.is_fist:
                    unity.set_gesture("fist")
                else:
                    unity.set_gesture("open")
            unity.send()
            last_send = time.time()

        # Clear old status
        if status and time.time() - status_time > 3:
            status = ""

        # Display
        stdscr.clear()
        t = state.tracker

        stdscr.addstr(0, 0, "=== IMU POSITION TRACKER ===")
        stdscr.addstr(1, 0, "C:calibrate  R:reset  Space:gesture  Q:quit")
        stdscr.addstr(2, 0, "1/2:scale  3/4:start thr  5/6:stop thr  7/8:decay")

        conn_str = "CONNECTED" if state.connected else "waiting..."
        stdscr.addstr(4, 0, f"BioGUI: {conn_str} ({state.packets} packets)")

        if state.calibrating:
            pct = cal_progress * 100 // CALIBRATION_SAMPLES
            stdscr.addstr(
                5,
                0,
                f"CALIBRATING: {pct}% ({cal_progress}/{CALIBRATION_SAMPLES})",
                curses.A_BOLD,
            )
        else:
            cal_str = "YES" if t.calibrated else "NO (press C)"
            stdscr.addstr(5, 0, f"Calibrated: {cal_str}")

        # State
        stdscr.addstr(6, 0, f"State: {t.get_state_name()}  dt={t.dt:.4f}s")
        stdscr.addstr(7, 0, f"Gesture: {'FIST' if state.is_fist else 'OPEN'}")

        # Debug: show gravity after calibration
        if t.calibrated:
            g = t.gravity
            stdscr.addstr(
                8, 0, f"Gravity: [{g[0]:+.1f}, {g[1]:+.1f}, {g[2]:+.1f}] (raw units)"
            )
        else:
            stdscr.addstr(8, 0, "Gravity: not calibrated")

        # Direction (if moving)
        if t.state == MovementState.MOVING:
            md = t.movement_direction
            stdscr.addstr(
                9, 0, f"Direction: [{md[0]:+.2f}, {md[1]:+.2f}, {md[2]:+.2f}]"
            )
        else:
            stdscr.addstr(9, 0, "Direction: ---")

        # Values
        stdscr.addstr(
            11,
            0,
            f"Accel:    [{t.accel[0]:+.3f}, {t.accel[1]:+.3f}, {t.accel[2]:+.3f}] m/s²",
        )
        stdscr.addstr(
            12,
            0,
            f"Velocity: [{t.velocity[0]:+.3f}, {t.velocity[1]:+.3f}, {t.velocity[2]:+.3f}] m/s",
        )
        stdscr.addstr(
            13,
            0,
            f"Position: [{t.position[0]:+.3f}, {t.position[1]:+.3f}, {t.position[2]:+.3f}] m",
        )

        # Acceleration bar with thresholds
        accel_mag = t.get_accel_magnitude()
        velocity_mag = t.get_velocity_magnitude()
        bar_max = t.start_threshold * 2
        bar_len = min(30, int(accel_mag / bar_max * 30))
        stop_pos = int(t.stop_threshold / bar_max * 30)
        start_pos = int(t.start_threshold / bar_max * 30)

        bar = ""
        for i in range(30):
            if i < bar_len:
                bar += "█"
            elif i == stop_pos:
                bar += "|"
            elif i == start_pos:
                bar += "|"
            else:
                bar += "·"

        stdscr.addstr(15, 0, f"|Accel|: {accel_mag:.2f} [{bar}]")
        stdscr.addstr(
            16,
            0,
            f"         stop={t.stop_threshold:.2f}  start={t.start_threshold:.2f}",
        )
        stdscr.addstr(17, 0, f"|Veloc|: {velocity_mag:.3f} m/s")

        # Parameters
        stdscr.addstr(19, 0, "--- Parameters ---")
        stdscr.addstr(20, 0, f"[1/2] Scale:           {t.scale:.1f}")
        stdscr.addstr(21, 0, f"[3/4] Start threshold: {t.start_threshold:.2f} m/s²")
        stdscr.addstr(22, 0, f"[5/6] Stop threshold:  {t.stop_threshold:.2f} m/s²")
        stdscr.addstr(23, 0, f"[7/8] Velocity decay:  {t.velocity_decay:.2f}")

        if status:
            stdscr.addstr(27, 0, f">>> {status}", curses.A_BOLD)

        stdscr.refresh()
        time.sleep(0.02)

    unity.close()


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="IMU Position Tracker with Direction Tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
How it works:
  - State machine: STATIONARY <-> MOVING
  - STATIONARY: Wait for accel > start_threshold to begin moving
  - MOVING: Track movement direction
    - Acceleration in same direction -> increase velocity
    - Acceleration in opposite direction -> decrease velocity (not reverse!)
  - Velocity decay acts like friction to prevent runaway movement

Examples:
  python apps/imu_control.py
  python apps/imu_control.py --start-threshold 0.35 --stop-threshold 0.15
  python apps/imu_control.py --decay 0.88
""",
    )
    parser.add_argument(
        "--start-threshold",
        type=float,
        default=DEFAULT_START_THRESHOLD,
        help=f"Threshold to start moving [m/s²] (default: {DEFAULT_START_THRESHOLD})",
    )
    parser.add_argument(
        "--stop-threshold",
        type=float,
        default=DEFAULT_STOP_THRESHOLD,
        help=f"Threshold to stop moving [m/s²] (default: {DEFAULT_STOP_THRESHOLD})",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=DEFAULT_POSITION_SCALE,
        help=f"Position scale factor (default: {DEFAULT_POSITION_SCALE})",
    )
    parser.add_argument(
        "--decay",
        type=float,
        default=DEFAULT_VELOCITY_DECAY,
        help=f"Velocity decay per sample (default: {DEFAULT_VELOCITY_DECAY})",
    )
    return parser.parse_args()


def main():
    """Entry point."""
    args = parse_args()

    print("=" * 70)
    print("IMU Position Tracker")
    print("=" * 70)
    print(f"BioGUI: {BIOGUI_HOST}:{BIOGUI_PORT}")
    print("Parameters:")
    print(f"  Start threshold: {args.start_threshold} m/s²")
    print(f"  Stop threshold:  {args.stop_threshold} m/s²")
    print(f"  Position scale:  {args.scale}")
    print(f"  Velocity decay:  {args.decay}")
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
