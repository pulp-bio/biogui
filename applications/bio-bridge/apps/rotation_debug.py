# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Rotation Debug Tool
====================

BioGUI IMU → Terminal rotation display only.

INPUT:  BioGUI TCP (IMU data only)
OUTPUT: None (no Unity)
TERMINAL: ncurses UI showing rotation angle, calibration status

Use Case:
- Debug/test IMU rotation tracking
- Verify gravity-based rotation algorithm
- No gesture recognition, no Unity output

Setup:
    1. BioGUI: Lowpass filter (Order 2, Cutoff 3 Hz)

Controls:
- C:   Calibrate neutral rotation
- R:   Reset angle to zero
- 1/2: Adjust smoothing
- Q:   Quit

Usage:
    python -m apps.rotation_debug
    python -m apps.rotation_debug --smoothing 0.8
"""

import argparse
import curses
import socket
import threading
import time

from core import (
    BIOGUI_HOST,
    BIOGUI_PORT,
    WULPUS_PACKET_FORMAT,
    decode_packet,
    recv_exact,
)
from imu.gravity_rotation import GravityRotationTracker


class State:
    """Shared state between threads."""

    def __init__(self, rotation_tracker: GravityRotationTracker):
        self.rotation_tracker = rotation_tracker

        self.connected = False
        self.packets = 0
        self.calibrating = False

        self.lock = threading.Lock()


def receiver_thread(state: State):
    """
    Background thread to receive WULPUS packets from BioGUI.
    Only processes IMU data for rotation tracking.
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

                            with state.lock:
                                # Update IMU rotation tracking
                                if state.calibrating:
                                    state.rotation_tracker.add_calibration_sample(imu)
                                else:
                                    state.rotation_tracker.update(imu)

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
    """Main curses loop for rotation debug."""

    # Initialize rotation tracker
    rotation_tracker = GravityRotationTracker(smoothing=args.smoothing)
    state = State(rotation_tracker)

    # Start receiver thread
    thread = threading.Thread(target=receiver_thread, args=(state,), daemon=True)
    thread.start()

    curses.curs_set(0)
    stdscr.nodelay(True)

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

            # Smoothing adjustment
            elif ch == ord("1"):
                state.rotation_tracker.smoothing = max(0.0, state.rotation_tracker.smoothing - 0.05)
                status = f"Smoothing: {state.rotation_tracker.smoothing:.2f}"
                status_time = time.time()

            elif ch == ord("2"):
                state.rotation_tracker.smoothing = min(
                    0.99, state.rotation_tracker.smoothing + 0.05
                )
                status = f"Smoothing: {state.rotation_tracker.smoothing:.2f}"
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

        # Clear old status messages
        if status and time.time() - status_time > 3:
            status = ""

        # === Display ===
        stdscr.clear()
        rt = state.rotation_tracker

        stdscr.addstr(0, 0, "=== ROTATION DEBUG ===")
        stdscr.addstr(1, 0, "C:calibrate  R:reset  1/2:smoothing  Q:quit")

        # Connection status
        conn_str = "CONNECTED" if state.connected else "waiting..."
        stdscr.addstr(3, 0, f"BioGUI: {conn_str} ({state.packets} packets)")

        # Calibration status
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

        # === Rotation Display ===
        stdscr.addstr(6, 0, "--- ROTATION ---")
        if rt.is_calibrated():
            angle = rt.get_angle()
            raw_angle = rt.get_raw_angle()
            abs_angle = abs(angle)

            # Visual rotation bar (-90° to +90°)
            bar_center = 40
            bar_width = 30
            bar_pos = int(bar_center + (angle / 90.0) * bar_width)
            bar_pos = max(10, min(70, bar_pos))

            bar = ""
            for i in range(10, 71):
                if i == bar_center:
                    bar += "|"  # Center mark
                elif abs(i - bar_pos) <= 1:
                    bar += "█"  # Current position
                elif i % 10 == 0:
                    bar += "·"  # Grid marks
                else:
                    bar += " "

            stdscr.addstr(7, 0, f"Angle:     {angle:+7.1f}°")
            stdscr.addstr(8, 0, f"Raw:       {raw_angle:+7.1f}°")
            stdscr.addstr(9, 0, f"Absolute:  {abs_angle:7.1f}°")
            stdscr.addstr(10, 0, f"          -90°{bar}+90°")
        else:
            stdscr.addstr(7, 0, "Angle: --- (not calibrated)")

        # === Parameters ===
        stdscr.addstr(13, 0, "--- PARAMETERS ---")
        stdscr.addstr(14, 0, f"[1/2] Smoothing: {rt.smoothing:.2f}")

        # Status message
        if status:
            stdscr.addstr(17, 0, f">>> {status}", curses.A_BOLD)

        stdscr.refresh()
        time.sleep(0.02)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Rotation Debug - Visualize IMU rotation tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Debug tool for testing IMU rotation tracking without Unity or gestures.

Examples:
  python -m apps.rotation_debug
  python apps/rotation_debug.py --smoothing 0.8
""",
    )
    parser.add_argument(
        "--smoothing",
        type=float,
        default=0.40,
        help="Rotation angle smoothing (0-1). Default: 0.40",
    )
    return parser.parse_args()


def main():
    """Entry point."""
    args = parse_args()

    print("=" * 70)
    print("Rotation Debug Tool")
    print("=" * 70)
    print(f"BioGUI: {BIOGUI_HOST}:{BIOGUI_PORT}")
    print(f"Rotation smoothing: {args.smoothing}")
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
