#!/usr/bin/env python3
"""
Performance test script for OpenGL rendering vs software rendering.

This script tests the dummy interface with both OpenGL and software rendering
to measure the performance impact.

Usage:
    python performance_test_opengl.py [--duration SECONDS] [--no-gui]
"""

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import psutil
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

# Add parent directory to Python path so we can import biogui module
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from biogui.views.signal_plot_widget import SignalPlotWidget


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    mode: str  # "OpenGL" or "Software"
    duration: float
    frames_rendered: int
    avg_cpu_percent: float
    max_cpu_percent: float
    avg_memory_mb: float
    avg_frame_time_ms: float
    max_frame_time_ms: float
    min_frame_time_ms: float
    fps: float

    def __str__(self) -> str:
        return (
            f"\n{'=' * 60}\n"
            f"Performance Metrics - {self.mode} Rendering\n"
            f"{'=' * 60}\n"
            f"Test Duration:        {self.duration:.2f} s\n"
            f"Data Processing Rate: {self.fps:.2f} samples/s\n"
            f"---\n"
            f"CPU Usage (avg):      {self.avg_cpu_percent:.2f}%\n"
            f"CPU Usage (max):      {self.max_cpu_percent:.2f}%\n"
            f"Memory Usage (avg):   {self.avg_memory_mb:.2f} MB\n"
            f"{'=' * 60}\n"
        )


class PerformanceTestWindow(QMainWindow):
    """Main window for performance testing."""

    def __init__(
        self,
        use_opengl: bool,
        test_duration: float,
        show_gui: bool = True,
    ):
        super().__init__()

        self.use_opengl = use_opengl
        self.test_duration = test_duration
        self.show_gui = show_gui

        # Performance tracking
        self.process = psutil.Process()
        self.start_time: Optional[float] = None
        self.test_start_time: Optional[float] = None
        self.cpu_samples: list[float] = []
        self.memory_samples: list[float] = []
        self.render_times: list[float] = []  # Renamed from frame_times
        self.data_added_count = 0  # How many times we added data
        self.renders_count = 0  # How many times we actually rendered

        # Setup UI
        self.setWindowTitle(
            f"Performance Test - {'OpenGL' if use_opengl else 'Software'} Rendering"
        )
        self.setGeometry(100, 100, 1400, 1000)

        # Central widget with grid layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Use grid layout for better organization
        from PySide6.QtWidgets import QGridLayout

        layout = QGridLayout(central_widget)

        # Create multiple plot widgets
        # 4 single-channel plots + 1 multi-channel plot (3 channels)
        self.plot_widgets = []

        # Create 4 single-channel plots (e.g., EMG channels)
        for i in range(4):
            plot_widget = self._create_plot_widget(
                use_opengl=use_opengl,
                sig_name=f"EMG Channel {i + 1}",
                n_channels=1,
                fs=128,
            )
            self.plot_widgets.append(plot_widget)
            # Arrange in 2x2 grid (first 4 plots)
            row = i // 2
            col = i % 2
            layout.addWidget(plot_widget, row, col)

        # Create 1 multi-channel plot (e.g., IMU - Accel X, Y, Z)
        multi_plot_widget = self._create_plot_widget(
            use_opengl=use_opengl,
            sig_name="IMU Accelerometer (X, Y, Z)",
            n_channels=3,
            fs=128,
        )
        self.plot_widgets.append(multi_plot_widget)
        # Place in bottom row, spanning both columns
        layout.addWidget(multi_plot_widget, 2, 0, 1, 2)

        # Hook into all plot widgets' render methods
        # self._hook_render_methods()

        # Timer for generating dummy data
        self.data_timer = QTimer(self)
        self.data_timer.setInterval(10)  # 100 Hz data generation
        self.data_timer.timeout.connect(self._generate_and_add_data)
        # Use precise timer to avoid being throttled by OpenGL
        self.data_timer.setTimerType(Qt.TimerType.PreciseTimer)

        # Timer for collecting performance metrics
        self.metrics_timer = QTimer(self)
        self.metrics_timer.setInterval(100)  # Sample every 100ms
        self.metrics_timer.timeout.connect(self._collect_metrics)

        # Timer for stopping the test
        self.stop_timer = QTimer(self)
        self.stop_timer.setSingleShot(True)
        self.stop_timer.setInterval(int(test_duration * 1000))
        self.stop_timer.timeout.connect(self._finish_test)

    def _hook_render_methods(self):
        """Hook into all plot widgets' render methods to measure actual render time."""
        for plot_widget in self.plot_widgets:
            original_refresh = plot_widget._refresh_plot

            def measured_refresh(orig=original_refresh):
                render_start = time.perf_counter()
                orig()
                render_end = time.perf_counter()

                render_time_ms = (render_end - render_start) * 1000
                self.render_times.append(render_time_ms)
                self.renders_count += 1

            plot_widget._refresh_plot = measured_refresh

    def _create_plot_widget(
        self, use_opengl: bool, sig_name: str, n_channels: int, fs: float
    ) -> SignalPlotWidget:
        """Create a plot widget with or without OpenGL."""
        # Temporarily modify the SignalPlotWidget class to control OpenGL usage
        original_init = SignalPlotWidget.__init__

        def patched_init(widget_self, *args, **kwargs):
            # Call original __init__ but skip OpenGL setup
            QWidget.__init__(widget_self, kwargs.get("parent"))
            widget_self.setupUi(widget_self)

            if use_opengl:
                # Enable OpenGL
                try:
                    from PySide6.QtOpenGLWidgets import QOpenGLWidget

                    gl_widget = QOpenGLWidget()
                    widget_self.graphWidget.setViewport(gl_widget)
                    logging.info(
                        f"OpenGL rendering enabled for {kwargs.get('sigName', 'plot')}"
                    )
                except Exception as e:
                    logging.error(f"Failed to initialize OpenGL: {e}")
            else:
                logging.info(
                    f"Software rendering enabled for {kwargs.get('sigName', 'plot')}"
                )

            # Continue with the rest of the initialization
            # Extract parameters
            sigName = args[0] if args else kwargs.get("sigName", "Test")
            fs = args[1] if len(args) > 1 else kwargs.get("fs", 128)
            nCh = args[2] if len(args) > 2 else kwargs.get("nCh", 4)
            chSpacing = args[3] if len(args) > 3 else kwargs.get("chSpacing", 1.0)
            renderLenMs = args[4] if len(args) > 4 else kwargs.get("renderLenMs", 5000)

            # Store parameters
            widget_self._sig_name = sigName
            widget_self._render_len_ms = renderLenMs
            widget_self._signal_type = kwargs.get("signal_type", {})

            # Set label
            widget_self.label1.setText("Sampling rate:")

            # Create plot mode - use only kwargs to avoid duplicate parameter issues
            from biogui.views.plot_modes import TimeSeriesPlotMode

            plot_mode_kwargs = {
                "fs": fs,
                "nCh": nCh,
                "chSpacing": chSpacing,
                "renderLenMs": renderLenMs,
            }
            # Add any additional kwargs (like signal_type, dataQueue, etc.)
            for key in ["signal_type", "dataQueue", "minRange", "maxRange"]:
                if key in kwargs:
                    plot_mode_kwargs[key] = kwargs[key]

            widget_self._plot_mode = TimeSeriesPlotMode(**plot_mode_kwargs)

            # Setup UI and plot
            widget_self._setup_graph_widget(widget_self._sig_name)
            widget_self._plot_mode.setup_plot(widget_self.graphWidget)
            widget_self._setup_timers()

        # Monkey-patch temporarily
        SignalPlotWidget.__init__ = patched_init

        try:
            widget = SignalPlotWidget(
                sigName=sig_name,
                fs=fs,
                nCh=n_channels,
                chSpacing=1.0,
                renderLenMs=5000,
                signal_type={"type": "time-series"},
            )
        finally:
            # Restore original __init__
            SignalPlotWidget.__init__ = original_init

        return widget

    def _generate_and_add_data(self):
        """Generate dummy data and add to all plots (simulating real-time streaming)."""
        # Generate the correct number of samples based on timer interval
        if not hasattr(self, "_accumulated_samples"):
            self._accumulated_samples = 0.0
            self._debug_counter = 0
            self._last_debug_time = time.time()
            self._total_samples_generated = 0  # Track total samples

        fs = 128  # Hz
        interval_s = self.data_timer.interval() / 1000.0  # Convert ms to seconds
        samples_per_interval = fs * interval_s

        self._accumulated_samples += samples_per_interval
        n_samples = int(self._accumulated_samples)
        self._accumulated_samples -= n_samples

        if n_samples == 0:
            return

        # Track total samples generated
        self._total_samples_generated += n_samples

        # Debug output every second
        self._debug_counter += 1
        current_time = time.time()
        if current_time - self._last_debug_time >= 1.0:
            elapsed = current_time - self._last_debug_time
            data_rate = self._debug_counter / elapsed
            logging.info(
                f"Data generation rate: {data_rate:.1f} Hz, {n_samples} samples/call"
            )
            self._debug_counter = 0
            self._last_debug_time = current_time

        # Create synthetic signals for all plots
        t = time.time()

        # Generate data for 4 single-channel plots (EMG-like signals)
        for i in range(4):
            data = np.zeros((n_samples, 1), dtype=np.float32)
            for s in range(n_samples):
                # Each channel has different frequency and amplitude
                freq = 1.0 + i * 0.5  # 1.0, 1.5, 2.0, 2.5 Hz
                phase = i * np.pi / 4
                data[s, 0] = np.sin(2 * np.pi * freq * (t + s * 0.01) + phase)
                # Add some noise
                data[s, 0] += np.random.randn() * 0.1

            self.plot_widgets[i].addData(data)

        # Generate data for multi-channel plot (IMU-like: 3 channels)
        data_multi = np.zeros((n_samples, 3), dtype=np.float32)
        for s in range(n_samples):
            # Channel 0: X-axis (sine)
            data_multi[s, 0] = np.sin(2 * np.pi * 0.5 * (t + s * 0.01))
            # Channel 1: Y-axis (cosine)
            data_multi[s, 1] = np.cos(2 * np.pi * 0.7 * (t + s * 0.01))
            # Channel 2: Z-axis (square-ish)
            data_multi[s, 2] = np.sign(np.sin(2 * np.pi * 0.3 * (t + s * 0.01))) * 0.8
            # Add noise to all channels
            data_multi[s, :] += np.random.randn(3) * 0.05

        self.plot_widgets[4].addData(data_multi)

        self.data_added_count += 1

    def _collect_metrics(self):
        """Collect CPU and memory usage metrics."""
        try:
            # CPU usage (percent)
            cpu_percent = self.process.cpu_percent()
            self.cpu_samples.append(cpu_percent)

            # Memory usage (MB)
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            self.memory_samples.append(memory_mb)
        except Exception as e:
            logging.warning(f"Failed to collect metrics: {e}")

    def _finish_test(self):
        """Finish the test and compute metrics."""
        # Stop all timers
        self.data_timer.stop()
        self.metrics_timer.stop()

        for plot_widget in self.plot_widgets:
            plot_widget.stopTimers()

        # Calculate metrics
        elapsed_time = time.time() - self.test_start_time if self.test_start_time else 0

        # Use our tracked sample count
        total_samples = getattr(self, "_total_samples_generated", 0)
        actual_sample_rate = total_samples / elapsed_time if elapsed_time > 0 else 0

        # Expected sample rate at 128 Hz
        expected_rate = 128.0
        efficiency = (
            (actual_sample_rate / expected_rate * 100) if expected_rate > 0 else 0
        )

        metrics = PerformanceMetrics(
            mode="OpenGL" if self.use_opengl else "Software",
            duration=elapsed_time,
            frames_rendered=self.data_added_count,  # Timer calls
            avg_cpu_percent=(np.mean(self.cpu_samples) if self.cpu_samples else 0.0),
            max_cpu_percent=(np.max(self.cpu_samples) if self.cpu_samples else 0.0),
            avg_memory_mb=(
                np.mean(self.memory_samples) if self.memory_samples else 0.0
            ),
            avg_frame_time_ms=0.0,
            max_frame_time_ms=0.0,
            min_frame_time_ms=0.0,
            fps=actual_sample_rate,
        )

        # Store metrics for later comparison
        self.metrics = metrics

        # Additional info
        print(f"\nData Processing Rate: {actual_sample_rate:.2f} samples/s")
        print(f"Expected Rate: {expected_rate:.2f} samples/s")
        print(f"Efficiency: {efficiency:.1f}%")
        print(f"Total Samples Generated: {total_samples}")

        # Print results
        print(metrics)

        # Close the window
        self.close()

    def start_test(self):
        """Start the performance test."""
        logging.info(
            f"Starting performance test ({'OpenGL' if self.use_opengl else 'Software'})..."
        )

        self.test_start_time = time.time()

        # Start all plot widget timers
        for plot_widget in self.plot_widgets:
            plot_widget.startTimers()

        # Start test timers
        self.data_timer.start()
        self.metrics_timer.start()
        self.stop_timer.start()

        if self.show_gui:
            self.show()

    def get_metrics(self) -> PerformanceMetrics:
        """Get the collected metrics after test completion."""
        return self.metrics


def run_performance_test(
    use_opengl: bool, duration: float, show_gui: bool = True
) -> PerformanceMetrics:
    """
    Run a single performance test.

    Parameters
    ----------
    use_opengl : bool
        Whether to use OpenGL rendering.
    duration : float
        Test duration in seconds.
    show_gui : bool
        Whether to show the GUI during testing.

    Returns
    -------
    PerformanceMetrics
        The collected performance metrics.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = PerformanceTestWindow(use_opengl, duration, show_gui)
    window.start_test()

    app.exec()

    return window.get_metrics()


def compare_metrics(
    opengl_metrics: PerformanceMetrics, software_metrics: PerformanceMetrics
):
    """Compare and print the difference between OpenGL and software rendering."""
    print("\n" + "=" * 60)
    print("COMPARISON: OpenGL vs Software Rendering")
    print("=" * 60)

    # Data processing rate comparison
    rate_diff = opengl_metrics.fps - software_metrics.fps
    rate_percent = (
        (rate_diff / software_metrics.fps * 100) if software_metrics.fps > 0 else 0
    )
    print(f"\nData Processing Rate (samples/s):")
    print(f"  OpenGL:   {opengl_metrics.fps:.2f}")
    print(f"  Software: {software_metrics.fps:.2f}")
    print(f"  Diff:     {rate_diff:+.2f} ({rate_percent:+.1f}%)")

    # CPU usage comparison
    cpu_diff = opengl_metrics.avg_cpu_percent - software_metrics.avg_cpu_percent
    cpu_percent = (
        (cpu_diff / software_metrics.avg_cpu_percent * 100)
        if software_metrics.avg_cpu_percent > 0
        else 0
    )
    print(f"\nAverage CPU Usage:")
    print(f"  OpenGL:   {opengl_metrics.avg_cpu_percent:.2f}%")
    print(f"  Software: {software_metrics.avg_cpu_percent:.2f}%")
    print(f"  Diff:     {cpu_diff:+.2f}% ({cpu_percent:+.1f}%)")

    # Memory usage comparison
    mem_diff = opengl_metrics.avg_memory_mb - software_metrics.avg_memory_mb
    print(f"\nAverage Memory Usage:")
    print(f"  OpenGL:   {opengl_metrics.avg_memory_mb:.2f} MB")
    print(f"  Software: {software_metrics.avg_memory_mb:.2f} MB")
    print(f"  Diff:     {mem_diff:+.2f} MB")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)

    # Check if data processing is significantly impacted
    if rate_percent < -10:
        print(
            f"✗ OpenGL BLOCKS the event loop: {abs(rate_percent):.1f}% slower data processing!"
        )
        print("  → This means fewer data samples are processed")
        print("  → Signals appear 'compressed' or 'choppy'")
    elif rate_percent > 10:
        print(f"✓ OpenGL processes data faster: {rate_percent:.1f}% improvement")
    else:
        print("≈ Similar data processing rate")

    # Overall recommendation
    print()
    if cpu_diff < 0 and mem_diff < 50:
        print("✓ RECOMMENDATION: Use OpenGL (lower CPU, acceptable memory)")
    elif rate_percent < -10:
        print("✗ RECOMMENDATION: Avoid OpenGL (blocks data processing!)")
    elif cpu_diff > 20:
        print("✗ RECOMMENDATION: Use Software rendering (much lower CPU usage)")
    else:
        print("≈ RECOMMENDATION: Both options are similar, Software is safer")

    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Performance test for OpenGL vs Software rendering"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Test duration in seconds (default: 10)",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Run tests without showing the GUI (headless)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    print("\n" + "=" * 60)
    print("BioGUI OpenGL Performance Test")
    print("=" * 60)
    print(f"Test Duration: {args.duration} seconds")
    print(f"GUI Mode: {'Headless' if args.no_gui else 'Visible'}")
    print("=" * 60 + "\n")

    # Run software rendering test
    print("Running test with SOFTWARE rendering...")
    software_metrics = run_performance_test(
        use_opengl=False,
        duration=args.duration,
        show_gui=not args.no_gui,
    )

    # Small delay between tests
    time.sleep(2)

    # Run OpenGL rendering test
    print("\nRunning test with OPENGL rendering...")
    opengl_metrics = run_performance_test(
        use_opengl=True,
        duration=args.duration,
        show_gui=not args.no_gui,
    )

    # Compare results
    compare_metrics(opengl_metrics, software_metrics)


if __name__ == "__main__":
    main()
