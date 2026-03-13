"""
Unity controller for hand visualization.

Provides a unified UnityController class for sending hand control
commands to Unity via UDP.

Protocol (JSON over UDP):
{
    "positionDelta": [0.0, 0.0, 0.0],   // Delta position (dx, dy, dz)
    "positionState": "forward",          // Label: "start", "forward", "right"
    "gesture": "close",                  // Label: "rest", "open", "close", "pinch"
    "rotation": [0, 0, 90],              // Absolute: [flexion, unused, supination] (IMU-based)
    "curls": [1, 1, 1, 1, 1]             // Absolute: [thumb, index, middle, ring, pinky]
}

Unity uses:
- Position: positionDelta (continuous) OR positionState (discrete)
- Rotation: IMU-based only (continuous)
"""

import json
import socket
import threading
from collections import deque

from core import (
    DEFAULT_HAND_ROTATION,
    PREDICTION_SMOOTHING,
    UNITY_HOST,
    UNITY_PORT,
    Mode,
)


class UnityController:
    """
    Controller for sending hand state to Unity.

    Sends both delta positions AND position state labels.
    Unity decides which to use based on the task type.

    Parameters
    ----------
    host : str
        Unity host address.
    port : int
        Unity UDP port.
    smoothing : int
        Number of predictions to average for stability.
    thread_safe : bool
        If True, state updates are protected by a lock.

    Attributes
    ----------
    position_delta : list[float]
        Position delta [dx, dy, dz] to add to current position.
    position_state : str
        Position state label: "start", "forward", "right".
    gesture : str
        Gesture label: "rest", "open", "close", "pinch".
    rotation : list[float]
        Absolute rotation [flexion, unused, supination] in degrees (IMU-based).
    curls : list[float]
        Absolute finger curls [thumb, index, middle, ring, pinky] (0-1).
    """

    # Valid position states
    POSITION_STATES = ("start", "forward", "right")

    # Valid gestures (4 classes sent to Unity)
    GESTURES = ("rest", "open", "close", "pinch")

    def __init__(
        self,
        host: str = UNITY_HOST,
        port: int = UNITY_PORT,
        smoothing: int = PREDICTION_SMOOTHING,
        thread_safe: bool = True,
    ):
        self.host = host
        self.port = port
        self.smoothing = smoothing

        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Hand state
        self.position_delta = [0.0, 0.0, 0.0]  # dx, dy, dz
        self.position_state = "start"  # "start", "forward", "right"
        self.gesture = "rest"  # "rest", "open", "close", "pinch"
        self.rotation = list(DEFAULT_HAND_ROTATION)  # [flex, unused, supin] (IMU-based)
        self.curls = [0.0, 0.0, 0.0, 0.0, 0.0]  # [thumb, index, middle, ring, pinky]

        self.mode = Mode.CLASSIFICATION

        # Prediction smoothing
        self.prediction_history = deque(maxlen=smoothing)
        self.last_confidence = 0.0

        # Thread safety
        self._lock = threading.Lock() if thread_safe else _DummyLock()

    # =========================================================================
    # Position Delta (for continuous movement)
    # =========================================================================

    def set_position_delta(self, dx: float, dy: float, dz: float):
        """
        Set position delta to send.

        Parameters
        ----------
        dx, dy, dz : float
            Position delta values.
        """
        with self._lock:
            self.position_delta = [dx, dy, dz]

    def clear_position_delta(self):
        """Clear position delta (set to zero)."""
        with self._lock:
            self.position_delta = [0.0, 0.0, 0.0]

    # =========================================================================
    # Position State (for discrete movement)
    # =========================================================================

    def set_position_state(self, state: str):
        """
        Set position state label.

        Parameters
        ----------
        state : str
            One of: "start", "forward", "right"
        """
        state = state.lower()
        if state not in self.POSITION_STATES:
            raise ValueError(
                f"Invalid position state: {state}. "
                f"Must be one of: {self.POSITION_STATES}"
            )
        with self._lock:
            self.position_state = state

    def move_start(self):
        """Set position state to 'start'."""
        self.set_position_state("start")

    def move_forward(self):
        """Set position state to 'forward'."""
        self.set_position_state("forward")

    def move_right(self):
        """Set position state to 'right'."""
        self.set_position_state("right")

    # =========================================================================
    # Gesture (label as text)
    # =========================================================================

    def set_gesture(self, gesture: str):
        """
        Set gesture label.

        Parameters
        ----------
        gesture : str
            One of: "rest", "open", "close", "pinch"
        """
        gesture = gesture.lower()
        if gesture not in self.GESTURES:
            raise ValueError(
                f"Invalid gesture: {gesture}. Must be one of: {self.GESTURES}"
            )
        with self._lock:
            self.gesture = gesture

            # Also update curls to match gesture
            if gesture == "open":
                self.curls = [0.0, 0.0, 0.0, 0.0, 0.0]
            elif gesture == "close":
                self.curls = [1.0, 1.0, 1.0, 1.0, 1.0]
            elif gesture == "pinch":
                self.curls = [0.8, 0.8, 0.14, 0.12, 0.10]
            elif gesture == "rest":
                self.curls = [0.12, 0.12, 0.12, 0.12, 0.12]

    # =========================================================================
    # Rotation (IMU-based)
    # =========================================================================

    def set_rotation(self, flexion: float, unused: float, supination: float):
        """
        Set absolute hand rotation (IMU-based).

        Parameters
        ----------
        flexion : float
            Flexion/extension angle in degrees.
        unused : float
            Unused (set to 0).
        supination : float
            Supination angle in degrees.
        """
        with self._lock:
            self.rotation = [flexion, unused, supination]

    def set_supination(self, degrees: float):
        """Set supination angle in degrees (IMU-based)."""
        with self._lock:
            self.rotation[2] = degrees

    def set_flexion(self, degrees: float):
        """Set flexion/extension angle in degrees (IMU-based)."""
        with self._lock:
            self.rotation[0] = degrees

    # =========================================================================
    # Curls (absolute)
    # =========================================================================

    def set_curls(self, curls: list[float]):
        """
        Set absolute finger curl values.

        Parameters
        ----------
        curls : list[float]
            Curl values for [thumb, index, middle, ring, pinky] (0-1).
        """
        with self._lock:
            if len(curls) != 5:
                raise ValueError(f"Expected 5 curl values, got {len(curls)}")
            self.curls = [max(0.0, min(1.0, c)) for c in curls]

    # =========================================================================
    # Legacy compatibility
    # =========================================================================

    def update_gesture(self, prediction: int, confidence: float = 1.0):
        """
        Update gesture based on NN prediction with smoothing.

        Parameters
        ----------
        prediction : int
            Predicted gesture class (0=Fist, 1=Open)
        confidence : float
            Prediction confidence.
        """
        with self._lock:
            self.prediction_history.append(prediction)

            if len(self.prediction_history) < self.smoothing:
                return

            avg_prediction = sum(self.prediction_history) / len(self.prediction_history)

            if avg_prediction > 0.5:
                self.gesture = "open"
                self.curls = [0.0, 0.0, 0.0, 0.0, 0.0]
            else:
                self.gesture = "fist"
                self.curls = [1.0, 1.0, 1.0, 1.0, 1.0]

            self.last_confidence = confidence

    # =========================================================================
    # Network
    # =========================================================================

    def send(self):
        """
        Send current state to Unity.

        Sends JSON with:
        - positionDelta: [dx, dy, dz]
        - positionState: "start" | "forward" | "right"
        - gesture: "rest" | "open" | "close" | "pinch"
        - rotation: [flex, unused, supin] (IMU-based)
        - curls: [t, i, m, r, p]
        """
        with self._lock:
            msg = {
                "positionDelta": self.position_delta,
                "positionState": self.position_state,
                "gesture": self.gesture,
                "rotation": self.rotation,
                "curls": self.curls,
            }
        json_data = json.dumps(msg).encode("utf-8")
        self.sock.sendto(json_data, (self.host, self.port))

    def get_state(self) -> dict:
        """Get current state for display or debugging."""
        with self._lock:
            return {
                "position_delta": self.position_delta.copy(),
                "position_state": self.position_state,
                "gesture": self.gesture,
                "rotation": self.rotation.copy(),
                "curls": self.curls.copy(),
                "mode": self.mode,
                "confidence": self.last_confidence,
            }

    # =========================================================================
    # Reset
    # =========================================================================

    def reset_rotation(self):
        """Reset rotation to default (0, 0, 0)."""
        with self._lock:
            self.rotation = list(DEFAULT_HAND_ROTATION)

    def reset(self):
        """Reset all state to defaults."""
        with self._lock:
            self.position_delta = [0.0, 0.0, 0.0]
            self.position_state = "start"
            self.gesture = "rest"
            self.rotation = list(DEFAULT_HAND_ROTATION)
            self.curls = [0.0, 0.0, 0.0, 0.0, 0.0]
            self.mode = Mode.CLASSIFICATION
            self.prediction_history.clear()
            self.last_confidence = 0.0

    def close(self):
        """Close the UDP socket."""
        self.sock.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __repr__(self) -> str:
        return (
            f"UnityController("
            f"state='{self.position_state}', "
            f"gesture='{self.gesture}', "
            f"supin={self.rotation[2]:.0f}°)"
        )


class _DummyLock:
    """Dummy context manager for non-thread-safe mode."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
