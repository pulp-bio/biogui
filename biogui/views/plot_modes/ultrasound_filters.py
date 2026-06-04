# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Class for filtering ultrasound.
"""

from __future__ import annotations

import numpy as np
from scipy import signal as ss
from scipy.signal import hilbert


class UltrasoundFilter:
    """
    Bandpass filter and envelope detector for ultrasound signals.

    Online/runtime convention
    -------------------------
    Online data uses axis=0 as sample axis.

    Expected shapes:
    - (n_samples,)
    - (n_samples, n_channels)

    Offline/post-acquisition convention
    -----------------------------------
    Post-acquisition data uses axis=-1 as sample axis.

    Expected shapes:
    - (n_samples,)
    - (..., n_samples)

    Example:
    - (76, 397) means 76 independent waveforms, each with 397 samples.
    """

    def __init__(
        self,
        sampling_freq: float,
        low_cutoff: float,
        high_cutoff: float,
        trans_width: float = 0.2e6,
        n_taps: int = 31,
        enabled: bool = True,
    ) -> None:
        self._sampling_freq = sampling_freq
        self._low_cutoff = low_cutoff
        self._high_cutoff = high_cutoff
        self._trans_width = trans_width
        self._n_taps = n_taps
        self._enabled = enabled

        self._filt_b: np.ndarray | None = None
        self._filt_a = 1

        if self._enabled:
            self._design_filter()

    def _design_filter(self) -> None:
        """Design bandpass filter using Remez algorithm."""
        if not self._enabled:
            return

        nyquist = self._sampling_freq / 2.0

        low_stop = self._low_cutoff - self._trans_width
        high_stop = self._high_cutoff + self._trans_width

        if low_stop < 0:
            print(f"Warning: Lower transition band is negative ({low_stop / 1e6:.3f} MHz).")
            print(
                f"  Low cutoff: {self._low_cutoff / 1e6:.3f} MHz, "
                f"Transition width: {self._trans_width / 1e6:.3f} MHz"
            )
            print("  Adjusting low_stop to 0 Hz...")
            low_stop = 0.0

        if high_stop > nyquist:
            print(
                f"Warning: Upper transition band exceeds Nyquist "
                f"({high_stop / 1e6:.3f} MHz > {nyquist / 1e6:.3f} MHz)."
            )
            print("  Adjusting high_stop to Nyquist...")
            high_stop = nyquist

        bands = [0.0, low_stop, self._low_cutoff, self._high_cutoff, high_stop, nyquist]

        for i in range(len(bands) - 1):
            if bands[i] >= bands[i + 1]:
                print("Error: Non-monotonic filter bands. Filter disabled.")
                print(f"  Bands: {[f'{f / 1e6:.3f} MHz' for f in bands]}")
                self._enabled = False
                self._filt_b = None
                return

        print(f"Designing filter with bands: {[f'{f / 1e6:.3f} MHz' for f in bands]}")

        try:
            self._filt_b = ss.remez(
                self._n_taps,
                bands,
                [0, 1, 0],
                fs=self._sampling_freq,
                maxiter=2500,
            )
            print(f"Filter designed successfully. Gain at passband: {np.sum(self._filt_b):.3f}")
        except Exception as exc:
            print(f"Error: Filter design failed: {exc}")
            self._enabled = False
            self._filt_b = None

    # -------------------------------------------------------------------------
    # Online / runtime API
    # -------------------------------------------------------------------------

    def filter_data(self, data_in: np.ndarray) -> np.ndarray:
        """
        Apply bandpass filter to online/runtime data.

        Online convention:
        - sample axis is axis=0

        Expected shapes:
        - (n_samples,)
        - (n_samples, n_channels)
        """
        if not self._enabled or self._filt_b is None:
            return data_in

        return ss.filtfilt(
            self._filt_b,
            self._filt_a,
            data_in,
            axis=0,
        )

    @staticmethod
    def get_envelope(data_in: np.ndarray) -> np.ndarray:
        """
        Calculate envelope for online/runtime data.

        Online convention:
        - sample axis is axis=0
        """
        return np.abs(hilbert(data_in, axis=0))

    @staticmethod
    def apply_log_compression(data: np.ndarray, dynamic_range: float = 40.0) -> np.ndarray:
        """
        Apply B-mode style log compression globally.

        This keeps the original online behavior:
        one global peak is used for normalization.
        """
        amplitude = np.abs(data).astype(np.float64)
        amplitude = np.where(np.isfinite(amplitude), amplitude, 0.0)

        peak = float(np.max(amplitude))

        if peak <= 0.0 or not np.isfinite(peak):
            return np.zeros_like(data, dtype=np.float64)

        if dynamic_range >= 1.0:
            compressed = np.zeros_like(amplitude, dtype=np.float64)
            positive = amplitude > 0.0
            compressed[positive] = (
                20.0 * np.log10(amplitude[positive] / peak) + dynamic_range
            )
            compressed = 255.0 * compressed / dynamic_range
        else:
            compressed = np.power(amplitude / peak, dynamic_range) * 255.0

        return np.clip(compressed, 0.0, 255.0)

    # -------------------------------------------------------------------------
    # Offline / post-acquisition API
    # -------------------------------------------------------------------------

    def filter_data_postacq(self, data_in: np.ndarray) -> np.ndarray:
        """
        Apply bandpass filter independently to each post-acquisition waveform.

        Offline convention:
        - sample axis is axis=-1

        Expected shapes:
        - (n_samples,)
        - (..., n_samples)

        Example:
        - (76, 397): 76 independent waveforms, each with 397 samples.
        """
        if not self._enabled or self._filt_b is None:
            return data_in

        return ss.filtfilt(
            self._filt_b,
            self._filt_a,
            data_in,
            axis=-1,
        )

    @staticmethod
    def get_envelope_postacq(data_in: np.ndarray) -> np.ndarray:
        """
        Calculate envelope independently for each post-acquisition waveform.

        Offline convention:
        - sample axis is axis=-1
        """
        return np.abs(hilbert(data_in, axis=-1))

    @staticmethod
    def apply_log_compression_postacq(
        data: np.ndarray,
        dynamic_range: float = 40.0,
        normalize_per_waveform: bool = True,
    ) -> np.ndarray:
        """
        Apply B-mode style log compression to post-acquisition data.

        Offline convention:
        - sample axis is axis=-1

        If normalize_per_waveform=True:
        - each waveform is normalized independently along the last axis.

        If normalize_per_waveform=False:
        - one global peak is used for the full array.
        """
        amplitude = np.abs(data).astype(np.float64)
        amplitude = np.where(np.isfinite(amplitude), amplitude, 0.0)

        if normalize_per_waveform:
            peak = np.max(amplitude, axis=-1, keepdims=True)
        else:
            peak = np.max(amplitude)

        valid = np.isfinite(peak) & (peak > 0.0)
        safe_peak = np.where(valid, peak, 1.0)

        ratio = amplitude / safe_peak

        if dynamic_range >= 1.0:
            compressed = np.zeros_like(amplitude, dtype=np.float64)
            positive = ratio > 0.0

            compressed[positive] = (
                20.0 * np.log10(ratio[positive]) + dynamic_range
            )
            compressed = 255.0 * compressed / dynamic_range
        else:
            compressed = np.power(ratio, dynamic_range) * 255.0

        compressed = np.where(valid, compressed, 0.0)

        return np.clip(compressed, 0.0, 255.0)

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        """Check if filter is enabled."""
        return self._enabled

    def update_parameters(
        self,
        low_cutoff: float | None = None,
        high_cutoff: float | None = None,
        enabled: bool | None = None,
    ) -> None:
        """
        Update filter parameters and re-design if necessary.
        """
        redesign = False

        if enabled is not None and enabled != self._enabled:
            self._enabled = enabled
            redesign = True

        if low_cutoff is not None and low_cutoff != self._low_cutoff:
            self._low_cutoff = low_cutoff
            redesign = True

        if high_cutoff is not None and high_cutoff != self._high_cutoff:
            self._high_cutoff = high_cutoff
            redesign = True

        if redesign and self._enabled:
            self._design_filter()