"""
IMU Position Tracker for velocity-based position tracking.

Provides a PositionTracker class that uses acceleration data from the IMU
to estimate position through double integration with drift compensation.

Uses a state machine approach:
- STATIONARY: Wait for acceleration above start_threshold to begin moving
- MOVING: Track movement direction, use velocity decay as friction

Features:
- Hysteresis thresholds to prevent jitter
- Velocity decay to prevent runaway drift
- Zero-velocity update (ZUPT) when stationary
- Configurable calibration for gravity offset removal
"""

import numpy as np

from core import (
    CALIBRATION_SAMPLES,
    DEFAULT_POSITION_SCALE,
    DEFAULT_START_THRESHOLD,
    DEFAULT_STOP_THRESHOLD,
    DEFAULT_VELOCITY_DECAY,
    MEAS_PERIOD,
)

# Default hand position for IMU tracking (Unity world coordinates)
DEFAULT_HAND_POSITION = [0.0, 0.0, 0.0]


class MovementState:
    """Movement state machine states."""

    STATIONARY = 0
    MOVING = 1


class PositionTracker:
    """
    Velocity-based IMU position tracker with direction tracking.

    Uses a state machine approach with hysteresis to robustly track
    position from noisy IMU acceleration data.

    Parameters
    ----------
    start_threshold : float, optional
        Acceleration magnitude threshold to start moving (m/s²).
        Defaults to DEFAULT_START_THRESHOLD.
    stop_threshold : float, optional
        Acceleration magnitude threshold to stop moving (m/s²).
        Should be less than start_threshold for hysteresis.
        Defaults to DEFAULT_STOP_THRESHOLD.
    scale : float, optional
        Position scale factor for Unity coordinates.
        Defaults to DEFAULT_POSITION_SCALE.
    velocity_decay : float, optional
        Per-sample velocity decay factor (0-1), acts like friction.
        Defaults to DEFAULT_VELOCITY_DECAY.
    dt : float, optional
        Time step between samples in seconds.
        Defaults to MEAS_PERIOD (1/30 Hz = 33.333ms).

    Attributes
    ----------
    position : np.ndarray
        Current position estimate [x, y, z] in meters
    velocity : np.ndarray
        Current velocity estimate [x, y, z] in m/s
    accel : np.ndarray
        Most recent acceleration reading [x, y, z] in m/s²
    state : int
        Current movement state (STATIONARY or MOVING)
    calibrated : bool
        Whether gravity offset calibration has been performed

    Examples
    --------
    >>> tracker = PositionTracker()
    >>> tracker.start_calibration()
    >>> for sample in calibration_samples:
    ...     tracker.add_calibration_sample(sample)
    >>> tracker.finish_calibration()
    >>> for imu_sample in live_samples:
    ...     tracker.update(imu_sample)
    ...     unity_pos = tracker.get_unity_position()
    """

    # Conversion factor from raw IMU units to m/s²
    RAW_TO_MS2 = 9.81 / 17327.0

    def __init__(
        self,
        start_threshold: float = DEFAULT_START_THRESHOLD,
        stop_threshold: float = DEFAULT_STOP_THRESHOLD,
        scale: float = DEFAULT_POSITION_SCALE,
        velocity_decay: float = DEFAULT_VELOCITY_DECAY,
        dt: float = MEAS_PERIOD,
    ):
        # Timing
        self.dt = dt

        # Calibration
        self.gravity = np.zeros(3)
        self.calibrated = False
        self.cal_samples = []
        self.noise_std = np.zeros(3)

        # State
        self.accel = np.zeros(3)
        self.velocity = np.zeros(3)
        self.position = np.zeros(3)

        # Movement state machine
        self.state = MovementState.STATIONARY
        self.movement_direction = np.zeros(3)
        self.stationary_count = 0
        self.stationary_samples_needed = 5  # ~125ms at 40Hz

        # Thresholds with hysteresis
        self.start_threshold = start_threshold
        self.stop_threshold = stop_threshold

        # Movement parameters
        self.scale = scale
        self.velocity_decay = velocity_decay

        # Unity base position
        self.base_pos = list(DEFAULT_HAND_POSITION)

    def start_calibration(self):
        """
        Start calibration process.

        Call this, then add_calibration_sample() repeatedly,
        then finish_calibration().
        """
        self.cal_samples = []

    def add_calibration_sample(self, raw: np.ndarray):
        """
        Add a calibration sample.

        Parameters
        ----------
        raw : np.ndarray
            Raw IMU reading [ax, ay, az] as int16 values
        """
        self.cal_samples.append(raw.astype(float))

    def finish_calibration(self) -> bool:
        """
        Finish calibration and compute gravity offset.

        Returns
        -------
        bool
            True if calibration succeeded (enough samples),
            False otherwise
        """
        if len(self.cal_samples) < CALIBRATION_SAMPLES:
            return False

        samples = np.array(self.cal_samples)
        self.gravity = np.mean(samples, axis=0)
        self.noise_std = np.std(samples, axis=0) * self.RAW_TO_MS2

        # Reset state
        self.velocity = np.zeros(3)
        self.position = np.zeros(3)
        self.state = MovementState.STATIONARY
        self.movement_direction = np.zeros(3)
        self.stationary_count = 0
        self.calibrated = True

        return True

    def update(self, raw_imu: np.ndarray):
        """
        Process new IMU sample and update position estimate.

        Parameters
        ----------
        raw_imu : np.ndarray
            Raw IMU reading [ax, ay, az] as int16 values
        """
        prev_accel = self.accel.copy()
        prev_velocity = self.velocity.copy()

        # Convert to m/s² and remove gravity
        if self.calibrated:
            self.accel = (raw_imu.astype(float) - self.gravity) * self.RAW_TO_MS2
        else:
            self.accel = raw_imu.astype(float) * self.RAW_TO_MS2

        accel_mag = np.linalg.norm(self.accel)

        # State machine update
        if self.state == MovementState.STATIONARY:
            self._update_stationary_trapezoidal(accel_mag, prev_accel)
        else:  # MOVING
            self._update_moving_trapezoidal(accel_mag, prev_accel, prev_velocity)

        # Apply velocity decay (like friction)
        self.velocity *= self.velocity_decay

        # Integrate velocity to position
        self.position += (prev_velocity + self.velocity) / 2.0 * self.dt

    def _update_stationary_trapezoidal(self, accel_mag: float, prev_accel: np.ndarray):
        """Handle STATIONARY state."""
        if accel_mag > self.start_threshold:
            # Start moving!
            self.state = MovementState.MOVING
            self.movement_direction = self.accel / accel_mag
            # Trapezoidal integration
            self.velocity = (prev_accel + self.accel) * self.dt / 2.0
            self.stationary_count = 0

    def _update_moving_trapezoidal(
        self, accel_mag: float, prev_accel: np.ndarray, prev_velocity: np.ndarray
    ):
        """Handle MOVING state."""
        if accel_mag < self.stop_threshold:
            # Might be stopping
            self.stationary_count += 1

            velocity_mag = np.linalg.norm(self.velocity)
            if (
                self.stationary_count > self.stationary_samples_needed
                and velocity_mag < 0.05
            ):
                # Confirmed stopped - apply ZUPT
                self.state = MovementState.STATIONARY
                self.velocity = np.zeros(3)
                self.movement_direction = np.zeros(3)
                return
        else:
            self.stationary_count = 0

        # Check if acceleration is in movement direction or opposite
        if accel_mag > 0.01:
            accel_unit = self.accel / accel_mag
            dot = np.dot(accel_unit, self.movement_direction)

            if dot > 0.3:
                # Accelerating in movement direction - add to velocity (Trapezoidal)
                accel_avg = (prev_accel + self.accel) / 2.0
                self.velocity += accel_avg * self.dt
                # Update movement direction (smooth)
                self.movement_direction = (
                    0.9 * self.movement_direction + 0.1 * accel_unit
                )
                md_mag = np.linalg.norm(self.movement_direction)
                if md_mag > 0:
                    self.movement_direction /= md_mag

            elif dot < -0.3:
                # Decelerating (opposite direction) - reduce velocity magnitude
                accel_avg_mag = (np.linalg.norm(prev_accel) + accel_mag) / 2.0
                velocity_mag = np.linalg.norm(self.velocity)
                decel_amount = accel_avg_mag * self.dt
                new_velocity_mag = max(0, velocity_mag - decel_amount)

                if velocity_mag > 0.001:
                    self.velocity = self.movement_direction * new_velocity_mag
                else:
                    self.velocity = np.zeros(3)

            else:
                # Perpendicular - allow some influence for curved paths
                accel_avg = (prev_accel + self.accel) / 2.0
                self.velocity += accel_avg * self.dt * 0.3

    def _update_stationary_euler(self, accel_mag: float):
        """Handle STATIONARY state."""
        if accel_mag > self.start_threshold:
            # Start moving!
            self.state = MovementState.MOVING
            self.movement_direction = self.accel / accel_mag
            self.velocity = self.accel * self.dt
            self.stationary_count = 0

    def _update_moving_euler(self, accel_mag: float):
        """Handle MOVING state."""
        if accel_mag < self.stop_threshold:
            # Might be stopping
            self.stationary_count += 1

            velocity_mag = np.linalg.norm(self.velocity)
            if (
                self.stationary_count > self.stationary_samples_needed
                and velocity_mag < 0.05
            ):
                # Confirmed stopped - apply ZUPT
                self.state = MovementState.STATIONARY
                self.velocity = np.zeros(3)
                self.movement_direction = np.zeros(3)
                return
        else:
            self.stationary_count = 0

        # Check if acceleration is in movement direction or opposite
        if accel_mag > 0.01:
            accel_unit = self.accel / accel_mag
            dot = np.dot(accel_unit, self.movement_direction)

            if dot > 0.3:
                # Accelerating in movement direction - add to velocity
                self.velocity += self.accel * self.dt
                # Update movement direction (smooth)
                self.movement_direction = (
                    0.9 * self.movement_direction + 0.1 * accel_unit
                )
                md_mag = np.linalg.norm(self.movement_direction)
                if md_mag > 0:
                    self.movement_direction /= md_mag

            elif dot < -0.3:
                # Decelerating (opposite direction) - reduce velocity magnitude
                velocity_mag = np.linalg.norm(self.velocity)
                decel_amount = accel_mag * self.dt
                new_velocity_mag = max(0, velocity_mag - decel_amount)

                if velocity_mag > 0.001:
                    self.velocity = self.movement_direction * new_velocity_mag
                else:
                    self.velocity = np.zeros(3)

            else:
                # Perpendicular - allow some influence for curved paths
                self.velocity += self.accel * self.dt * 0.3

    def reset(self):
        """Reset position and velocity to origin."""
        self.position = np.zeros(3)
        self.velocity = np.zeros(3)
        self.state = MovementState.STATIONARY
        self.movement_direction = np.zeros(3)
        self.stationary_count = 0

    def get_unity_position(self) -> list[float]:
        """
        Get position in Unity coordinate system.

        Applies scale factor and coordinate transformation.

        Returns
        -------
        list[float]
            Position [x, y, z] in Unity world space
        """
        return [
            self.base_pos[0] + self.position[0] * self.scale,
            self.base_pos[1] + self.position[2] * self.scale,  # Z -> Y
            self.base_pos[2] + self.position[1] * self.scale,  # Y -> Z
        ]

    def is_stationary(self) -> bool:
        """Check if currently stationary."""
        return self.state == MovementState.STATIONARY

    def get_state_name(self) -> str:
        """Get human-readable state name."""
        return "STATIONARY" if self.state == MovementState.STATIONARY else "MOVING"

    def get_accel_magnitude(self) -> float:
        """Get current acceleration magnitude in m/s²."""
        return float(np.linalg.norm(self.accel))

    def get_velocity_magnitude(self) -> float:
        """Get current velocity magnitude in m/s."""
        return float(np.linalg.norm(self.velocity))

    def get_calibration_progress(self) -> tuple[int, int]:
        """
        Get calibration progress.

        Returns
        -------
        tuple[int, int]
            (current_samples, required_samples)
        """
        return len(self.cal_samples), CALIBRATION_SAMPLES

    def __repr__(self) -> str:
        state = self.get_state_name()
        pos = self.position
        vel_mag = self.get_velocity_magnitude()
        return (
            f"PositionTracker("
            f"state={state}, "
            f"pos=[{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}], "
            f"|vel|={vel_mag:.3f} m/s, "
            f"calibrated={self.calibrated})"
        )
