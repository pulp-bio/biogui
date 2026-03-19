# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Prediction Monitor - Prints predictions from BioGUI data to terminal.

Usage:
    python -m apps.prediction_monitor                    # 7-class (default)
    python -m apps.prediction_monitor --model base       # 4-class
    python -m apps.prediction_monitor --smoothing 5      # Majority voting
    python -m apps.prediction_monitor --position         # Show position too
"""

import argparse
import socket
import sys
from collections import Counter
from pathlib import Path

from core import (
    BIOGUI_HOST,
    BIOGUI_PORT,
    PREDICTION_SMOOTHING,
    WULPUS_PACKET_FORMAT,
    decode_packet,
    recv_exact,
)
from gesture import GesturePredictor, USDataBuffer

MODEL_DIR = Path(__file__).parent.parent / "nn" / "models"
NUM_TRANSDUCERS = 6

MODELS = {
    "7class": {
        "pose_path": MODEL_DIR / "fold_1_pose_model_ft_1_3rep.pth",
        "pose_meta_path": MODEL_DIR / "additional_info_pose.json",
        "pose_classes": 7,
        "pose_map": {
            0: "rest",
            1: "open",
            2: "rotopen",
            3: "close",
            4: "rotclosed",
            5: "pinch",
            6: "pour",
        },
        #
        "position_path": MODEL_DIR / "fold_1_position_model_ft_1_3rep.pth",
        "position_meta_path": MODEL_DIR / "additional_info_position.json",
        "position_classes": 3,
        "position_map": {0: "start", 1: "forward", 2: "right"},
    },
    "3class": {
        "pose_path": MODEL_DIR / "3class" / "fold_1_pose_model.pth",
        "pose_meta_path": MODEL_DIR / "additional_info_pose.json",
        "pose_classes": 3,
        "pose_map": {0: "rest", 1: "open", 2: "close"},
        #
        "position_path": MODEL_DIR / "3class" / "fold_1_position_model.pth",
        "position_meta_path": MODEL_DIR / "additional_info_position.json",
        "position_classes": 3,
        "position_map": {0: "start", 1: "forward", 2: "right"},
    },
}


class Smoother:
    """Majority voting over a sliding window."""

    def __init__(self, window: int):
        self.window = window
        self.history: list[int] = []

    def add(self, value: int) -> int:
        self.history.append(value)
        if len(self.history) > self.window:
            self.history.pop(0)
        return Counter(self.history).most_common(1)[0][0]


def receive_packets(conn, us_buffer, pose_model, position_model, smoothing, config):
    """Process packets and print predictions."""
    packet_size = WULPUS_PACKET_FORMAT.packet_size
    pose_smoother = Smoother(smoothing)
    pos_smoother = Smoother(smoothing)

    while True:
        data = recv_exact(conn, packet_size)
        if not data:
            break

        packet = decode_packet(data)
        config_id = int(packet["tx_rx_id"][0])

        if config_id < NUM_TRANSDUCERS:
            us_buffer.add_sample_to_channel(packet["ultrasound"], config_id)

        if not us_buffer.is_ready():
            continue

        us_array = us_buffer.get_data()

        # Pose
        pose_idx, pose_name, pose_probs = pose_model.predict(us_array)
        pose_conf = pose_probs[pose_idx] * 100
        smoothed_pose = config["pose_map"].get(pose_smoother.add(pose_idx), "?")

        # Position (optional)
        pos_str = ""
        if position_model:
            pos_idx, pos_name, pos_probs = position_model.predict(us_array)
            pos_conf = pos_probs[pos_idx] * 100
            smoothed_pos = config["position_map"].get(pos_smoother.add(pos_idx), "?")
            pos_str = f"  |  Pos: {smoothed_pos:<12} (raw: {pos_name:<10} {pos_conf:5.1f}%)"

        print(f"Pose: {smoothed_pose:<12} (raw: {pose_name:<10} {pose_conf:5.1f}%){pos_str}")


def main():
    parser = argparse.ArgumentParser(description="Monitor predictions from BioGUI")
    parser.add_argument("--model", default="7class")
    parser.add_argument("--smoothing", type=int, default=PREDICTION_SMOOTHING)
    parser.add_argument("--position", action="store_true")
    args = parser.parse_args()

    config = MODELS[args.model]

    print(f"\n{'=' * 50}")
    print(f"Model: {args.model} | Smoothing: {args.smoothing}")
    print(f"{'=' * 50}\n")

    # Load models
    try:
        pose_model = GesturePredictor(
            config["pose_path"],
            json_meta_path=config["pose_meta_path"],
            num_transducers=NUM_TRANSDUCERS,
            num_classes=config["pose_classes"],
            class_map=config["pose_map"],
        )
        position_model = None
        if args.position:
            position_model = GesturePredictor(
                config["position_path"],
                json_meta_path=config["position_meta_path"],
                num_transducers=NUM_TRANSDUCERS,
                num_classes=config["position_classes"],
                class_map=config["position_map"],
            )
        print("Models loaded.\n")
    except Exception as e:
        sys.exit(f"Failed to load models: {e}")

    us_buffer = USDataBuffer(num_channels=NUM_TRANSDUCERS)

    print(f"Listening on {BIOGUI_HOST}:{BIOGUI_PORT}... (Ctrl+C to stop)\n")

    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((BIOGUI_HOST, BIOGUI_PORT))
                server.listen(1)

                conn, addr = server.accept()
                print(f"Connected: {addr}\n{'-' * 50}")

                with conn:
                    receive_packets(
                        conn,
                        us_buffer,
                        pose_model,
                        position_model,
                        args.smoothing,
                        config,
                    )

                print(f"{'-' * 50}\nDisconnected.\n")

        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
