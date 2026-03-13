# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
IMU Data Recorder

Collects raw acceleration data from BioGUI for analysis.
Records stationary and movement data with calibration support.

Usage (from bio-bridge directory):
    python imu/record.py <testname>

Examples:
    python imu/record.py rest
    python imu/record.py move_slow
    python imu/record.py move_medium
    python imu/record.py move_fast

Controls:
    Space - Start/Stop recording
    C     - Calibrate (collect gravity offset)
    Q     - Quit

Output: data/<testname>_<timestamp>.csv
"""

import curses
import os
import socket
import sys
import time
from datetime import datetime

import numpy as np

# Import from core module
try:
    from core import BIOGUI_HOST, BIOGUI_PORT, PACKET_SIZE, US_BYTES, recv_exact
except ModuleNotFoundError:
    # If running from imu/ directory, add parent to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core import BIOGUI_HOST, BIOGUI_PORT, PACKET_SIZE, US_BYTES, recv_exact

# Use core config values
HOST = BIOGUI_HOST
PORT = BIOGUI_PORT
SAMPLE_RATE = 40  # Hz


class IMURecorder:
    def __init__(self, filename):
        self.filename = filename
        self.recording = False
        self.samples = []
        self.timestamps = []
        self.start_time = None

        self.gravity = np.array([0.0, 0.0, 0.0])
        self.calibrated = False
        self.cal_samples = []

        self.raw_to_ms2 = 9.81 / 17327.0

    def start_calibration(self):
        self.cal_samples = []

    def add_calibration_sample(self, raw):
        self.cal_samples.append(raw.astype(float))

    def finish_calibration(self):
        if len(self.cal_samples) < 30:
            return False
        samples = np.array(self.cal_samples)
        self.gravity = np.mean(samples, axis=0)
        self.calibrated = True
        return True

    def start_recording(self):
        self.samples = []
        self.timestamps = []
        self.start_time = time.time()
        self.recording = True

    def stop_recording(self):
        self.recording = False

    def add_sample(self, raw_imu):
        if self.recording:
            timestamp = time.time() - self.start_time
            self.timestamps.append(timestamp)

            if self.calibrated:
                accel = (raw_imu.astype(float) - self.gravity) * self.raw_to_ms2
            else:
                accel = raw_imu.astype(float) * self.raw_to_ms2

            self.samples.append(accel)

    def save(self):
        if len(self.samples) == 0:
            return False

        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)
        filepath = os.path.join(data_dir, self.filename)

        with open(filepath, "w") as f:
            f.write("time,ax,ay,az\n")
            for t, sample in zip(self.timestamps, self.samples):
                f.write(f"{t:.6f},{sample[0]:.6f},{sample[1]:.6f},{sample[2]:.6f}\n")

        return True


def main(stdscr, testname):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(1)

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.clear()
    stdscr.addstr(0, 0, "Waiting for BioGUI connection...")
    stdscr.refresh()

    conn, addr = sock.accept()
    conn.settimeout(2.0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{testname}_{timestamp}.csv"
    recorder = IMURecorder(filename)

    packets_received = 0
    status = "Ready"
    calibrating = False

    while True:
        try:
            packet = recv_exact(conn, PACKET_SIZE)
            imu = np.frombuffer(packet[US_BYTES:], dtype=np.int16)

            if calibrating:
                recorder.add_calibration_sample(imu)
            else:
                recorder.add_sample(imu)

            packets_received += 1

        except socket.timeout:
            pass
        except ConnectionError:
            status = "Connection lost"

        if calibrating and len(recorder.cal_samples) >= 60:
            if recorder.finish_calibration():
                status = "Calibrated"
            else:
                status = "Calibration failed"
            calibrating = False

        ch = stdscr.getch()
        if ch != -1:
            if ch in (ord("q"), ord("Q"), 27):
                break

            elif ch in (ord("c"), ord("C")):
                recorder.start_calibration()
                calibrating = True
                status = "Calibrating... keep still"

            elif ch == ord(" "):
                if recorder.recording:
                    recorder.stop_recording()
                    if recorder.save():
                        status = f"Saved {filename} ({len(recorder.samples)} samples)"
                    else:
                        status = "Save failed"
                else:
                    recorder.start_recording()
                    status = "RECORDING"

        stdscr.clear()
        stdscr.addstr(0, 0, "IMU Data Recorder")
        stdscr.addstr(1, 0, f"Test: {testname}")
        stdscr.addstr(2, 0, f"File: {filename}")
        stdscr.addstr(4, 0, "Space: Start/Stop recording")
        stdscr.addstr(5, 0, "C: Calibrate")
        stdscr.addstr(6, 0, "Q: Quit")
        stdscr.addstr(8, 0, f"Connected: {addr}")
        stdscr.addstr(9, 0, f"Packets: {packets_received}")

        if calibrating:
            pct = len(recorder.cal_samples) * 100 // 60
            stdscr.addstr(11, 0, f"CALIBRATING: {pct}%")
        else:
            cal_status = "YES" if recorder.calibrated else "NO (press C)"
            stdscr.addstr(11, 0, f"Calibrated: {cal_status}")

        if recorder.recording:
            duration = len(recorder.samples) / SAMPLE_RATE
            stdscr.addstr(
                13,
                0,
                f">>> RECORDING: {len(recorder.samples)} samples ({duration:.1f}s)",
                curses.A_BOLD,
            )
        else:
            stdscr.addstr(13, 0, "Ready to record (press Space)")

        stdscr.addstr(15, 0, f"Status: {status}")
        stdscr.refresh()
        time.sleep(0.02)

    conn.close()
    sock.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python record.py <testname>")
        print("\nExamples:")
        print("  python record.py rest")
        print("  python record.py move_slow")
        print("  python record.py move_medium")
        print("  python record.py move_fast")
        sys.exit(1)

    testname = sys.argv[1]
    curses.wrapper(main, testname)
