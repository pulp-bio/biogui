from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import scipy.signal
from scipy.signal import hilbert


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


class UltrasoundFilter(SignalFilter):
    """
    Bandpass filter and envelope detector for ultrasound RF signals.

    This is the same filter used in WULPUS GUI.

    Parameters
    ----------
    adc_sampling_freq : float
        ADC sampling frequency in Hz.

    Attributes
    ----------
    _sampling_freq : float
        ADC sampling frequency in Hz.
    _processing_mode : str
        One of: "raw", "filtered", "envelope".
    _low_cutoff : float
        Lower cutoff frequency in Hz.
    _high_cutoff : float
        Upper cutoff frequency in Hz.
    _trans_width : float
        Transition width in Hz.
    _n_taps : int
        Number of filter taps.
    _filt_b : ndarray or None
        Filter coefficients (numerator).
    _filt_a : int
        Filter coefficients (denominator), always 1 for FIR.
    """

    def __init__(self, adc_sampling_freq: float) -> None:
        self._sampling_freq = adc_sampling_freq
        self._processing_mode = "raw"
        self._low_cutoff = None
        self._high_cutoff = None
        self._trans_width = 0.2e6
        self._n_taps = 31
        self._filt_b = None
        self._filt_a = 1

    def configure(self, sigConfig: dict) -> None:
        """
        Configure ultrasound processing from config.

        Parameters
        ----------
        sigConfig : dict
            Configuration with optional key:
            - "ultrasoundFilterConfig": Dict with:
                - "processingMode": "raw", "filtered", or "envelope"
                - "lowCutoff": Low frequency cutoff in Hz
                - "highCutoff": High frequency cutoff in Hz
                - "transWidth": Transition width in Hz (optional, default 0.2 MHz)
                - "nTaps": Number of filter taps (optional, default 31)
        """
        us_config = sigConfig.get("ultrasoundFilterConfig", {})
        self._processing_mode = us_config.get("processingMode", "raw")

        # Only design filter if needed
        if self._processing_mode in ("filtered", "envelope"):
            self._low_cutoff = us_config.get("lowCutoff", self._sampling_freq * 0.1)
            self._high_cutoff = us_config.get("highCutoff", self._sampling_freq * 0.45)
            self._trans_width = us_config.get("transWidth", 0.2e6)
            self._n_taps = us_config.get("nTaps", 31)

            self._design_filter()
        else:
            self._filt_b = None

    def _design_filter(self) -> None:
        """
        Design bandpass filter using Remez algorithm.
        """
        nyquist = self._sampling_freq / 2

        # Build frequency bands (same as wulpus-gui)
        low_stop = self._low_cutoff - self._trans_width
        high_stop = self._high_cutoff + self._trans_width

        # Clamp to valid range
        if low_stop < 0:
            print(
                f"Warning: Lower transition band is negative ({low_stop / 1e6:.3f} MHz)."
            )
            print(f"  Adjusting to 0 Hz...")
            low_stop = 0

        if high_stop >= nyquist:
            print(
                f"Warning: Upper transition band meets/exceeds Nyquist "
                f"({high_stop / 1e6:.3f} MHz >= {nyquist / 1e6:.3f} MHz)."
            )
            # Leave small margin (0.1%) below Nyquist
            high_stop = nyquist * 0.999

            # If this makes high_stop <= high_cutoff, adjust high_cutoff too
            if high_stop <= self._high_cutoff:
                print(
                    f"  Adjusting high_cutoff from {self._high_cutoff / 1e6:.3f} MHz "
                    f"to {high_stop * 0.95 / 1e6:.3f} MHz"
                )
                self._high_cutoff = high_stop * 0.95

        # Build frequency array (same order as WULPUS GUI)
        temp = [0, low_stop, self._low_cutoff, self._high_cutoff, high_stop, nyquist]

        # Verify monotonicity
        for i in range(len(temp) - 1):
            if temp[i] >= temp[i + 1]:
                raise ValueError(
                    f"Non-monotonic filter bands. Bands: "
                    f"{[f'{f / 1e6:.3f} MHz' for f in temp]}"
                )

        print(f"Designing filter with bands: {[f'{f / 1e6:.3f} MHz' for f in temp]}")

        try:
            # Design filter (identical to WULPUS GUI)
            self._filt_b = scipy.signal.remez(
                self._n_taps,
                temp,
                [0, 1, 0],
                fs=self._sampling_freq,
                maxiter=2500,
            )
            print(
                f"Filter designed successfully. "
                f"Gain at passband: {np.sum(self._filt_b):.3f}"
            )
        except Exception as e:
            raise ValueError(f"Filter design failed: {e}")

    def process(self, data: np.ndarray) -> np.ndarray:
        """
        Apply ultrasound processing based on mode.

        Parameters
        ----------
        data : ndarray
            Input RF data with shape (nSamp, nCh).

        Returns
        -------
        ndarray
            Processed data (raw, filtered, or envelope).
        """
        if self._processing_mode == "raw":
            return data

        if self._filt_b is None:
            raise ValueError("Ultrasound filter not configured")

        # Apply bandpass filter (same as wulpus-gui: filtfilt)
        processed_data = scipy.signal.filtfilt(self._filt_b, self._filt_a, data, axis=0)

        # Optionally compute envelope (same as wulpus-gui: abs(hilbert))
        if self._processing_mode == "envelope":
            processed_data = np.abs(hilbert(processed_data, axis=0))

        return processed_data

    def is_enabled(self) -> bool:
        """Check if processing is enabled."""
        return self._processing_mode != "raw"


def create_filter(signal_type_info: dict, fs: float, n_ch: int) -> SignalFilter:
    """
    Factory function to create appropriate filter based on signal type.

    Parameters
    ----------
    signal_type_info : dict
        Signal type information with:
        - "type": "time-series" or "ultrasound"
        - "adc_sampling_freq": ADC sampling frequency (for ultrasound)
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
        # Use ADC sampling frequency for ultrasound
        adc_fs = signal_type_info.get("adc_sampling_freq", fs)
        return UltrasoundFilter(adc_fs)
    else:
        return TimeSeriesFilter(fs, n_ch)
