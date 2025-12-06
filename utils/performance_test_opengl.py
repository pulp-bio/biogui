#!/usr/bin/env python3
"""Performance test for OpenGL vs Software rendering in BioGUI."""

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import psutil
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QGridLayout, QMainWindow, QWidget

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from biogui.views.signal_plot_widget import SignalPlotWidget


@dataclass
class PerformanceMetrics:
    mode: str
    duration: float
    sample_rate: float
    avg_cpu: float
    max_cpu: float
    avg_memory: float

    def __str__(self):
        return (
            f"\n{'=' * 60}\n"
            f"{self.mode} Rendering\n"
            f"{'=' * 60}\n"
            f"Duration:          {self.duration:.2f} s\n"
            f"Sample Rate:       {self.sample_rate:.2f} samples/s\n"
            f"CPU (avg):         {self.avg_cpu:.2f}%\n"
            f"CPU (max):         {self.max_cpu:.2f}%\n"
            f"Memory (avg):      {self.avg_memory:.2f} MB\n"
            f"{'=' * 60}\n"
        )


class PerformanceTestWindow(QMainWindow):
    def __init__(self, use_opengl: bool, duration: float, show_gui: bool = True):
        super().__init__()

        self.use_opengl = use_opengl
        self.duration = duration
        self.show_gui = show_gui

        self.process = psutil.Process()
        self.test_start = None
        self.cpu_samples = []
        self.memory_samples = []
        self.total_samples = 0
        self.sample_accumulator = 0.0
        self.debug_counter = 0
        self.last_debug = time.time()

        self.setWindowTitle(
            f"Performance Test - {'OpenGL' if use_opengl else 'Software'}"
        )
        self.setGeometry(100, 100, 1400, 1000)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QGridLayout(central)

        self.plot_widgets = []

        for i in range(4):
            widget = self._create_plot(use_opengl, f"EMG Channel {i + 1}", 1, 128)
            self.plot_widgets.append(widget)
            layout.addWidget(widget, i // 2, i % 2)

        imu_widget = self._create_plot(
            use_opengl, "IMU Accelerometer (X, Y, Z)", 3, 128
        )
        self.plot_widgets.append(imu_widget)
        layout.addWidget(imu_widget, 2, 0, 1, 2)

        self.data_timer = QTimer(self)
        self.data_timer.setInterval(10)
        self.data_timer.timeout.connect(self._add_data)
        self.data_timer.setTimerType(Qt.TimerType.PreciseTimer)

        self.metrics_timer = QTimer(self)
        self.metrics_timer.setInterval(100)
        self.metrics_timer.timeout.connect(self._collect_metrics)

        self.stop_timer = QTimer(self)
        self.stop_timer.setSingleShot(True)
        self.stop_timer.setInterval(int(duration * 1000))
        self.stop_timer.timeout.connect(self._finish)

    def _create_plot(self, use_opengl, name, channels, fs):
        original_init = SignalPlotWidget.__init__

        def patched_init(widget_self, *args, **kwargs):
            QWidget.__init__(widget_self, kwargs.get("parent"))
            widget_self.setupUi(widget_self)

            if use_opengl:
                try:
                    from PySide6.QtOpenGLWidgets import QOpenGLWidget

                    gl_widget = QOpenGLWidget()
                    widget_self.graphWidget.setViewport(gl_widget)
                    logging.info(f"OpenGL enabled: {name}")
                except Exception as e:
                    logging.error(f"OpenGL failed: {e}")
            else:
                logging.info(f"Software rendering: {name}")

            sig_name = args[0] if args else kwargs.get("sigName", "Test")
            fs_val = args[1] if len(args) > 1 else kwargs.get("fs", 128)
            n_ch = args[2] if len(args) > 2 else kwargs.get("nCh", 4)
            spacing = args[3] if len(args) > 3 else kwargs.get("chSpacing", 1.0)
            render_len = args[4] if len(args) > 4 else kwargs.get("renderLenMs", 5000)

            widget_self._sig_name = sig_name
            widget_self._render_len_ms = render_len
            widget_self._signal_type = kwargs.get("signal_type", {})
            widget_self.label1.setText("Sampling rate:")

            from biogui.views.plot_modes import TimeSeriesPlotMode

            mode_kwargs = {
                "fs": fs_val,
                "nCh": n_ch,
                "chSpacing": spacing,
                "renderLenMs": render_len,
            }
            for key in ["signal_type", "dataQueue", "minRange", "maxRange"]:
                if key in kwargs:
                    mode_kwargs[key] = kwargs[key]

            widget_self._plot_mode = TimeSeriesPlotMode(**mode_kwargs)
            widget_self._setup_graph_widget(widget_self._sig_name)
            widget_self._plot_mode.setup_plot(widget_self.graphWidget)
            widget_self._setup_timers()

        SignalPlotWidget.__init__ = patched_init

        try:
            widget = SignalPlotWidget(
                sigName=name,
                fs=fs,
                nCh=channels,
                chSpacing=1.0,
                renderLenMs=5000,
                signal_type={"type": "time-series"},
            )
        finally:
            SignalPlotWidget.__init__ = original_init

        return widget

    def _add_data(self):
        fs = 128
        interval = self.data_timer.interval() / 1000.0
        self.sample_accumulator += fs * interval
        n_samples = int(self.sample_accumulator)
        self.sample_accumulator -= n_samples

        if n_samples == 0:
            return

        self.total_samples += n_samples
        self.debug_counter += 1

        current = time.time()
        if current - self.last_debug >= 1.0:
            rate = self.debug_counter / (current - self.last_debug)
            logging.info(f"Data rate: {rate:.1f} Hz, {n_samples} samples/call")
            self.debug_counter = 0
            self.last_debug = current

        t = time.time()

        for i in range(4):
            data = np.zeros((n_samples, 1), dtype=np.float32)
            freq = 1.0 + i * 0.5
            phase = i * np.pi / 4
            for s in range(n_samples):
                data[s, 0] = np.sin(2 * np.pi * freq * (t + s * 0.01) + phase)
                data[s, 0] += np.random.randn() * 0.1
            self.plot_widgets[i].addData(data)

        data_imu = np.zeros((n_samples, 3), dtype=np.float32)
        for s in range(n_samples):
            data_imu[s, 0] = np.sin(2 * np.pi * 0.5 * (t + s * 0.01))
            data_imu[s, 1] = np.cos(2 * np.pi * 0.7 * (t + s * 0.01))
            data_imu[s, 2] = np.sign(np.sin(2 * np.pi * 0.3 * (t + s * 0.01))) * 0.8
            data_imu[s, :] += np.random.randn(3) * 0.05
        self.plot_widgets[4].addData(data_imu)

    def _collect_metrics(self):
        try:
            self.cpu_samples.append(self.process.cpu_percent())
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            self.memory_samples.append(memory_mb)
        except Exception as e:
            logging.warning(f"Metrics collection failed: {e}")

    def _finish(self):
        self.data_timer.stop()
        self.metrics_timer.stop()

        for widget in self.plot_widgets:
            widget.stopTimers()

        elapsed = time.time() - self.test_start if self.test_start else 0
        sample_rate = self.total_samples / elapsed if elapsed > 0 else 0
        efficiency = (sample_rate / 128 * 100) if sample_rate > 0 else 0

        metrics = PerformanceMetrics(
            mode="OpenGL" if self.use_opengl else "Software",
            duration=elapsed,
            sample_rate=sample_rate,
            avg_cpu=np.mean(self.cpu_samples) if self.cpu_samples else 0,
            max_cpu=np.max(self.cpu_samples) if self.cpu_samples else 0,
            avg_memory=np.mean(self.memory_samples) if self.memory_samples else 0,
        )

        self.metrics = metrics

        print(f"\nSample Rate: {sample_rate:.2f} samples/s (expected: 128)")
        print(f"Efficiency: {efficiency:.1f}%")
        print(f"Total Samples: {self.total_samples}")
        print(metrics)

        self.close()

    def start(self):
        logging.info(f"Starting test: {'OpenGL' if self.use_opengl else 'Software'}")

        self.test_start = time.time()

        for widget in self.plot_widgets:
            widget.startTimers()

        self.data_timer.start()
        self.metrics_timer.start()
        self.stop_timer.start()

        if self.show_gui:
            self.show()

    def get_metrics(self):
        return self.metrics


def run_test(use_opengl, duration, show_gui=True):
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = PerformanceTestWindow(use_opengl, duration, show_gui)
    window.start()
    app.exec()

    return window.get_metrics()


def compare_results(opengl, software):
    print("\n" + "=" * 60)
    print("Comparison: OpenGL vs Software")
    print("=" * 60)

    rate_diff = opengl.sample_rate - software.sample_rate
    rate_pct = (
        (rate_diff / software.sample_rate * 100) if software.sample_rate > 0 else 0
    )

    print("\nSample Rate:")
    print(f"  OpenGL:   {opengl.sample_rate:.2f} samples/s")
    print(f"  Software: {software.sample_rate:.2f} samples/s")
    print(f"  Diff:     {rate_diff:+.2f} ({rate_pct:+.1f}%)")

    cpu_diff = opengl.avg_cpu - software.avg_cpu
    cpu_pct = (cpu_diff / software.avg_cpu * 100) if software.avg_cpu > 0 else 0

    print("\nCPU Usage:")
    print(f"  OpenGL:   {opengl.avg_cpu:.2f}%")
    print(f"  Software: {software.avg_cpu:.2f}%")
    print(f"  Diff:     {cpu_diff:+.2f}% ({cpu_pct:+.1f}%)")

    mem_diff = opengl.avg_memory - software.avg_memory

    print("\nMemory:")
    print(f"  OpenGL:   {opengl.avg_memory:.2f} MB")
    print(f"  Software: {software.avg_memory:.2f} MB")
    print(f"  Diff:     {mem_diff:+.2f} MB")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="OpenGL vs Software rendering test")
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--no-gui", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    print("\n" + "=" * 60)
    print("BioGUI OpenGL Performance Test")
    print("=" * 60)
    print(f"Duration: {args.duration}s")
    print(f"Mode: {'Headless' if args.no_gui else 'GUI'}")
    print("=" * 60 + "\n")

    print("Testing SOFTWARE rendering...")
    software = run_test(False, args.duration, not args.no_gui)

    time.sleep(2)

    print("\nTesting OPENGL rendering...")
    opengl = run_test(True, args.duration, not args.no_gui)

    compare_results(opengl, software)


if __name__ == "__main__":
    main()
