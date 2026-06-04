"""
Ultrasound post-run plotting for collected .bio files.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .bio_file_utils import LoadedBioFile, find_latest_bio_file, load_bio_file
from .registry import register_plotter
from biogui.views.plot_modes.ultrasound_filters import UltrasoundFilter


SPEED_OF_SOUND = 1540.0  # in m/s, typical for soft tissue
def _build_runtime_dataframe(loaded: LoadedBioFile) -> pd.DataFrame:
    signals = loaded.signals

    if "imu" in signals:
        samples_per_acquisition = 397
    else:
        samples_per_acquisition = 400

    counter_values = np.hstack(signals["acquisition_number"]["data"]).astype(int)
    rx_ids = np.hstack(signals["tx_rx_id"]["data"]).astype(int)

    if "imu" in signals:
        imu_data = signals["imu"]["data"]
    if "trigger" in signals:
        trigger_data = np.hstack(signals["trigger"]["data"])
    if "trigger_str" in signals:
        trigger_data_str = np.hstack(signals["trigger_str"]["data"])

    n_total = int(counter_values[-1] + 1)
    full_tx_rx_id = np.full(n_total, np.nan)
    full_tx_rx_id[counter_values] = rx_ids

    if "trigger" in signals:
        trigger_data_full = np.full(n_total, np.nan)
        trigger_data_full[counter_values] = trigger_data

    if "trigger_str" in signals:
        trigger_str_full = np.full(n_total, "", dtype=object)
        trigger_str_full[counter_values] = trigger_data_str

    if "imu" in signals:
        imu_x_full = np.full(n_total, np.nan)
        imu_y_full = np.full(n_total, np.nan)
        imu_z_full = np.full(n_total, np.nan)

        imu_x_full[counter_values] = imu_data[:, 0]
        imu_y_full[counter_values] = imu_data[:, 1]
        imu_z_full[counter_values] = imu_data[:, 2]

    if n_total != len(counter_values):
        print("Data losses detected.")

    df_session = pd.DataFrame()

    for sig_name, sig_data in signals.items():
        if sig_name in {
            "timestamp",
            "trigger",
            "trigger_str",
            "imu",
            "acquisition_number",
            "tx_rx_id",
        }:
            continue

        rx_data = sig_data["data"]
        n_samp, _ = rx_data.shape

        n_acq = n_samp // samples_per_acquisition
        if n_acq == 0:
            print(f"Warning: signal '{sig_name}' skipped, not enough samples.")
            continue

        trunc = n_acq * samples_per_acquisition
        data_reshaped = rx_data[:trunc, :].reshape(n_acq, samples_per_acquisition)

        us_id = int(sig_name[-1])
        counter_curr = counter_values[rx_ids == us_id]

        n = min(len(counter_curr), len(data_reshaped))
        counter_curr = counter_curr[:n]
        data_reshaped = data_reshaped[:n]

        if n == 0:
            continue

        diffs = np.diff(counter_curr)
        if len(diffs) == 0:
            step = 1
        else:
            step = int(pd.Series(diffs).mode().iloc[0])

        if np.any(diffs != step):
            print(f"Data losses for {sig_name}, expected step={step}")

        series = pd.Series(
            list(data_reshaped),
            index=counter_curr,
            name=f"tx_{us_id}",
        )
        series = series[~series.index.duplicated(keep="first")]

        start = int(series.index.min())
        end = int(series.index.max())
        full_counter = np.arange(start, end + step, step)

        nan_waveform = np.full(samples_per_acquisition, np.nan)
        series = series.reindex(full_counter, fill_value=nan_waveform)

        df_session = pd.concat([df_session, series.to_frame()], axis=1)

    df_session = df_session.sort_index()

    if "trigger" in signals:
        df_session["Label"] = trigger_data_full[: len(df_session)]
    if "trigger_str" in signals:
        df_session["Label_str"] = trigger_str_full[: len(df_session)]
    if "imu" in signals:
        df_session["imu_x"] = imu_x_full[: len(df_session)]
        df_session["imu_y"] = imu_y_full[: len(df_session)]
        df_session["imu_z"] = imu_z_full[: len(df_session)]

    df_session["rx_id"] = full_tx_rx_id[: len(df_session)]

    return df_session




_NON_CHANNEL_COLUMNS = {
    "Label",
    "Label_str",
    "imu_x",
    "imu_y",
    "imu_z",
    "rx_id",
    "timestamp",
    "trigger",
    "trigger_str",
}


def _resolve_enabled_channels(
    dataframe: pd.DataFrame,
    plot_options: dict | None,
) -> list[str]:
    channel_columns = [
        column for column in dataframe.columns if column not in _NON_CHANNEL_COLUMNS
    ]

    if not plot_options:
        return channel_columns

    enabled_channels = plot_options.get("enabledChannels")

    if isinstance(enabled_channels, dict):
        filtered = [
            column for column in channel_columns if enabled_channels.get(column, True)
        ]
        return filtered or channel_columns

    if isinstance(enabled_channels, (list, tuple, set)):
        filtered = [column for column in channel_columns if column in enabled_channels]
        return filtered or channel_columns

    return channel_columns



def _depth_axis_mm(adc_start_delay_s: float, num_samples: int, adc_sampling_freq: float) -> tuple[float, float]:
    """Calculate depth axis limits in mm.

    adc_start_delay_s : delay from pulse to first ADC sample, in seconds.
    """
    axis_start = (SPEED_OF_SOUND * adc_start_delay_s / 2) * 1e3
    axis_stop = (SPEED_OF_SOUND * (adc_start_delay_s + num_samples / adc_sampling_freq) / 2) * 1e3
    return axis_start, axis_stop

def _get_processing_config(
    plot_options: dict | None,
    ) -> tuple[float, float, bool, bool, float,float,float]:
    if not plot_options:
        return 0.0, 0.0, False, True, 0.45, 33.33, 5.0/1e6

    transmission_freq = float(plot_options.get("transmissionFrequencyHz", 0.0) or 0.0)
    adc_sampling_freq = float(plot_options.get("adcSamplingFreqHz", 0.0) or 0.0)
    bandwidth_fraction = float(plot_options.get("bandwidthFraction", 0.45) or 0.45)
    apply_bandpass = bool(plot_options.get("enableBandpass", True))
    apply_envelope = bool(plot_options.get("showEnvelope", True))
    meas_period = int(plot_options.get("meas_period", 33.33))           # in microseconds
    start_pgg = int(plot_options.get("start_ppg", 500))
    adc_start_delay = int(plot_options.get("start_adcsampl", 505))
    adc_delay = adc_start_delay - start_pgg

    return (
        transmission_freq,
        adc_sampling_freq,
        apply_bandpass,
        apply_envelope,
        bandwidth_fraction,
        meas_period/1000,               # meas period in ms
        adc_delay/1e6,     # adc delay in seconds
    )


def _build_filter(plot_options: dict | None) -> UltrasoundFilter | None:
    (
        transmission_freq,
        adc_sampling_freq,
        apply_bandpass,
        _,
        bandwidth_fraction,
        meas_period, 
        adc_start_delay,
    ) = _get_processing_config(plot_options)

    if not apply_bandpass or transmission_freq <= 0.0 or adc_sampling_freq <= 0.0:
        return None

    half_band = max(transmission_freq * bandwidth_fraction / 2.0, 1.0)
    low_cutoff = max(0.0, transmission_freq - half_band)
    high_cutoff = min(adc_sampling_freq / 2.0, transmission_freq + half_band)

    print(f"Calculated low cutoff frequency: {low_cutoff:.2f}")
    print(f"Calculated high cutoff frequency: {high_cutoff:.2f}")

    if low_cutoff >= high_cutoff:
        return None

    return UltrasoundFilter(
        sampling_freq=adc_sampling_freq,
        low_cutoff=low_cutoff,
        high_cutoff=high_cutoff,
        enabled=True,
    )


def _process_waveforms(
    waveforms: np.ndarray,
    plot_options: dict | None,
) -> np.ndarray:
    """
    Apply ultrasound preprocessing.

    Expected input shape:
    - (n_frames, n_depth_samples)

    The last axis is the 397-sample waveform axis.
    """
    print("Processing waveforms with shape", waveforms.shape)

    filter_instance = _build_filter(plot_options)
    _, _, _, apply_envelope, _, _,_ = _get_processing_config(plot_options)

    processed = np.asarray(waveforms, dtype=float)

    if filter_instance is not None:
        processed = filter_instance.filter_data_postacq(processed)

    if apply_envelope:
        processed = UltrasoundFilter.get_envelope_postacq(processed)

    return processed




def plot_latest_ultrasound_run(
    runtime_dir: Path | None = None,
    plot_options: dict | None = None,
) -> Path | None:
    bio_file = find_latest_bio_file(runtime_dir)

    if bio_file is None:
        print("No .bio file found for post-run plotting.")
        return None

    plot_file(bio_file, plot_options)
    return bio_file


# Module-level list that keeps PostRunPlotWindow instances alive after plot_file returns.
_active_windows: list = []


def plot_file(
    file_path: Path,
    plot_options: dict | None = None,
) -> pd.DataFrame:
    """Load, process and display a .bio file in the Qt post-run window."""
    from .post_run_dialog import PostRunPlotWindow

    loaded = load_bio_file(file_path)
    dataframe = _build_runtime_dataframe(loaded)

    print("Built dataframe with len", len(dataframe), "and columns", list(dataframe.columns))

    channel_columns = _resolve_enabled_channels(dataframe, plot_options)
    print("Resolved channel columns:", channel_columns)

    # ── collect raw matrices (no processing — dialog handles it) ────
    raw_matrices: dict[str, np.ndarray] = {}
    for col in channel_columns:
        us_curr = dataframe[col].dropna()
        if us_curr.empty:
            continue
        raw_matrices[col] = np.vstack(us_curr.to_numpy())  # (n_frames, n_depth)

    if not raw_matrices:
        print(f"No ultrasound data to display for {file_path.name}")
        return dataframe

    # ── compute physical axes ────────────────────────────────────────
    _, adc_sampling_freq, _, _, _, meas_period_ms, adc_start_delay_s = _get_processing_config(plot_options)

    n_depth = next(iter(raw_matrices.values())).shape[1]
    depth_start_mm, depth_stop_mm = _depth_axis_mm(adc_start_delay_s, n_depth, adc_sampling_freq)
    print("Depth axis (mm):", depth_start_mm, "→", depth_stop_mm)

    num_us_channels = len(raw_matrices)
    meas_period_ms_per_channel = meas_period_ms * num_us_channels

    # ── launch Qt window ─────────────────────────────────────────────
    window = PostRunPlotWindow(
        file_path=file_path,
        raw_matrices=raw_matrices,
        depth_start_mm=depth_start_mm,
        depth_stop_mm=depth_stop_mm,
        meas_period_ms_per_channel=meas_period_ms_per_channel,
        meas_period_ms_global=meas_period_ms,
        dataframe=dataframe,
        plot_options=plot_options,
    )
    _active_windows.append(window)
    window.destroyed.connect(
        lambda: _active_windows.remove(window) if window in _active_windows else None
    )
    window.show()

    return dataframe


class UltrasoundPostRunPlotter:
    """Convenience wrapper for ultrasound post-run plotting."""

    def plot_latest(
        self,
        runtime_dir: Path | None = None,
        plot_options: dict | None = None,
    ) -> Path | None:
        return plot_latest_ultrasound_run(runtime_dir, plot_options)

    def plot_file(
        self,
        file_path: Path,
        plot_options: dict | None = None,
    ) -> pd.DataFrame:
        return plot_file(file_path, plot_options)


register_plotter("ultrasound", plot_latest_ultrasound_run)

