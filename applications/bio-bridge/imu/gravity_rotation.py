# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Gravity-based rotation tracker for forearm supination/pronation.

Uses the gravity vector from IMU accelerometer to estimate forearm rotation
around its longitudinal axis. Requires calibration to establish neutral position.
"""

import numpy as np

from core import CALIBRATION_SAMPLES, MEAS_PERIOD


class GravityRotationTracker:
    """
    Track forearm rotation using gravity vector.

    Measures supination (palm up) and pronation (palm down) by analyzing
    how the gravity vector changes in the sensor reference frame.
    """

    # Conversion from raw IMU units to m/s²
    RAW_TO_MS2 = 9.81 / 17327.0

    # Rotation limits (matching Unity's HandRotationLimits.cs)
    PRONATION_MAX = -35.0  # Maximum pronation (negative)
    SUPINATION_MAX = 149.0  # Maximum supination (positive)

    def __init__(
        self,
        dt: float = MEAS_PERIOD,
        smoothing: float = 0.0,
        flip_imu: bool = False,
    ):
        self.dt = dt
        self.smoothing = smoothing
        self.flip_imu = flip_imu

        # Calibration state
        self.neutral_gravity = np.zeros(3)
        self.calibrated = False
        self.cal_samples = []

        # Current state
        self.raw_angle = 0.0
        self.current_angle = 0.0
        self.last_raw_angle = 0.0

        # Set rotation limits based on orientation
        self.pronation_limit = self.PRONATION_MAX
        self.supination_limit = self.SUPINATION_MAX

    def start_calibration(self):
        """
        Start calibration process.

        Keep the forearm in neutral position (palm facing inward/sideways)
        and call this, then add samples, then finish_calibration().
        """
        self.cal_samples = []
        self.calibrated = False  # Pause tracking during re-calibration

    def add_calibration_sample(self, raw: np.ndarray):
        """
        Add calibration sample.

        Parameters
        ----------
        raw : np.ndarray
            Raw IMU reading [ax, ay, az] as int16 values
        """
        self.cal_samples.append(raw.astype(float))

    def finish_calibration(self) -> bool:
        """
        Finish calibration and compute neutral gravity direction.

        Returns
        -------
        bool
            True if calibration succeeded, False otherwise
        """
        if len(self.cal_samples) < CALIBRATION_SAMPLES:
            return False

        # Average all calibration samples
        samples = np.array(self.cal_samples)
        self.neutral_gravity = np.mean(samples, axis=0)

        # Normalize to unit vector
        mag = np.linalg.norm(self.neutral_gravity)
        if mag < 100.0:  # Safety check in raw units
            return False

        self.neutral_gravity /= mag

        # Reset angle state
        self.raw_angle = 0.0
        self.current_angle = 0.0
        self.calibrated = True

        return True

    def update(self, raw_imu: np.ndarray):
        """
        Update rotation estimate from new IMU sample.
        """
        if not self.calibrated:
            return

        # Normalize current gravity
        current_gravity = raw_imu.astype(float)
        mag = np.linalg.norm(current_gravity)

        if mag < 100.0:
            return

        current_gravity /= mag

        # Extract XZ components (perpendicular to Y-axis rotation)
        # Index: [0]=X, [1]=Y, [2]=Z in probe coordinates
        neutral_x = self.neutral_gravity[0]
        neutral_z = self.neutral_gravity[2]

        current_x = current_gravity[0]
        current_z = current_gravity[2]

        # Calculate angle in XZ plane
        # This is the rotation around Y-axis
        neutral_angle = np.arctan2(neutral_x, neutral_z)
        current_angle = np.arctan2(current_x, current_z)

        # Rotation difference
        angle_diff = neutral_angle - current_angle

        # Normalize to [-π, π]
        while angle_diff > np.pi:
            angle_diff -= 2 * np.pi
        while angle_diff < -np.pi:
            angle_diff += 2 * np.pi

        # Convert to degrees and flip if necessary
        new_raw_angle = np.degrees(angle_diff)
        if self.flip_imu:
            new_raw_angle *= -1

        # Detect and fix wrap-around jumps
        # If jump is > 180°, we wrapped around
        jump = new_raw_angle - self.last_raw_angle
        if jump > 180.0:
            # Wrapped from negative to positive - subtract 360
            new_raw_angle -= 360.0
        elif jump < -180.0:
            # Wrapped from positive to negative - add 360
            new_raw_angle += 360.0

        self.raw_angle = new_raw_angle
        self.last_raw_angle = new_raw_angle

        # Smoothing and clipping to Unity limits
        self.current_angle = np.clip(
            self.smoothing * self.current_angle + (1 - self.smoothing) * self.raw_angle,
            self.pronation_limit,
            self.supination_limit,
        )

    def get_angle(self) -> float:
        """
        Get current smoothed rotation angle in degrees.

        Returns
        -------
        float
            Rotation angle. Positive = supination, negative = pronation.
        """
        return self.current_angle

    def get_raw_angle(self) -> float:
        """
        Get unsmoothed rotation angle.

        Returns
        -------
        float
            Raw rotation angle in degrees
        """
        return self.raw_angle

    def reset(self):
        """Reset angle to zero without losing calibration."""
        self.raw_angle = 0.0
        self.current_angle = 0.0

    @property
    def is_calibrated(self) -> bool:
        """Check if tracker is calibrated."""
        return self.calibrated

    @property
    def calibration_samples(self) -> int:
        """Number of calibration samples collected."""
        return len(self.cal_samples)

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
        return (
            f"GravityRotationTracker("
            f"angle={self.current_angle:.1f}°, "
            f"calibrated={self.calibrated})"
        )
