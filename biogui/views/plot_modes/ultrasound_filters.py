"""
Class for filtering ultrasound.


Copyright 2025 Enzo Baraldi

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import numpy as np
from scipy import signal as ss
from scipy.signal import hilbert


class UltrasoundFilter:
    """
    Bandpass filter and envelope detector for ultrasound signals.

    Parameters
    ----------
    sampling_freq : float
        ADC sampling frequency in Hz.
    low_cutoff : float
        Lower cutoff frequency in Hz.
    high_cutoff : float
        Upper cutoff frequency in Hz.
    trans_width : float, default=0.2e6
        Transition width in Hz.
    n_taps : int, default=31
        Number of filter taps.
    enabled : bool, default=True
        Whether filtering is enabled.

    Attributes
    ----------
    _filt_b : ndarray
        Filter coefficients (numerator).
    _filt_a : int or ndarray
        Filter coefficients (denominator), typically 1 for FIR.
    _enabled : bool
        Whether filtering is currently enabled.
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

        self._filt_b = None
        self._filt_a = 1

        if self._enabled:
            self._design_filter()

    def _design_filter(self) -> None:
        """Design bandpass filter using Remez algorithm."""
        if not self._enabled:
            return

        nyquist = self._sampling_freq / 2

        # Build frequency bands like wulpus gui
        low_stop = self._low_cutoff - self._trans_width
        high_stop = self._high_cutoff + self._trans_width

        # Check if bands are valid
        if low_stop < 0:
            print(
                f"Warning: Lower transition band is negative ({low_stop / 1e6:.3f} MHz)."
            )
            print(
                f"  Low cutoff: {self._low_cutoff / 1e6:.3f} MHz, Transition width: {self._trans_width / 1e6:.3f} MHz"
            )
            print("  Adjusting low_stop to 0 Hz...")
            low_stop = 0

        if high_stop > nyquist:
            print(
                f"Warning: Upper transition band exceeds Nyquist ({high_stop / 1e6:.3f} MHz > {nyquist / 1e6:.3f} MHz)."
            )
            print("  Adjusting high_stop to Nyquist...")
            high_stop = nyquist

        # Verify monotonicity
        temp = [0, low_stop, self._low_cutoff, self._high_cutoff, high_stop, nyquist]

        for i in range(len(temp) - 1):
            if temp[i] >= temp[i + 1]:
                print("Error: Non-monotonic filter bands. Filter disabled.")
                print(f"  Bands: {[f'{f / 1e6:.3f} MHz' for f in temp]}")
                self._enabled = False
                return

        print(f"Designing filter with bands: {[f'{f / 1e6:.3f} MHz' for f in temp]}")

        try:
            self._filt_b = ss.remez(
                self._n_taps, temp, [0, 1, 0], fs=self._sampling_freq, maxiter=2500
            )
            print(
                f"Filter designed successfully. Gain at passband: {np.sum(self._filt_b):.3f}"
            )
        except Exception as e:
            print(f"Error: Filter design failed: {e}")
            self._enabled = False

    def filter_data(self, data_in: np.ndarray) -> np.ndarray:
        """
        Apply bandpass filter to data.

        Parameters
        ----------
        data_in : ndarray
            Input data (shape: [n_samples, n_channels] or [n_samples]).

        Returns
        -------
        ndarray
            Filtered data with same shape as input.
        """
        if not self._enabled or self._filt_b is None:
            return data_in

        return ss.filtfilt(self._filt_b, self._filt_a, data_in, axis=0)

    @staticmethod
    def get_envelope(data_in: np.ndarray) -> np.ndarray:
        """
        Calculate envelope using Hilbert transform.

        Parameters
        ----------
        data_in : ndarray
            Input data (shape: [n_samples, n_channels] or [n_samples]).

        Returns
        -------
        ndarray
            Envelope data with same shape as input.
        """
        return np.abs(hilbert(data_in, axis=0))

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

        Parameters
        ----------
        low_cutoff : float or None
            New lower cutoff frequency.
        high_cutoff : float or None
            New upper cutoff frequency.
        enabled : bool or None
            New enabled state.
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
