"""
IMU Frequency Analysis

Compare FFT of movement data vs rest data to identify relevant frequency bands.
Automatically loads all m_*.csv and r_*.csv files from data directory.

Usage:
    python imu/freq.py
    python imu/freq.py --energy-threshold 80
    python imu/freq.py --highpass 0.5  # Filter out DC and low freq noise
    python imu/freq.py --lowpass 20    # Analyze only up to 20 Hz
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Handle both direct execution and module execution
try:
    from . import DATA_DIR, estimate_fs, load_all_files, load_csv
except ImportError:
    # Direct execution - define utilities locally
    DATA_DIR = Path(__file__).parent / "data"

    def load_csv(filepath: Path) -> tuple[np.ndarray, np.ndarray]:
        """Load IMU data from CSV."""
        data = np.genfromtxt(filepath, delimiter=",", skip_header=1)
        return data[:, 0], data[:, 1:4]

    def estimate_fs(t: np.ndarray) -> float:
        """Estimate sampling frequency."""
        return 1.0 / np.median(np.diff(t))

    def load_all_files(prefix: str) -> list[tuple[Path, np.ndarray, np.ndarray]]:
        """Load all files matching prefix."""
        files = sorted(DATA_DIR.glob(f"{prefix}_*.csv"))
        result = []
        for f in files:
            t, accel = load_csv(f)
            result.append((f, t, accel))
        return result


# Larger fonts for high-DPI displays
plt.rcParams.update(
    {
        "figure.dpi": 100,
        "font.size": 16,
        "axes.titlesize": 18,
        "axes.labelsize": 16,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "legend.fontsize": 13,
        "lines.linewidth": 1.2,
    }
)


def remove_dc(accel: np.ndarray) -> np.ndarray:
    """Remove DC component (mean) from each axis."""
    return accel - np.mean(accel, axis=0)


def apply_highpass(accel: np.ndarray, fs: float, cutoff: float) -> np.ndarray:
    """Apply highpass filter to remove low-frequency noise and DC."""
    nyquist = fs / 2
    normalized_cutoff = cutoff / nyquist

    # Butterworth 4th order highpass
    sos = signal.butter(4, normalized_cutoff, btype="high", output="sos")
    filtered = np.zeros_like(accel)
    for i in range(3):
        filtered[:, i] = signal.sosfilt(sos, accel[:, i])
    return filtered


def apply_lowpass(accel: np.ndarray, fs: float, cutoff: float) -> np.ndarray:
    """Apply lowpass filter to remove high-frequency noise."""
    nyquist = fs / 2
    normalized_cutoff = cutoff / nyquist

    # Butterworth 4th order lowpass
    sos = signal.butter(4, normalized_cutoff, btype="low", output="sos")
    filtered = np.zeros_like(accel)
    for i in range(3):
        filtered[:, i] = signal.sosfilt(sos, accel[:, i])
    return filtered


def compute_psd(
    t: np.ndarray,
    accel: np.ndarray,
    highpass_cutoff: float = None,
    lowpass_cutoff: float = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute power spectral density (magnitude squared)."""
    fs = estimate_fs(t)

    # Remove DC component
    accel_filtered = remove_dc(accel)

    # Optional: Apply highpass filter
    if highpass_cutoff is not None and highpass_cutoff > 0:
        accel_filtered = apply_highpass(accel_filtered, fs, highpass_cutoff)

    # Optional: Apply lowpass filter
    if lowpass_cutoff is not None and lowpass_cutoff > 0:
        accel_filtered = apply_lowpass(accel_filtered, fs, lowpass_cutoff)

    n = len(t)
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    fft = np.fft.rfft(accel_filtered, axis=0)
    psd = (np.abs(fft) ** 2) / n
    return freqs, psd


def compute_average_psd(
    files: list[tuple[Path, np.ndarray, np.ndarray]],
    max_freq: float = None,
    highpass_cutoff: float = None,
    lowpass_cutoff: float = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute average PSD across files, interpolated to common frequency grid."""
    all_fs = [estimate_fs(t) for _, t, _ in files]
    min_fs = min(all_fs)
    max_f = (min_fs / 2) if max_freq is None else min(max_freq, min_fs / 2)

    # Common frequency grid (0.1 Hz resolution)
    freq_grid = np.arange(0.1, max_f, 0.1)

    # Interpolate each file's PSD to common grid
    all_psd = []
    for _, t, accel in files:
        freqs, psd = compute_psd(t, accel, highpass_cutoff, lowpass_cutoff)
        psd_interp = np.zeros((len(freq_grid), 3))
        for i in range(3):
            psd_interp[:, i] = np.interp(freq_grid, freqs, psd[:, i])
        all_psd.append(psd_interp)

    psd_array = np.array(all_psd)
    mean_psd = np.mean(psd_array, axis=0)
    std_psd = np.std(psd_array, axis=0)

    return freq_grid, mean_psd, std_psd


def compute_cumulative_energy(freqs: np.ndarray, psd: np.ndarray) -> np.ndarray:
    """Compute cumulative energy (fraction of total) vs frequency."""
    psd_total = np.sum(psd, axis=1)
    cumsum = np.cumsum(psd_total)
    return cumsum / cumsum[-1]


def main():
    parser = argparse.ArgumentParser(description="Frequency analysis")
    parser.add_argument(
        "--energy-threshold",
        type=float,
        default=80,
        help="Energy threshold [%%] for cutoff suggestion (default: 80)",
    )
    parser.add_argument(
        "--highpass",
        type=float,
        default=0.5,
        help="Highpass cutoff in Hz to remove DC and low-freq noise (default 0.5)",
    )
    parser.add_argument(
        "--lowpass",
        type=float,
        default=20.0,
        help="Lowpass cutoff in Hz to limit analysis bandwidth (default 20)",
    )
    args = parser.parse_args()

    # Load files
    movement_files = load_all_files("m")
    rest_files = load_all_files("r")

    if not movement_files:
        print("No movement files (m_*.csv) found")
        return
    if not rest_files:
        print("No rest files (r_*.csv) found")
        return

    print(f"Movement files: {[f.name for f, _, _ in movement_files]}")
    print(f"Rest files: {[f.name for f, _, _ in rest_files]}")
    if args.highpass:
        print(f"Highpass filter: {args.highpass} Hz (removes DC and low-freq noise)")
    if args.lowpass:
        print(f"Lowpass filter: {args.lowpass} Hz (removes high-freq noise)")

    # Compute average PSDs (limited to lowpass frequency)
    freq_m, psd_m, std_m = compute_average_psd(
        movement_files,
        max_freq=args.lowpass,
        highpass_cutoff=args.highpass,
        lowpass_cutoff=args.lowpass,
    )
    freq_r, psd_r, std_r = compute_average_psd(
        rest_files,
        max_freq=args.lowpass,
        highpass_cutoff=args.highpass,
        lowpass_cutoff=args.lowpass,
    )

    # Cumulative energy
    cum_energy_m = compute_cumulative_energy(freq_m, psd_m)
    cum_energy_r = compute_cumulative_energy(freq_r, psd_r)

    # Total PSD (sum of all axes)
    psd_m_total = np.sum(psd_m, axis=1)
    psd_r_total = np.sum(psd_r, axis=1)
    std_m_total = np.sqrt(np.sum(std_m**2, axis=1))
    std_r_total = np.sqrt(np.sum(std_r**2, axis=1))

    # Find cutoff frequencies
    threshold = args.energy_threshold / 100
    idx_m = np.searchsorted(cum_energy_m, threshold)
    idx_r = np.searchsorted(cum_energy_r, threshold)
    cutoff_m = freq_m[min(idx_m, len(freq_m) - 1)]
    cutoff_r = freq_r[min(idx_r, len(freq_r) - 1)]

    # Print analysis
    print("\n" + "=" * 50)
    print("FREQUENCY ANALYSIS")
    print("=" * 50)

    print("\nCumulative energy (movement):")
    for pct in [50, 80, 90, 95, 99]:
        idx = np.searchsorted(cum_energy_m, pct / 100)
        if idx < len(freq_m):
            print(f"  {pct:2d}% of energy below {freq_m[idx]:.1f} Hz")

    print("\nCumulative energy (rest/noise):")
    for pct in [50, 80, 90, 95, 99]:
        idx = np.searchsorted(cum_energy_r, pct / 100)
        if idx < len(freq_r):
            print(f"  {pct:2d}% of energy below {freq_r[idx]:.1f} Hz")

    print(f"\nSuggested lowpass cutoff ({args.energy_threshold:.0f}% energy):")
    print(f"  Movement: {cutoff_m:.1f} Hz")
    print(f"  Rest:     {cutoff_r:.1f} Hz")

    # Signal-to-Noise analysis
    print("\n" + "-" * 50)
    print("Signal-to-Noise Analysis")
    print("-" * 50)
    avg_movement_power = np.mean(psd_m_total)
    avg_rest_power = np.mean(psd_r_total)
    snr_linear = (
        avg_movement_power / avg_rest_power if avg_rest_power > 0 else float("inf")
    )
    snr_db = 10 * np.log10(snr_linear) if snr_linear > 0 else float("inf")
    print(f"  Average movement power: {avg_movement_power:.2e} (m/s²)²/Hz")
    print(f"  Average rest power:     {avg_rest_power:.2e} (m/s²)²/Hz")
    print(f"  Signal-to-Noise Ratio:  {snr_linear:.1f} ({snr_db:.1f} dB)")

    # Typical hand movement frequencies
    print("\n" + "-" * 50)
    print("Reference: Typical hand movement frequencies")
    print("-" * 50)
    print("  Voluntary hand motion:    0.5 - 5 Hz")
    print("  Fast intentional motion:  up to 8 Hz")
    print("  Physiological tremor:     8 - 12 Hz")
    print("  Pathological tremor:      4 - 8 Hz")

    # Plot 1: PSD comparison (all axes combined)
    fig1, ax1 = plt.subplots(figsize=(14, 8))

    ax1.semilogy(freq_m, psd_m_total, "C0", label="Movement", linewidth=2)
    ax1.fill_between(
        freq_m,
        np.maximum(psd_m_total - std_m_total, 1e-12),
        psd_m_total + std_m_total,
        color="C0",
        alpha=0.2,
    )
    ax1.semilogy(freq_r, psd_r_total, "C3", label="Rest (Noise Floor)", linewidth=2)
    ax1.fill_between(
        freq_r,
        np.maximum(psd_r_total - std_r_total, 1e-12),
        psd_r_total + std_r_total,
        color="C3",
        alpha=0.2,
    )

    ax1.axvline(
        cutoff_m,
        color="C0",
        linestyle="--",
        alpha=0.7,
        label=f"Movement {args.energy_threshold:.0f}%: {cutoff_m:.1f} Hz",
    )
    ax1.axvline(
        cutoff_r,
        color="C3",
        linestyle="--",
        alpha=0.7,
        label=f"Rest {args.energy_threshold:.0f}%: {cutoff_r:.1f} Hz",
    )

    ax1.set_xlabel("Frequency [Hz]")
    ax1.set_ylabel("Power Spectral Density [$(m/s^2)^2$/Hz]")
    title = "PSD: Movement vs Rest (sum of $a_x$, $a_y$, $a_z$)"
    filter_info = []
    if args.highpass:
        filter_info.append(f"HP: {args.highpass} Hz")
    if args.lowpass:
        filter_info.append(f"LP: {args.lowpass} Hz")
    if filter_info:
        title += f" [{', '.join(filter_info)}]"
    ax1.set_title(title)
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, min(args.lowpass, freq_m[-1]))

    fig1.tight_layout()

    # Plot 2: Cumulative energy
    fig2, ax2 = plt.subplots(figsize=(14, 8))

    ax2.plot(freq_m, cum_energy_m * 100, "C0", linewidth=2, label="Movement")
    ax2.plot(freq_r, cum_energy_r * 100, "C3", linewidth=2, label="Rest")

    # Highlight threshold line
    ax2.axhline(
        args.energy_threshold,
        color="C1",
        linestyle="-",
        linewidth=2,
        alpha=0.8,
        label=f"{args.energy_threshold:.0f}% threshold",
    )

    # Mark other threshold percentages (lighter)
    for pct in [50, 80, 95]:
        if pct != args.energy_threshold:
            ax2.axhline(pct, color="gray", linestyle=":", alpha=0.4)
            ax2.text(
                freq_m[-1] * 0.98,
                pct + 1.5,
                f"{pct}%",
                ha="right",
                fontsize=13,
                color="gray",
            )

    # Mark cutoff frequencies
    ax2.axvline(cutoff_m, color="C0", linestyle="--", linewidth=1.5, alpha=0.7)
    ax2.axvline(cutoff_r, color="C3", linestyle="--", linewidth=1.5, alpha=0.7)
    ax2.plot(cutoff_m, args.energy_threshold, "C0o", markersize=12)
    ax2.plot(cutoff_r, args.energy_threshold, "C3o", markersize=12)

    # Annotate cutoff frequencies
    ax2.annotate(
        f"{cutoff_m:.1f} Hz",
        xy=(cutoff_m, args.energy_threshold),
        xytext=(cutoff_m + 0.5, args.energy_threshold - 8),
        fontsize=13,
        color="C0",
    )
    ax2.annotate(
        f"{cutoff_r:.1f} Hz",
        xy=(cutoff_r, args.energy_threshold),
        xytext=(cutoff_r + 0.5, args.energy_threshold - 8),
        fontsize=13,
        color="C3",
    )

    ax2.set_xlabel("Frequency [Hz]")
    ax2.set_ylabel("Cumulative Energy [%]")
    title = "Cumulative Energy Distribution"
    filter_info = []
    if args.highpass:
        filter_info.append(f"HP: {args.highpass} Hz")
    if args.lowpass:
        filter_info.append(f"LP: {args.lowpass} Hz")
    if filter_info:
        title += f" [{', '.join(filter_info)}]"
    ax2.set_title(title)
    ax2.legend(loc="lower right")
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, min(args.lowpass, freq_m[-1]))
    ax2.set_ylim(0, 105)

    fig2.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()
