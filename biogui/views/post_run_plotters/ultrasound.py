"""
Ultrasound post-run plotting for collected .bio files.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
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


def _plot_trigger_row(axis, dataframe: pd.DataFrame, time_axis: np.ndarray) -> None:
    x_axis = time_axis

    if "Label" in dataframe.columns:
        axis.plot(
            x_axis,
            dataframe["Label"].to_numpy(dtype=float, copy=False),
            label="trigger",
        )
        axis.legend(loc="best")

    axis.set_ylabel("Trigger")
    axis.set_xlim(x_axis[0], x_axis[-1])


def _plot_trigger_string_row(axis, dataframe: pd.DataFrame, time_axis: np.ndarray) -> None:
    x_axis = time_axis
    codes, labels = pd.factorize(dataframe["Label_str"], sort=True)

    axis.plot(x_axis, codes.astype(float), label="trigger_str")
    axis.legend(loc="best")
    axis.set_yticks(np.arange(len(labels)))
    axis.set_yticklabels([str(label) for label in labels])
    axis.set_ylabel("Trigger str")
    axis.set_xlim(x_axis[0], x_axis[-1])


def _plot_imu_row(axis, dataframe: pd.DataFrame, time_axis: np.ndarray) -> None:
    x_axis = time_axis
    plotted = False

    for imu_column in ("imu_x", "imu_y", "imu_z"):
        if imu_column in dataframe.columns:
            axis.plot(
                x_axis,
                dataframe[imu_column].to_numpy(dtype=float, copy=False),
                label=imu_column,
            )
            plotted = True

    if plotted:
        axis.set_title("IMU Data")
        axis.legend(loc="best")
        axis.set_xlim(x_axis[0], x_axis[-1])
    else:
        axis.set_title("IMU Data (missing)")

    axis.set_ylabel("IMU")


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


def _plot_amode(
    dataframe: pd.DataFrame,
    channel_columns: list[str],
    plot_options: dict | None,
) -> pd.DataFrame:
    n_frames = len(dataframe)

    if n_frames == 0 or not channel_columns:
        plt.figure(figsize=(10, 4))
        plt.title("A-mode (no data)")
        plt.show()
        return dataframe

    figure, axes = plt.subplots(
        nrows=len(channel_columns),
        sharex=False,
        figsize=(18, max(1, len(channel_columns)) * 4),
        layout="constrained",
    )

    if not isinstance(axes, np.ndarray):
        axes = np.array([axes])

    waveform_matrices: list[np.ndarray] = []
    lines = []

    for axis, channel_name in zip(axes, channel_columns):
        waveforms = dataframe[channel_name].dropna()

        if waveforms.empty:
            axis.set_title(f"{channel_name} empty")
            axis.axis("off")
            waveform_matrices.append(np.empty((0, 0)))
            lines.append(None)
            continue

        values = waveforms.to_numpy()
        matrix = np.vstack(values)  # shape: (n_frames, n_depth_samples)

        processed = _process_waveforms(matrix, plot_options)
        waveform_matrices.append(processed)

        line, = axis.plot(
            np.arange(processed.shape[1]),
            processed[0, :],
            label=f"{channel_name} @ t=0",
        )

        axis.set_title(channel_name)
        axis.set_ylabel("Amplitude")
        axis.legend(loc="best")
        lines.append(line)

    slider_axis = figure.add_axes([0.15, 0.03, 0.7, 0.03])
    slider = Slider(
        slider_axis,
        "Time",
        0,
        max(0, n_frames - 1),
        valinit=0,
        valstep=1,
    )

    def _update(selected_index: float) -> None:
        index = int(selected_index)

        for line, matrix in zip(lines, waveform_matrices):
            if line is None or matrix.size == 0:
                continue

            row = min(index, matrix.shape[0] - 1)
            line.set_ydata(matrix[row, :])
            line.set_label(f"{line.get_label().split(' @ t=')[0]} @ t={row}")

        for axis in axes:
            axis.relim()
            axis.autoscale_view()
            axis.legend(loc="best")

        figure.canvas.draw_idle()

    slider.on_changed(_update)
    plt.show()

    return dataframe


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


def plot_file(
    file_path: Path,
    plot_options: dict | None = None,
) -> pd.DataFrame:
    loaded = load_bio_file(file_path)
    dataframe = _build_runtime_dataframe(loaded)

    print("Built dataframe with len", len(dataframe), "and columns", list(dataframe.columns))

    display_mode = (plot_options or {}).get("displayMode", "mmode").lower()
    print("Plotting in display mode:", display_mode)

    channel_columns = _resolve_enabled_channels(dataframe, plot_options)
    print("Resolved channel columns for plotting:", channel_columns)

    has_imu = any(column in dataframe.columns for column in ("imu_x", "imu_y", "imu_z"))

    if display_mode == "amode":
        _plot_amode(dataframe, channel_columns, plot_options)
        return dataframe

    processed_columns: list[str] = []
    processed_matrices: dict[str, np.ndarray] = {}

    for col in channel_columns:

        ## TO-DO:add option for MISSING values check!
        us_curr = dataframe[col].dropna()

        if us_curr.empty:
            continue

        values = us_curr.to_numpy()
        values_stacked = np.vstack(values)  # shape: (n_frames, n_depth_samples)

        processed = _process_waveforms(values_stacked, plot_options)

        processed_columns.append(col)
        processed_matrices[col] = processed.T  # shape: (n_depth_samples, n_frames)

    extra_rows = int(has_imu)
    extra_rows += int("Label" in dataframe.columns)
    extra_rows += int("Label_str" in dataframe.columns)

    num_us_channels = len(processed_columns)
    n_rows = max(1, len(processed_columns) + extra_rows)

    #for the time axis
    _, adc_sampling_freq, _, _, _, meas_period, adc_start_delay_s = _get_processing_config(plot_options)
    # adc_start_delay_s already in seconds; n_samples is constant across channels
    n_samples = next(
        (dataframe[col].dropna().iloc[0].size for col in channel_columns if not dataframe[col].dropna().empty),
        400,
    )
    depth_axis_start, depth_axis_stop = _depth_axis_mm(adc_start_delay_s, n_samples, adc_sampling_freq)
    print("Depth axis (mm) for US", depth_axis_start, depth_axis_stop)
    meas_period_base = meas_period
    meas_period_us = meas_period_base * num_us_channels  # global period → per-channel period

    figure, axes = plt.subplots(
        nrows=n_rows,
        sharex=True,
        figsize=(18, n_rows * 4),
        layout="constrained",
    )

    if not isinstance(axes, np.ndarray):
        axes = np.array([axes])

    axis_index = 0
    time_axis_us_max = 0
    for channel_name in processed_columns:
        processed = processed_matrices[channel_name]


        # build time axis
        time_axis = np.arange(processed.shape[1]) * meas_period_us
        if(time_axis[-1]< time_axis_us_max):
            time_axis_us_max = time_axis[-1]

        axes[axis_index].imshow(
            processed,
            extent=[time_axis[0], time_axis[-1], depth_axis_start, depth_axis_stop],
            aspect="auto",
            origin="lower",
            interpolation="nearest",
            cmap="viridis",
        )
        axes[axis_index].invert_yaxis()  # shallow (small mm) at top, deep at bottom
        axes[axis_index].set_xlim(time_axis[0], time_axis[-1])
        axes[axis_index].set_title(f"{channel_name} M-mode")
        axes[axis_index].set_ylabel("Depth (mm)")
        axis_index += 1

    min_stop_time = time_axis_us_max
    if has_imu:
        time_axis_imu = np.arange(len(dataframe)) * meas_period_base
        _plot_imu_row(axes[axis_index], dataframe,time_axis_imu)
        axis_index += 1
        min_stop_time = np.min([time_axis_imu[-1], min_stop_time])

    if "Label" in dataframe.columns:
        time_axis_trigger = np.arange(len(dataframe)) * meas_period_base
        _plot_trigger_row(axes[axis_index], dataframe, time_axis_trigger)
        axis_index += 1

        min_stop_time = np.min([time_axis_trigger[-1], min_stop_time])

    if "Label_str" in dataframe.columns:
        time_axis_trigger_str = np.arange(len(dataframe)) * meas_period_base
        _plot_trigger_string_row(axes[axis_index], dataframe, time_axis_trigger_str)
        min_stop_time = np.min([time_axis_trigger_str[-1], min_stop_time])

    axes[-1].set_xlabel("Frame index")
    for ax in axes:
        ax.set_xlim(0, min_stop_time)

    figure.suptitle(file_path.name)
    plt.show()

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

