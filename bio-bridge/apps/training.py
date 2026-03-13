"""
Online Training for Gesture Recognition
========================================

Collects labeled data from Unity triggers and trains NN model.

INPUT:  BioGUI TCP (Ultrasound data) + Unity UDP triggers (gesture labels)
OUTPUT: Trained model saved to nn/models/
TERMINAL: Training progress, sample counts, loss curves

Use Case:
- Train gesture recognition model with live data
- Unity sends gesture labels, BioGUI sends ultrasound data
- Automatically trains when enough samples collected

Workflow:
1. Start this script
2. Connect BioGUI
3. In Unity: trigger gestures (fist/open) during calibration phase
4. Script collects labeled samples
5. Sends "finish" → trains and saves model

Usage:
    python -m apps.training
"""

import json
import socket
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

from core import (
    BIOGUI_HOST,
    BIOGUI_PORT,
    DEFAULT_BATCH_SIZE,
    DEFAULT_EPOCHS,
    GESTURE_TO_LABEL,
    MODEL_DIR,
    NUM_CLASSES,
    NUM_US_CHANNELS,
    SKIP_PACKETS_AFTER_CHANGE,
    TARGET_SAMPLES_PER_CLASS,
    UNITY_TRIGGER_HOST,
    US_WINDOW_SIZE,
    WULPUS_PACKET_FORMAT,
    decode_packet,
    recv_exact,
)
from nn.train_utils import test_model, train_loop
from nn.architectures.us_simple_cnn import US_Simple_Class, encoder_blocks_us

# Unity training port (must match MiddlewareClient.cs)
UNITY_TRAINING_PORT = 6000


class TrainingState:
    """Shared state for training workflow."""

    WAITING_FOR_BIOGUI = "waiting_biogui"
    WAITING_FOR_UNITY = "waiting_unity"
    COLLECTING = "collecting"
    TRAINING = "training"
    FINISHED = "finished"


class Buffer:
    """
    Thread-safe buffer for ultrasound data collection.

    Collects labeled samples from BioGUI based on Unity trigger commands.
    Uses absolute Unix timestamps and duration to handle packet loss gracefully.
    """

    def __init__(
        self, window_size: int = US_WINDOW_SIZE, num_channels: int = NUM_US_CHANNELS
    ):
        self.window_size = window_size
        self.num_channels = num_channels

        # Circular buffers for each channel
        self.us_buffers = [deque(maxlen=window_size) for _ in range(num_channels)]

        # Current gesture state with timing (absolute Unix timestamps in ms)
        self.current_gesture = "rest"
        self.previous_gesture = "rest"
        self.gesture_start_time_ms = 0  # Absolute Unix timestamp from Unity (ms)
        self.gesture_duration_ms = 0  # Duration from Unity (ms)

        # Transition tracking (skip packets after gesture change)
        self.packets_since_change = 0
        self.in_transition = False

        # Collected training samples
        self.training_samples = []

        # Statistics
        self.stats = {
            "total_packets": 0,
            "samples_collected": {0: 0, 1: 0, 2: 0},
            "samples_skipped_no_gesture": 0,
            "samples_skipped_rest": 0,
            "samples_skipped_expired": 0,
            "samples_skipped_transition": 0,
            "gesture_changes": 0,
        }

        self.lock = threading.Lock()
        self.collecting = False

    def start_collecting(self):
        """Start collecting samples."""
        with self.lock:
            self.collecting = True
            print("[Buffer] Collection started")

    def stop_collecting(self):
        """Stop collecting samples."""
        with self.lock:
            self.collecting = False
            print("[Buffer] Collection stopped")

    def update_trigger(self, gesture: str, timestamp_ms: int, duration_ms: int):
        """Update current gesture from Unity trigger with absolute Unix timestamp and duration."""
        with self.lock:
            # Check if gesture actually changed
            if gesture != self.current_gesture:
                self.previous_gesture = self.current_gesture
                self.current_gesture = gesture
                self.packets_since_change = 0

                if gesture in ["fist", "open"]:
                    self.in_transition = True
                    self.stats["gesture_changes"] += 1
                    print(
                        f"[Buffer] Gesture: {self.previous_gesture} → {gesture} "
                        f"(t={timestamp_ms}ms, dur={duration_ms}ms)"
                    )
                else:
                    self.in_transition = False
                    print(
                        f"[Buffer] Gesture: {gesture} "
                        f"(t={timestamp_ms}ms, dur={duration_ms}ms)"
                    )
            else:
                # Same gesture, just update timing (in case of packet retransmission)
                self.gesture_start_time_ms = timestamp_ms
                self.gesture_duration_ms = duration_ms

            # Always update timing info
            self.gesture_start_time_ms = timestamp_ms
            self.gesture_duration_ms = duration_ms

    def add_us_sample(self, us_data: np.ndarray, channel_id: int):
        """Add ultrasound sample to buffer."""
        with self.lock:
            if not self.collecting:
                return

            # Add samples to channel buffer
            for sample in us_data:
                self.us_buffers[channel_id].append(sample)

            self.stats["total_packets"] += 1
            self.packets_since_change += 1

            # Only create sample when channel 0 completes (full cycle)
            if channel_id != 0:
                return

            # Check if all buffers are full
            if not all(len(buf) == self.window_size for buf in self.us_buffers):
                return

            self._try_create_sample()

    def _try_create_sample(self):
        """Try to create a training sample from current buffer state."""
        # Get current absolute Unix timestamp (ms)
        current_time_ms = int(time.time() * 1000)

        # Check if we have a valid gesture with timing info
        if self.gesture_duration_ms == 0:
            # No valid gesture packet received yet
            self.stats["samples_skipped_no_gesture"] += 1
            return

        # Skip transition period after gesture change (user needs time to switch)
        if self.in_transition:
            if self.packets_since_change < SKIP_PACKETS_AFTER_CHANGE:
                self.stats["samples_skipped_transition"] += 1
                return
            else:
                self.in_transition = False
                print(f"[Buffer] Transition complete for '{self.current_gesture}'")

        # Check if current gesture has expired (based on absolute timestamp + duration)
        gesture_end_time_ms = self.gesture_start_time_ms + self.gesture_duration_ms
        if current_time_ms > gesture_end_time_ms:
            # Gesture period has expired, ignore this sample
            self.stats["samples_skipped_expired"] += 1
            return

        # Skip rest gestures
        if self.current_gesture == "rest":
            self.stats["samples_skipped_rest"] += 1
            return

        # Create sample
        us_data = np.array([list(buf) for buf in self.us_buffers], dtype=np.float32)
        label = GESTURE_TO_LABEL.get(self.current_gesture, 0)

        self.training_samples.append(
            {
                "us_data": us_data,
                "label": label,
                "gesture": self.current_gesture,
            }
        )
        self.stats["samples_collected"][label] += 1

        # Progress update
        total = sum(self.stats["samples_collected"].values())
        if total % 10 == 0:
            print(
                f"[Buffer] Samples: fist={self.stats['samples_collected'][1]}, "
                f"open={self.stats['samples_collected'][2]} (total={total})"
            )

    def get_training_data(self):
        """Get collected training data as numpy arrays."""
        with self.lock:
            if not self.training_samples:
                return None, None

            X = np.stack([s["us_data"] for s in self.training_samples])
            y = np.array([s["label"] for s in self.training_samples])

            return X, y

    def get_stats(self):
        """Get current statistics."""
        with self.lock:
            return self.stats.copy()

    def get_sample_counts(self):
        """Get sample counts per class."""
        with self.lock:
            return self.stats["samples_collected"].copy()


def biogui_receiver_thread(buffer: Buffer, state: dict):
    """Thread that receives ultrasound data from BioGUI."""
    packet_size = WULPUS_PACKET_FORMAT.packet_size

    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((BIOGUI_HOST, BIOGUI_PORT))
        srv.listen(1)

        print(f"[BioGUI] Waiting for connection on {BIOGUI_HOST}:{BIOGUI_PORT}...")

        conn, addr = srv.accept()
        print(f"[BioGUI] Connected: {addr}")
        state["biogui_connected"] = True

        conn.settimeout(0.5)

        while state["active"]:
            try:
                packet = recv_exact(conn, packet_size)
                decoded = decode_packet(packet)

                tx_rx_id = int(decoded["tx_rx_id"][0])
                us = decoded["ultrasound"]

                buffer.add_us_sample(us, tx_rx_id)

            except socket.timeout:
                continue
            except ConnectionError:
                print("[BioGUI] Connection lost")
                break
            except Exception as e:
                print(f"[BioGUI] Error: {e}")
                break

        conn.close()
        srv.close()

    except Exception as e:
        print(f"[BioGUI] Fatal error: {e}")
        state["error"] = str(e)

    state["biogui_connected"] = False
    print("[BioGUI] Thread terminated")


def unity_trigger_receiver_thread(buffer: Buffer, state: dict):
    """
    Thread that receives gesture triggers from Unity.

    Expected messages (matching MiddlewareClient.cs):
    - {"gesture": "fist", "timestamp": <unix_ms>, "duration": 5000} - switch to fist gesture
    - {"gesture": "open", "timestamp": <unix_ms>, "duration": 5000} - switch to open gesture
    - {"gesture": "rest", "timestamp": <unix_ms>, "duration": 3000} - switch to rest (not collected)
    - {"action": "finish"} - stop collection and start training

    Note: timestamp is an absolute Unix timestamp in milliseconds (from DateTimeOffset.UtcNow).
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((UNITY_TRIGGER_HOST, UNITY_TRAINING_PORT))
        sock.settimeout(0.5)

        print(f"[Unity] Listening on {UNITY_TRIGGER_HOST}:{UNITY_TRAINING_PORT}...")
        state["unity_listening"] = True

        while state["active"]:
            try:
                data, addr = sock.recvfrom(1024)
                msg = json.loads(data.decode("utf-8"))

                # Check for finish command ({"action": "finish"})
                if msg.get("action", "").lower() == "finish":
                    print("[Unity] Received FINISH command")
                    state["finish_requested"] = True
                    continue

                # Handle gesture trigger with timestamp and duration
                gesture = msg.get("gesture", "").lower()
                if gesture in ["fist", "open", "rest"]:
                    timestamp_ms = msg.get("timestamp", 0)
                    duration_ms = msg.get("duration", 0)

                    if timestamp_ms == 0 or duration_ms == 0:
                        print(
                            "[Unity] Warning: Invalid gesture message (missing timestamp/duration)"
                        )
                        continue

                    buffer.update_trigger(gesture, timestamp_ms, duration_ms)

                    # First non-rest trigger starts collection
                    if gesture in ["fist", "open"] and not state["collection_started"]:
                        print(f"[Unity] First trigger received: {gesture}")
                        state["collection_started"] = True
                        buffer.start_collecting()

            except socket.timeout:
                continue
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"[Unity] Error: {e}")
                continue

        sock.close()

    except Exception as e:
        print(f"[Unity] Fatal error: {e}")
        state["error"] = str(e)

    state["unity_listening"] = False
    print("[Unity] Thread terminated")


class OnlineTrainer:
    """Handles neural network training on collected data."""

    def __init__(self):
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = DEFAULT_EPOCHS):
        """Train model on collected data."""
        print("\n" + "=" * 70)
        print("Training Neural Network")
        print("=" * 70)
        print(f"Device: {self.device}")
        print(f"Data shape: X={X.shape}, y={y.shape}")
        print(f"Epochs: {epochs}")

        # Convert labels: 1,2 → 0,1 for 2-class model
        y_model = y - 1

        # Split train/val (80/20)
        from sklearn.model_selection import train_test_split

        X_train, X_val, y_train, y_val = train_test_split(
            X, y_model, test_size=0.2, random_state=42, stratify=y_model
        )

        print(f"Train: {len(X_train)}, Val: {len(X_val)}")

        # Create dataloaders
        from torch.utils.data import DataLoader, TensorDataset

        train_dataset = TensorDataset(
            torch.from_numpy(X_train).float(), torch.from_numpy(y_train).long()
        )
        val_dataset = TensorDataset(
            torch.from_numpy(X_val).float(), torch.from_numpy(y_val).long()
        )

        train_loader = DataLoader(
            train_dataset, batch_size=DEFAULT_BATCH_SIZE, shuffle=True
        )
        val_loader = DataLoader(
            val_dataset, batch_size=DEFAULT_BATCH_SIZE, shuffle=False
        )

        # Initialize model
        self.model = US_Simple_Class(
            encoder_blocks_us=encoder_blocks_us, num_classes=NUM_CLASSES
        ).to(self.device)

        # Train
        print("\nTraining...")
        self.model = train_loop(
            self.model, train_loader, val_loader, num_epochs=epochs, device=self.device
        )

        # Test
        print("\nEvaluating...")
        metrics, _, _, _ = test_model(self.model, val_loader, device=self.device)

        return metrics

    def save_model(self, path: Path):
        """Save model to disk."""
        if self.model is None:
            raise ValueError("No model to save")

        path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "num_classes": NUM_CLASSES,
            "timestamp": datetime.now().isoformat(),
        }

        torch.save(checkpoint, path)
        print(f"Model saved: {path}")

        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.parent / f"model_{timestamp}.pt"
        torch.save(checkpoint, backup_path)
        print(f"Backup saved: {backup_path}")


def main():
    print("=" * 70)
    print("Online Gesture Recognition Training")
    print("=" * 70)
    print(f"BioGUI: {BIOGUI_HOST}:{BIOGUI_PORT}")
    print(f"Unity:  {UNITY_TRIGGER_HOST}:{UNITY_TRAINING_PORT}")
    print(f"Target: {TARGET_SAMPLES_PER_CLASS} samples per class")
    print("=" * 70)
    print()
    print("Workflow:")
    print("  1. Connect BioGUI (TCP)")
    print("  2. Wait for first gesture trigger from Unity")
    print("  3. Collect samples (fist/open)")
    print('  4. Unity sends {"action": "finish"} to start training')
    print("=" * 70)
    print()

    # Initialize
    buffer = Buffer()
    state = {
        "active": True,
        "biogui_connected": False,
        "unity_listening": False,
        "collection_started": False,
        "finish_requested": False,
        "error": None,
    }

    # Start BioGUI thread
    biogui_thread = threading.Thread(
        target=biogui_receiver_thread, args=(buffer, state), daemon=True
    )
    biogui_thread.start()

    # Wait for BioGUI connection
    print("Waiting for BioGUI connection...")
    while state["active"] and not state["biogui_connected"]:
        time.sleep(0.5)

    if not state["active"]:
        return

    print()
    print("BioGUI connected. Waiting for Unity trigger to start collection...")
    print("(Send a 'fist' or 'open' gesture trigger from Unity)")
    print()

    # Start Unity thread
    unity_thread = threading.Thread(
        target=unity_trigger_receiver_thread, args=(buffer, state), daemon=True
    )
    unity_thread.start()

    # Main loop - wait for collection to start, then wait for finish
    try:
        # Wait for first trigger
        while state["active"] and not state["collection_started"]:
            if not state["biogui_connected"]:
                print("\nBioGUI disconnected!")
                state["active"] = False
                break
            time.sleep(0.5)

        if not state["active"]:
            return

        print()
        print("=" * 70)
        print("Collection started! Perform gestures now.")
        print('Send {"action": "finish"} from Unity when done.')
        print("=" * 70)
        print()

        # Collection loop
        last_print = time.time()
        while state["active"] and not state["finish_requested"]:
            if not state["biogui_connected"]:
                print("\nBioGUI disconnected!")
                break

            # Print status every 2 seconds
            if time.time() - last_print > 2.0:
                counts = buffer.get_sample_counts()
                stats = buffer.get_stats()
                print(
                    f"Samples: fist={counts[1]:3d}, open={counts[2]:3d}  |  "
                    f"Packets: {stats['total_packets']}"
                )
                last_print = time.time()

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")

    # Stop collection
    state["active"] = False
    buffer.stop_collecting()

    # Wait for threads
    biogui_thread.join(timeout=2.0)
    unity_thread.join(timeout=2.0)

    # Get collected data
    X, y = buffer.get_training_data()

    if X is None or len(X) == 0:
        print("\nNo samples collected. Exiting.")
        return

    # Print summary
    stats = buffer.get_stats()
    print()
    print("=" * 70)
    print("Collection Summary")
    print("=" * 70)
    print(f"Total packets: {stats['total_packets']}")
    print(f"Fist samples: {stats['samples_collected'][1]}")
    print(f"Open samples: {stats['samples_collected'][2]}")
    print(f"Skipped (no gesture): {stats['samples_skipped_no_gesture']}")
    print(f"Skipped (transition): {stats['samples_skipped_transition']}")
    print(f"Skipped (rest): {stats['samples_skipped_rest']}")
    print(f"Skipped (expired): {stats['samples_skipped_expired']}")
    print("=" * 70)

    # Train
    trainer = OnlineTrainer()
    try:
        metrics = trainer.train(X, y)

        # Save model
        model_path = MODEL_DIR / "model_0.pt"
        trainer.save_model(model_path)

        print()
        print("=" * 70)
        print("Training Complete!")
        print("=" * 70)
        print(f"Accuracy: {metrics['accuracy']:.2%}")
        print(f"Model: {model_path}")
        print("=" * 70)

    except Exception as e:
        print(f"\nTraining error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
