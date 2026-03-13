"""
Classes for signal filtering.

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

from abc import ABC, abstractmethod

import numpy as np
import scipy.signal


class SignalFilter(ABC):
    """
    Abstract base class for signal filters.

    This defines the interface that all signal filters must implement.
    """

    @abstractmethod
    def configure(self, sigConfig: dict) -> None:
        """
        Configure the filter from signal configuration.

        Parameters
        ----------
        sigConfig : dict
            Signal configuration dictionary.
        """
        pass

    @abstractmethod
    def process(self, data: np.ndarray) -> np.ndarray:
        """
        Apply filtering/processing to data.

        Parameters
        ----------
        data : ndarray
            Input data with shape (nSamp, nCh).

        Returns
        -------
        ndarray
            Processed data with same shape as input.
        """
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if any processing is enabled."""
        pass


class TimeSeriesFilter(SignalFilter):
    """
    Filter for time-series signals (EEG, ECG, etc.).

    Parameters
    ----------
    fs : float
        Sampling frequency.
    n_ch : int
        Number of channels.

    Attributes
    ----------
    _fs : float
        Sampling frequency.
    _n_ch : int
        Number of channels.
    _sos_butter : ndarray or None
        Butterworth filter SOS (second-order sections).
    _zi_butter : ndarray or None
        Butterworth filter initial conditions.
    _ba_notch : tuple or None
        Notch filter coefficients (b, a).
    _zi_notch : ndarray or None
        Notch filter initial conditions.
    """

    def __init__(self, fs: float, n_ch: int) -> None:
        self._fs = fs
        self._n_ch = n_ch
        self._sos_butter = None
        self._zi_butter = None
        self._ba_notch = None
        self._zi_notch = None

    def configure(self, sigConfig: dict) -> None:
        """
        Configure Butterworth and Notch filters from config.

        Parameters
        ----------
        sigConfig : dict
            Configuration with optional keys:
            - "filtType": Filter type (highpass, lowpass, bandpass, bandstop)
            - "freqs": List of cutoff frequencies
            - "filtOrder": Filter order
            - "notchFreq": Notch filter frequency
            - "qFactor": Notch filter quality factor
        """
        # 1. Butterworth filter
        if "filtType" not in sigConfig:
            self._sos_butter = None
            self._zi_butter = None
        else:
            freqs = sigConfig["freqs"]
            self._sos_butter = scipy.signal.butter(
                N=sigConfig["filtOrder"],
                Wn=freqs if len(freqs) > 1 else freqs[0],
                fs=self._fs,
                btype=sigConfig["filtType"],
                output="sos",
            )
            self._zi_butter = np.stack(
                [scipy.signal.sosfilt_zi(self._sos_butter) for _ in range(self._n_ch)],
                axis=-1,
            )

        # 2. Notch filter
        if "notchFreq" not in sigConfig:
            self._ba_notch = None
            self._zi_notch = None
        else:
            b, a = scipy.signal.iirnotch(
                w0=sigConfig["notchFreq"],
                Q=sigConfig["qFactor"],
                fs=self._fs,
            )
            self._ba_notch = (b, a)
            self._zi_notch = np.stack(
                [scipy.signal.lfilter_zi(b, a) for _ in range(self._n_ch)],
                axis=-1,
            )

    def process(self, data: np.ndarray) -> np.ndarray:
        """
        Apply IIR filters with state preservation.

        Parameters
        ----------
        data : ndarray
            Input data with shape (nSamp, nCh).

        Returns
        -------
        ndarray
            Filtered data with same shape.
        """
        processed_data = data.copy()

        # Apply Butterworth filter
        if self._sos_butter is not None and self._zi_butter is not None:
            processed_data, self._zi_butter = scipy.signal.sosfilt(
                self._sos_butter,
                processed_data,
                axis=0,
                zi=self._zi_butter,
            )

        # Apply Notch filter
        if self._ba_notch is not None and self._zi_notch is not None:
            processed_data, self._zi_notch = scipy.signal.lfilter(
                *self._ba_notch,
                processed_data,
                axis=0,
                zi=self._zi_notch,
            )

        return processed_data

    def is_enabled(self) -> bool:
        """Check if any filter is active."""
        return (self._sos_butter is not None) or (self._ba_notch is not None)


class PassthroughFilter(SignalFilter):
    """
    Passthrough filter that returns data unchanged.

    Used for signal types that don't require preprocessing filtering,
    such as ultrasound signals where filtering is handled in the
    visualization layer.
    """

    def configure(self, sigConfig: dict) -> None:
        """No-op configuration."""
        pass

    def process(self, data: np.ndarray) -> np.ndarray:
        """Return data unchanged."""
        return data

    def is_enabled(self) -> bool:
        """Passthrough filter is never enabled."""
        return False


def create_filter(signal_type_info: dict, fs: float, n_ch: int) -> SignalFilter:
    """
    Factory function to create appropriate filter based on signal type.

    Parameters
    ----------
    signal_type_info : dict
        Signal type information with:
        - "type": "time-series" or "ultrasound"
    fs : float
        Sampling frequency (measurement rate for ultrasound, actual fs for time-series).
    n_ch : int
        Number of channels.

    Returns
    -------
    SignalFilter
        Appropriate filter instance.
    """
    signal_type = signal_type_info.get("type", "time-series")

    if signal_type == "ultrasound":
        # Ultrasound signals: no preprocessing filtering
        # Filtering happens in plot modes (A-mode, M-mode)
        return PassthroughFilter()
    else:
        # Time-series signals: apply Butterworth/Notch filters
        return TimeSeriesFilter(fs, n_ch)
