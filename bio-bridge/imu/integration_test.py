#!/usr/bin/env python3
"""
IMU Integration Test for Single Movement Data

Tests trapezoidal integration with causal Butterworth lowpass filtering
on single-movement data (50 cm movement along X-axis).

Usage:
    python imu/integration_test.py
    python imu/integration_test.py --cutoff 3
    python imu/integration_test.py --cutoff 5 --decay 0.9
    python imu/integration_test.py --no-filter
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import scipy.signal

# Handle both direct execution and module execution
try:
    from . import estimate_fs, load_csv
except ImportError:
    # Direct execution - define utilities locally
    def load_csv(filepath: str) -> tuple[np.ndarray, np.ndarray]:
        """Load IMU data from CSV."""
        data = np.genfromtxt(filepath, delimiter=",", skip_header=1)
        return data[:, 0], data[:, 1:4]

    def estimate_fs(t: np.ndarray) -> float:
        """Estimate sampling frequency from timestamps."""
        return 1.0 / np.median(np.diff(t))


# Larger fonts for high-DPI displays
plt.rcParams.update(
    {
        "figure.dpi": 100,
        "font.size": 16,
        "axes.titlesize": 18,
        "axes.labelsize": 16,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "legend.fontsize": 12,
        "lines.linewidth": 1.2,
    }
)


def design_butter_lowpass(order: int, cutoff: float, fs: float) -> np.ndarray:
    """Design Butterworth lowpass filter. Returns SOS coefficients."""
    return scipy.signal.butter(N=order, Wn=cutoff, fs=fs, btype="lowpass", output="sos")


def apply_sos_causal(data: np.ndarray, sos: np.ndarray) -> np.ndarray:
    """Apply SOS filter causally (real-time compatible)."""
    n_ch = data.shape[1]
    zi = np.stack([scipy.signal.sosfilt_zi(sos) for _ in range(n_ch)], axis=-1)
    filtered, _ = scipy.signal.sosfilt(sos, data, axis=0, zi=zi)
    return filtered


def integrate_trapezoidal(
    t: np.ndarray, data: np.ndarray, decay: float = 0.0
) -> np.ndarray:
    """Integrate using trapezoidal rule with optional velocity decay."""
    result = np.zeros_like(data)
    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]
        result[i] = (
            result[i - 1] * (1.0 - decay * dt) + 0.5 * (data[i] + data[i - 1]) * dt
        )
    return result


def process_file(
    filepath: Path,
    cutoff: float | None,
    decay: float,
    order: int = 2,
) -> dict:
    """
    Process a single CSV file with optional filtering and integration.

    Returns dict with:
        - name: filename
        - t: timestamps
        - accel_raw: raw acceleration
        - accel_filt: filtered acceleration (or None)
        - pos_raw: position from raw data [mm]
        - pos_filt: position from filtered data [mm] (or None)
        - fs: sampling frequency
    """
    # Load data
    t, accel = load_csv(str(filepath))
    fs = estimate_fs(t)

    # Raw integration
    vel_raw = integrate_trapezoidal(t, accel, decay=decay)
    pos_raw = integrate_trapezoidal(t, vel_raw, decay=decay)

    # Filtered integration
    accel_filt = None
    pos_filt = None
    if cutoff is not None:
        sos = design_butter_lowpass(order, cutoff, fs)
        accel_filt = apply_sos_causal(accel, sos)
        vel_filt = integrate_trapezoidal(t, accel_filt, decay=decay)
        pos_filt = integrate_trapezoidal(t, vel_filt, decay=decay)

    return {
        "name": filepath.stem,
        "t": t,
        "accel_raw": accel,
        "accel_filt": accel_filt,
        "pos_raw": pos_raw * 1000,  # Convert to mm
        "pos_filt": pos_filt * 1000 if pos_filt is not None else None,
        "fs": fs,
    }


def find_max_displacement(pos: np.ndarray, axis: int = 0) -> tuple[float, float, float]:
    """
    Find maximum displacement along specified axis.

    Returns:
        - max_displacement: maximum absolute displacement [mm]
        - final_displacement: final displacement [mm]
        - peak_to_peak: peak-to-peak displacement [mm]
    """
    pos_axis = pos[:, axis]
    max_disp = np.max(np.abs(pos_axis))
    final_disp = pos_axis[-1]
    peak_to_peak = np.max(pos_axis) - np.min(pos_axis)
    return max_disp, final_disp, peak_to_peak


def plot_results(
    results: list[dict], cutoff: float | None, decay: float, target_mm: float = 500.0
):
    """
    Plot acceleration and position for all files.
    """
    n_files = len(results)

    # Create figure with subplots for each file
    fig, axes = plt.subplots(n_files, 2, figsize=(16, 5 * n_files), squeeze=False)

    for i, res in enumerate(results):
        t = res["t"]
        name = res["name"]

        # Left plot: Acceleration (X-axis only, since movement is along X)
        ax_accel = axes[i, 0]
        ax_accel.plot(t, res["accel_raw"][:, 0], "C0", alpha=0.6, label="Raw")
        if res["accel_filt"] is not None:
            ax_accel.plot(
                t,
                res["accel_filt"][:, 0],
                "C1",
                alpha=0.9,
                linewidth=1.5,
                label=f"{cutoff} Hz",
            )
        ax_accel.set_ylabel("$a_x$ [m/s²]")
        ax_accel.set_xlabel("Time [s]")
        ax_accel.grid(True, alpha=0.3)
        ax_accel.legend()
        ax_accel.set_title(f"{name} — Acceleration")

        # Right plot: Position (X-axis only)
        ax_pos = axes[i, 1]

        # Raw position
        max_raw, final_raw, p2p_raw = find_max_displacement(res["pos_raw"], axis=0)
        error_raw = abs(p2p_raw - target_mm)
        ax_pos.plot(
            t, res["pos_raw"][:, 0], "C0", alpha=0.6, label=f"Raw ({p2p_raw:.0f} mm)"
        )

        # Filtered position
        if res["pos_filt"] is not None:
            max_filt, final_filt, p2p_filt = find_max_displacement(
                res["pos_filt"], axis=0
            )
            error_filt = abs(p2p_filt - target_mm)
            ax_pos.plot(
                t,
                res["pos_filt"][:, 0],
                "C1",
                alpha=0.9,
                linewidth=1.5,
                label=f"{cutoff} Hz ({p2p_filt:.0f} mm)",
            )

        # Target line
        ax_pos.axhline(
            target_mm,
            color="g",
            linestyle="--",
            alpha=0.5,
            label="Target",
        )
        ax_pos.axhline(0, color="k", linestyle="-", alpha=0.3, linewidth=0.8)

        ax_pos.set_ylabel("$x$ [mm]")
        ax_pos.set_xlabel("Time [s]")
        ax_pos.grid(True, alpha=0.3)
        ax_pos.legend()
        ax_pos.set_title(f"{name} — Position (decay={decay})")

    fig.tight_layout()


def main():
    parser = argparse.ArgumentParser(
        description="Integration test for IMU single-movement data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python imu/integration_test.py
  python imu/integration_test.py --cutoff 3
  python imu/integration_test.py --cutoff 5 --decay 0.9
  python imu/integration_test.py --no-filter --decay 0.95
""",
    )
    parser.add_argument(
        "--cutoff",
        type=float,
        default=5.0,
        help="Lowpass cutoff frequency [Hz] (default: 5.0)",
    )
    parser.add_argument(
        "--decay",
        type=float,
        default=0.9,
        help="Velocity decay factor (default: 0.9)",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Disable filtering (only show raw)",
    )
    parser.add_argument(
        "--target",
        type=float,
        default=500.0,
        help="Target displacement in mm (default: 500.0)",
    )
    args = parser.parse_args()

    # Find all single-movement files
    data_dir = Path("imu/data")
    if not data_dir.exists():
        # Try alternative path
        data_dir = Path("data")

    if not data_dir.exists():
        print("Error: Could not find data directory")
        return

    sm_files = sorted(data_dir.glob("sm_*.csv"))

    if not sm_files:
        print(f"Error: No sm_*.csv files found in {data_dir}")
        return

    print(f"Found {len(sm_files)} single-movement files:")
    for f in sm_files:
        print(f"  {f.name}")

    # Process all files
    cutoff = None if args.no_filter else args.cutoff
    results = []

    for filepath in sm_files:
        res = process_file(filepath, cutoff, args.decay)
        results.append(res)

    # Plot results
    plot_results(results, cutoff, args.decay, args.target)
    plt.show()


if __name__ == "__main__":
    main()
