"""
IMU Frequency Analysis - SNR-based approach

Identifies frequency bands where movement signal is significantly stronger
than rest/noise by computing Signal-to-Noise Ratio (SNR).

Usage:
    python imu/freq_snr.py                       # Auto threshold
    python imu/freq_snr.py --snr-threshold 6     # Manual threshold
    python imu/freq_snr.py --threshold-margin 10 # Adjust auto threshold
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


plt.rcParams.update(
    {
        "figure.dpi": 100,
        "font.size": 14,
        "axes.titlesize": 16,
        "axes.labelsize": 14,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 12,
        "lines.linewidth": 1.5,
    }
)


def compute_psd(t: np.ndarray, accel: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute power spectral density using Welch's method for smoothing."""
    fs = estimate_fs(t)
    n = len(t)

    # Use Welch's method for smoother PSD estimate
    nperseg = min(256, n // 4)
    freqs, psd = signal.welch(accel, fs=fs, nperseg=nperseg, axis=0)

    return freqs, psd


def compute_average_psd(
    files: list[tuple[Path, np.ndarray, np.ndarray]], max_freq: float = None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute average PSD across files, interpolated to common frequency grid."""
    all_fs = [estimate_fs(t) for _, t, _ in files]
    min_fs = min(all_fs)
    max_f = (min_fs / 2) if max_freq is None else min(max_freq, min_fs / 2)

    # Common frequency grid (0.1 Hz resolution)
    freq_grid = np.arange(0.1, max_f, 0.1)  # Start at 0.1 to avoid division by zero

    # Interpolate each file's PSD to common grid
    all_psd = []
    for _, t, accel in files:
        freqs, psd = compute_psd(t, accel)
        psd_interp = np.zeros((len(freq_grid), 3))
        for i in range(3):
            psd_interp[:, i] = np.interp(freq_grid, freqs, psd[:, i])
        all_psd.append(psd_interp)

    psd_array = np.array(all_psd)
    mean_psd = np.mean(psd_array, axis=0)
    std_psd = np.std(psd_array, axis=0)

    return freq_grid, mean_psd, std_psd


def compute_auto_threshold(snr_db: np.ndarray, margin_db: float = 6.0) -> float:
    """
    Automatically determine SNR threshold from data.

    Uses 25th percentile of SNR as baseline (typical noise level) and adds a margin.
    """
    baseline_snr = np.percentile(snr_db, 25)  # 25th percentile = lower quartile
    threshold = baseline_snr + margin_db
    return threshold


def find_significant_bands(
    freqs: np.ndarray, snr_db: np.ndarray, threshold_db: float
) -> list[tuple[float, float, float]]:
    """
    Find contiguous frequency bands where SNR > threshold.

    Returns:
        List of (f_start, f_end, avg_snr_db) tuples
    """
    above_threshold = snr_db > threshold_db
    bands = []

    in_band = False
    band_start = 0

    for i, is_above in enumerate(above_threshold):
        if is_above and not in_band:
            # Start new band
            in_band = True
            band_start = i
        elif not is_above and in_band:
            # End current band
            in_band = False
            band_snr = np.mean(snr_db[band_start:i])
            bands.append((freqs[band_start], freqs[i - 1], band_snr))

    # Handle case where band extends to end
    if in_band:
        band_snr = np.mean(snr_db[band_start:])
        bands.append((freqs[band_start], freqs[-1], band_snr))

    return bands


def main():
    parser = argparse.ArgumentParser(description="SNR-based frequency analysis")
    parser.add_argument(
        "--snr-threshold",
        type=float,
        default=None,
        help="SNR threshold in dB (6dB=4x, 10dB=10x stronger). If not set, uses auto-threshold.",
    )
    parser.add_argument(
        "--threshold-margin",
        type=float,
        default=6.0,
        help="Margin in dB above median SNR for auto-threshold (default: 6.0)",
    )
    parser.add_argument(
        "--max-freq",
        type=float,
        default=15.0,
        help="Maximum frequency to analyze in Hz (default: 15.0)",
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

    print(f"Movement files: {len(movement_files)}")
    print(f"Rest files: {len(rest_files)}")

    # Compute average PSDs
    freq_m, psd_m, std_m = compute_average_psd(movement_files, args.max_freq)
    freq_r, psd_r, std_r = compute_average_psd(rest_files, args.max_freq)

    # Total PSD (sum of all axes)
    psd_m_total = np.sum(psd_m, axis=1)
    psd_r_total = np.sum(psd_r, axis=1)

    # Compute SNR (with small epsilon to avoid division by zero)
    epsilon = 1e-12
    snr = psd_m_total / (psd_r_total + epsilon)
    snr_db = 10 * np.log10(snr)

    # Determine threshold
    if args.snr_threshold is not None:
        threshold = args.snr_threshold
        threshold_mode = "manual"
    else:
        threshold = compute_auto_threshold(snr_db, args.threshold_margin)
        threshold_mode = "auto"

    # Compute difference
    psd_diff = psd_m_total - psd_r_total

    # Find significant frequency bands
    sig_bands = find_significant_bands(freq_m, snr_db, threshold)

    # Print analysis
    print("\n" + "=" * 70)
    print("FREQUENCY ANALYSIS")
    print("=" * 70)

    # SNR statistics
    print("\nSNR Statistics:")
    print(f"  Median:  {np.median(snr_db):5.1f} dB  (typical noise floor)")
    print(f"  Mean:    {np.mean(snr_db):5.1f} dB")
    print(f"  Max:     {np.max(snr_db):5.1f} dB")

    print(f"\nThreshold: {threshold:.1f} dB ({threshold_mode})")
    if threshold_mode == "auto":
        print(
            f"  → Median ({np.median(snr_db):.1f} dB) + Margin ({args.threshold_margin:.1f} dB)"
        )

    print(f"\nSignificant frequency bands (Movement > {threshold:.1f} dB above Rest):")
    if sig_bands:
        total_bandwidth = 0
        for f_start, f_end, avg_snr in sig_bands:
            bandwidth = f_end - f_start
            total_bandwidth += bandwidth
            print(
                f"  {f_start:5.1f} - {f_end:5.1f} Hz  "
                f"(BW: {bandwidth:4.1f} Hz, SNR: {avg_snr:5.1f} dB)"
            )
        print(f"\nTotal bandwidth: {total_bandwidth:.1f} Hz")

        # Suggest filter parameters (prefer lowpass for real-time)
        if sig_bands:
            min_freq = sig_bands[0][0]
            max_freq = sig_bands[-1][1]

            # Primary recommendation: Lowpass (simpler for real-time)
            print("\nRecommended filter for real-time:")
            print(f"  Lowpass: {max_freq:.1f} Hz")

            # Only suggest bandpass if there's a significant low-freq gap
            if min_freq > 1.0:
                print(
                    f"  Alternative (if low-freq noise is issue): Bandpass {min_freq:.1f} - {max_freq:.1f} Hz"
                )
    else:
        print(f"  No bands found above {threshold:.1f} dB threshold")
        print("  → Try lower --snr-threshold or --threshold-margin")

    print("\n" + "-" * 70)
    print("Reference: Typical hand movement frequencies")
    print("-" * 70)
    print("  Voluntary hand motion:    0.5 - 5 Hz")
    print("  Fast intentional motion:  up to 8 Hz")
    print("  Physiological tremor:     8 - 12 Hz")

    # Create figure with 3 subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))

    # Plot 1: PSD comparison
    ax1.semilogy(freq_m, psd_m_total, label="Movement", color="C0")
    ax1.semilogy(freq_r, psd_r_total, label="Rest", color="C3")

    ax1.set_xlabel("Frequency [Hz]")
    ax1.set_ylabel("PSD [$(m/s^2)^2$/Hz]")
    ax1.set_title("Power Spectral Density")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, freq_m[-1])

    # Plot 2: SNR in dB
    ax2.plot(freq_m, snr_db, color="C2", label="SNR")
    ax2.axhline(
        threshold,
        color="red",
        linestyle="--",
        linewidth=1.5,
        label=f"Threshold ({threshold:.1f} dB, {threshold_mode})",
    )
    ax2.axhline(
        np.median(snr_db),
        color="orange",
        linestyle=":",
        linewidth=1.5,
        alpha=0.7,
        label=f"Median SNR ({np.median(snr_db):.1f} dB)",
    )
    ax2.axhline(0, color="gray", linestyle=":", alpha=0.5)

    ax2.set_xlabel("Frequency [Hz]")
    ax2.set_ylabel("SNR [dB]")
    ax2.set_title("Signal-to-Noise Ratio")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, freq_m[-1])

    # Plot 3: Absolute difference
    ax3.plot(freq_m, psd_diff, color="C4")
    ax3.axhline(0, color="gray", linestyle=":", alpha=0.5)

    ax3.set_xlabel("Frequency [Hz]")
    ax3.set_ylabel("PSD Difference [$(m/s^2)^2$/Hz]")
    ax3.set_title("Movement - Rest")
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, freq_m[-1])

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
