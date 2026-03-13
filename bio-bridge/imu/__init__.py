"""
IMU analysis and tracking module for BioBridge middleware.

Provides tools for IMU data recording, analysis, and position tracking.

Submodules:
- record: Record IMU data from BioGUI
- plot: Plot recorded IMU data
- freq: Frequency analysis of IMU signals
- freq_snr: SNR-based frequency analysis
- integration_test: Test double integration accuracy

Shared utilities are provided for common operations like loading
CSV files and estimating sampling frequency.
"""

from pathlib import Path

import numpy as np

# Data directory for IMU recordings
DATA_DIR = Path(__file__).parent / "data"


def load_csv(filepath: Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Load IMU data from CSV file.

    Parameters
    ----------
    filepath : Path
        Path to CSV file with columns: time, ax, ay, az

    Returns
    -------
    t : np.ndarray
        Timestamps in seconds
    accel : np.ndarray
        Acceleration data with shape (N, 3) for [ax, ay, az]
    """
    data = np.genfromtxt(filepath, delimiter=",", skip_header=1)
    return data[:, 0], data[:, 1:4]


def estimate_fs(t: np.ndarray) -> float:
    """
    Estimate sampling frequency from timestamps.

    Parameters
    ----------
    t : np.ndarray
        Timestamps in seconds

    Returns
    -------
    float
        Estimated sampling frequency in Hz
    """
    return 1.0 / np.median(np.diff(t))


def load_all_files(prefix: str) -> list[tuple[Path, np.ndarray, np.ndarray]]:
    """
    Load all CSV files matching a prefix from the data directory.

    Parameters
    ----------
    prefix : str
        Filename prefix to match (e.g., "m" for movement, "r" for rest)

    Returns
    -------
    list[tuple[Path, np.ndarray, np.ndarray]]
        List of (filepath, timestamps, acceleration) tuples
    """
    files = sorted(DATA_DIR.glob(f"{prefix}_*.csv"))
    result = []
    for f in files:
        t, accel = load_csv(f)
        result.append((f, t, accel))
    return result


__all__ = [
    "DATA_DIR",
    "load_csv",
    "estimate_fs",
    "load_all_files",
]
