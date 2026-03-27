# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Classes for signal filtering.
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
    def isEnabled(self) -> bool:
        """Check if any processing is enabled."""
        pass


class TimeSeriesFilter(SignalFilter):
    """
    Filter for time-series signals (EEG, ECG, etc.).

    Parameters
    ----------
    fs : float
        Sampling frequency.
    nCh : int
        Number of channels.

    Attributes
    ----------
    _fs : float
        Sampling frequency.
    _nCh : int
        Number of channels.
    _sosButter : ndarray or None
        Butterworth filter SOS (second-order sections).
    _ziButter : ndarray or None
        Butterworth filter initial conditions.
    _baNotch : tuple or None
        Notch filter coefficients (b, a).
    _ziNotch : ndarray or None
        Notch filter initial conditions.
    """

    def __init__(self, fs: float, nCh: int) -> None:
        self._fs = fs
        self._nCh = nCh
        self._sosButter = None
        self._ziButter = None
        self._baNotch = None
        self._ziNotch = None

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
            self._sosButter = None
            self._ziButter = None
        else:
            freqs = sigConfig["freqs"]
            self._sosButter = scipy.signal.butter(
                N=sigConfig["filtOrder"],
                Wn=freqs if len(freqs) > 1 else freqs[0],
                fs=self._fs,
                btype=sigConfig["filtType"],
                output="sos",
            )
            self._ziButter = np.stack(
                [scipy.signal.sosfilt_zi(self._sosButter) for _ in range(self._nCh)],
                axis=-1,
            )

        # 2. Notch filter
        if "notchFreq" not in sigConfig:
            self._baNotch = None
            self._ziNotch = None
        else:
            b, a = scipy.signal.iirnotch(
                w0=sigConfig["notchFreq"],
                Q=sigConfig["qFactor"],
                fs=self._fs,
            )
            self._baNotch = (b, a)
            self._ziNotch = np.stack(
                [scipy.signal.lfilter_zi(b, a) for _ in range(self._nCh)],
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
        dataFilt = data.copy()

        # Apply Butterworth filter
        if self._sosButter is not None and self._ziButter is not None:
            dataFilt, self._ziButter = scipy.signal.sosfilt(
                self._sosButter,
                dataFilt,
                axis=0,
                zi=self._ziButter,
            )

        # Apply Notch filter
        if self._baNotch is not None and self._ziNotch is not None:
            dataFilt, self._ziNotch = scipy.signal.lfilter(
                *self._baNotch,
                dataFilt,
                axis=0,
                zi=self._ziNotch,
            )

        return dataFilt

    def isEnabled(self) -> bool:
        """Check if any filter is active."""
        return self._sosButter is not None or self._baNotch is not None


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

    def isEnabled(self) -> bool:
        """Passthrough filter is never enabled."""
        return False


def createFilter(extras: dict, fs: float, nCh: int) -> SignalFilter:
    """
    Factory function to create appropriate filter based on signal type.

    Parameters
    ----------
    extras : dict
        Dictionary containing a "type" key (either "time-series" or "ultrasound")
    fs : float
        Sampling frequency (measurement rate for ultrasound, actual fs for time-series).
    nCh : int
        Number of channels.

    Returns
    -------
    SignalFilter
        Appropriate filter instance.
    """
    signalType = extras.get("type", "time-series")

    if signalType == "ultrasound":
        # Ultrasound signals: no preprocessing filtering
        # Filtering happens in plot modes (A-mode, M-mode)
        return PassthroughFilter()
    else:
        # Time-series signals: apply Butterworth/Notch filters
        return TimeSeriesFilter(fs, nCh)
