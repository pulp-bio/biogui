#!/usr/bin/env python3
# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
IMU Data Plotter

Plot acceleration and estimated position from recorded IMU data.
Compare raw data with various causal filters (lowpass, bandpass, DC-blocker).

Usage:
    python imu/plot.py <file.csv>
    python imu/plot.py <file.csv> --lowpass 2 3
    python imu/plot.py <file.csv> --lowpass 2 3 --bandpass 2 0.1 3
    python imu/plot.py <file.csv> --lowpass 2 3 --dc-blocker 0.995 --no-raw
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
    def load_csv(filepath: Path) -> tuple[np.ndarray, np.ndarray]:
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


# =============================================================================
# Filter Design Functions
# =============================================================================


def design_butter_lowpass(order: int, cutoff: float, fs: float) -> np.ndarray:
    """Design Butterworth lowpass filter. Returns SOS coefficients."""
    return scipy.signal.butter(N=order, Wn=cutoff, fs=fs, btype="lowpass", output="sos")


def design_butter_bandpass(
    order: int, low_cutoff: float, high_cutoff: float, fs: float
) -> np.ndarray:
    """Design Butterworth bandpass filter. Returns SOS coefficients."""
    return scipy.signal.butter(
        N=order, Wn=[low_cutoff, high_cutoff], fs=fs, btype="bandpass", output="sos"
    )


def design_dc_blocker(R: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Design Julius O. Smith DC blocker.

    H(z) = (1 - z^-1) / (1 - R*z^-1)

    Cutoff frequency: fc ≈ (1-R) * fs / (2*pi)
    R=0.995 at 40Hz → fc ≈ 0.03 Hz
    """
    b = np.array([1.0, -1.0])
    a = np.array([1.0, -R])
    return b, a


# =============================================================================
# Causal Filter Application (real-time compatible)
# =============================================================================


def apply_sos_causal(data: np.ndarray, sos: np.ndarray) -> np.ndarray:
    """Apply SOS filter causally (uses sosfilt, not sosfiltfilt)."""
    n_ch = data.shape[1]
    zi = np.stack([scipy.signal.sosfilt_zi(sos) for _ in range(n_ch)], axis=-1)
    filtered, _ = scipy.signal.sosfilt(sos, data, axis=0, zi=zi)
    return filtered


def apply_ba_causal(data: np.ndarray, b: np.ndarray, a: np.ndarray) -> np.ndarray:
    """Apply b/a filter causally (uses lfilter, not filtfilt)."""
    n_ch = data.shape[1]
    zi = np.stack([scipy.signal.lfilter_zi(b, a) for _ in range(n_ch)], axis=-1)
    filtered, _ = scipy.signal.lfilter(b, a, data, axis=0, zi=zi)
    return filtered


# =============================================================================
# Integration
# =============================================================================


def integrate_trapezoidal(t: np.ndarray, data: np.ndarray, decay: float = 0.0) -> np.ndarray:
    """Integrate using trapezoidal rule with optional velocity decay."""
    result = np.zeros_like(data)
    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]
        result[i] = result[i - 1] * (1.0 - decay * dt) + 0.5 * (data[i] + data[i - 1]) * dt
    return result


# =============================================================================
# Filter Configuration
# =============================================================================


class FilterConfig:
    """Configuration for a single filter chain."""

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.steps = []  # List of (filter_func, description)

    def add_dc_blocker(self, R: float, fs: float):
        b, a = design_dc_blocker(R)
        self.steps.append((lambda d, b=b, a=a: apply_ba_causal(d, b, a), f"DC(R={R})"))
        return self

    def add_lowpass(self, order: int, cutoff: float, fs: float):
        sos = design_butter_lowpass(order, cutoff, fs)
        self.steps.append((lambda d, s=sos: apply_sos_causal(d, s), f"LP({order},{cutoff}Hz)"))
        return self

    def add_bandpass(self, order: int, low: float, high: float, fs: float):
        sos = design_butter_bandpass(order, low, high, fs)
        self.steps.append((lambda d, s=sos: apply_sos_causal(d, s), f"BP({order},{low}-{high}Hz)"))
        return self

    def apply(self, data: np.ndarray) -> np.ndarray:
        """Apply all filter steps in sequence."""
        result = data.copy()
        for filter_func, _ in self.steps:
            result = filter_func(result)
        return result

    def get_label(self) -> str:
        """Get descriptive label for legend."""
        if not self.steps:
            return self.name
        parts = [desc for _, desc in self.steps]
        return f"{self.name}: {' + '.join(parts)}"


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Plot IMU data with optional filtering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python imu/plot.py data/m_test.csv
  python imu/plot.py data/m_test.csv --lowpass 2 3
  python imu/plot.py data/m_test.csv --lowpass 2 3 --bandpass 2 0.1 3
  python imu/plot.py data/m_test.csv --lowpass 2 3 --dc-blocker 0.995
  python imu/plot.py data/m_test.csv --lowpass 2 3 --dc-blocker 0.995 --no-raw
""",
    )
    parser.add_argument("file", help="CSV file")
    parser.add_argument(
        "--lowpass",
        nargs=2,
        type=float,
        metavar=("ORDER", "CUTOFF"),
        help="Butterworth lowpass: order and cutoff [Hz]",
    )
    parser.add_argument(
        "--bandpass",
        nargs=3,
        type=float,
        metavar=("ORDER", "LOW", "HIGH"),
        help="Butterworth bandpass: order, low cutoff, high cutoff [Hz]",
    )
    parser.add_argument(
        "--dc-blocker",
        type=float,
        metavar="R",
        help="DC blocker pole radius (e.g., 0.995)",
    )
    parser.add_argument(
        "--no-raw",
        action="store_true",
        help="Do not plot raw data",
    )
    parser.add_argument("--decay", type=float, default=0.95, help="Velocity decay (default: 0.95)")
    args = parser.parse_args()

    # Load data
    t, accel = load_csv(args.file)
    fs = estimate_fs(t)
    name = Path(args.file).stem
    print(f"Loaded {len(t)} samples, fs = {fs:.1f} Hz")

    # Build filter configurations
    # Colors: C0=blue, C1=orange, C2=green, C3=red, C4=purple
    filters = []
    color_idx = 1  # Start at C1, C0 is for raw

    if args.lowpass:
        order, cutoff = int(args.lowpass[0]), args.lowpass[1]
        f = FilterConfig("Lowpass", f"C{color_idx}")
        if args.dc_blocker:
            f.add_dc_blocker(args.dc_blocker, fs)
        f.add_lowpass(order, cutoff, fs)
        filters.append(f)
        color_idx += 1
        print(f"  {f.get_label()}")

    if args.bandpass:
        order, low, high = int(args.bandpass[0]), args.bandpass[1], args.bandpass[2]
        f = FilterConfig("Bandpass", f"C{color_idx}")
        if args.dc_blocker and not args.lowpass:
            # Only add DC blocker to bandpass if lowpass doesn't exist
            # (otherwise it's already in lowpass)
            f.add_dc_blocker(args.dc_blocker, fs)
        f.add_bandpass(order, low, high, fs)
        filters.append(f)
        color_idx += 1
        print(f"  {f.get_label()}")

    # If only DC blocker specified (no lowpass or bandpass)
    if args.dc_blocker and not args.lowpass and not args.bandpass:
        f = FilterConfig("DC-blocked", f"C{color_idx}")
        f.add_dc_blocker(args.dc_blocker, fs)
        filters.append(f)
        print(f"  {f.get_label()}")

    # Apply filters and integrate
    results = []  # List of (label, color, accel, pos_mm)

    if not args.no_raw:
        vel_raw = integrate_trapezoidal(t, accel, decay=args.decay)
        pos_raw = integrate_trapezoidal(t, vel_raw, decay=args.decay)
        results.append(("Raw", "C0", accel, pos_raw * 1000))

    for filt in filters:
        filtered = filt.apply(accel)
        vel = integrate_trapezoidal(t, filtered, decay=args.decay)
        pos = integrate_trapezoidal(t, vel, decay=args.decay)
        results.append((filt.get_label(), filt.color, filtered, pos * 1000))

    if not results:
        print("Nothing to plot (use filters or remove --no-raw)")
        return

    # Compute shared y-axis limits
    accel_max = max(np.max(np.abs(a)) for _, _, a, _ in results)
    accel_lim = (-accel_max * 1.1, accel_max * 1.1)

    pos_max = max(np.max(np.abs(p)) for _, _, _, p in results)
    pos_lim = (-pos_max * 1.1, pos_max * 1.1)

    # Determine alpha based on number of curves
    n_curves = len(results)
    alpha = 0.9 if n_curves == 1 else 0.7

    # Plot acceleration
    fig1, axes1 = plt.subplots(3, 1, figsize=(14, 9), sharex=True)
    accel_labels = ["$a_x$", "$a_y$", "$a_z$"]

    for i, (ax, lbl) in enumerate(zip(axes1, accel_labels)):
        for name, color, accel_data, _ in results:
            ax.plot(t, accel_data[:, i], color, alpha=alpha, label=name)
        ax.set_ylabel(f"{lbl} [m/s²]")
        ax.set_ylim(accel_lim)
        ax.grid(True, alpha=0.3)
        if i == 0:
            ax.legend(loc="upper right")

    axes1[-1].set_xlabel("Time [s]")
    axes1[0].set_title(f"Acceleration — {name}")
    fig1.tight_layout()

    # Plot position
    fig2, axes2 = plt.subplots(3, 1, figsize=(14, 9), sharex=True)
    pos_labels = ["$x$", "$y$", "$z$"]

    for i, (ax, lbl) in enumerate(zip(axes2, pos_labels)):
        for name, color, _, pos_data in results:
            ax.plot(t, pos_data[:, i], color, alpha=alpha, label=name)
        ax.set_ylabel(f"{lbl} [mm]")
        ax.set_ylim(pos_lim)
        ax.grid(True, alpha=0.3)
        if i == 0:
            ax.legend(loc="upper right")

    axes2[-1].set_xlabel("Time [s]")
    axes2[0].set_title(f"Position — {name} (decay={args.decay})")
    fig2.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()
