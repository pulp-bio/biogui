"""This module contains the main window of the app.


Copyright 2023 Mattia Orlandi, Pierangelo Maria Rapa

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

import datetime
import os
from collections import deque

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QRadioButton
from scipy import signal

from ._acquisition._abc_acq_controller import AcquisitionController
from ._acquisition._dummy_acq_controller import DummyAcquisitionController
from ._acquisition._esb_acq_controller import ESBAcquisitionController
from ._file_controller import FileController
from ._gesture_window import GeturesWindow
from ._ui.main_window_ui import Ui_MainWindow
from ._utils import load_validate_json, serial_ports


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window showing the real time plot.

    Parameters
    ----------
    fs : int
        Sampling frequency.
    wl : int
        Memory of the internal deques.
    dummy : bool, default=False
        Whether to use dummy signals.

    Attributes
    ----------
    _x : deque
        Deque for X values.
    _y : deque
        Deque for Y values.
    _n_ch : int
        Number of channels.
    _fs : int
        Sampling frequency.
    _serial_port : str
        Serial port.
    _config : dit
        Dictionary representing the experiment configuration.
    _buf_count : int
        Counter for the plot buffer.
    _dummy : bool
        Whether to use dummy signals.
    _plots : list of PlotItems
        List containing a PlotItem for each channel.
    _gest_win : GeturesWindow
        Window for gesture visualization.
    _b : ndarray
        Numerator polynomials for the filter.
    _a : ndarray
        Denominator polynomials for the filter.
    _zi : list of ndarrays
        Initial state for the filter (one per channel).
    """

    def __init__(self, fs: int, wl: int, dummy: bool = False):
        super(MainWindow, self).__init__()

        self._fs = fs
        self._x = deque(maxlen=wl)
        self._y = deque(maxlen=wl)
        self._buf_count = 0
        self._dummy = dummy

        self.setupUi(self)

        # Serial ports
        self._rescan_serial_ports()
        self._serial_port = self.serialPortsComboBox.currentText()
        self.serialPortsComboBox.currentTextChanged.connect(self._serial_port_change)
        self.rescanSerialPortsButton.clicked.connect(self._rescan_serial_ports)

        # Number of channels
        ch_buttons = filter(
            lambda elem: isinstance(elem, QRadioButton),
            self.channelsGroupBox.children(),
        )
        for ch_button in ch_buttons:
            ch_button.clicked.connect(self._update_channels)
            if ch_button.isChecked():
                self._n_ch = int(ch_button.text())  # set initial number of channels

        # Plot
        self._plots = []
        self._initialize_plot()

        # Experiments
        self._gest_win: GeturesWindow | None = None
        self._config: dict | None = None
        self.browseJSONButton.clicked.connect(self._browse_json)

        # Acquisition
        self._acq_controller: AcquisitionController = None
        self.startAcquisitionButton.setEnabled(self._serial_port != "" or self._dummy)
        self.stopAcquisitionButton.setEnabled(False)
        self.startAcquisitionButton.clicked.connect(self._start_acquisition)
        self.stopAcquisitionButton.clicked.connect(self._stop_acquisition)

        # Filtering
        self._b, self._a = signal.iirfilter(
            N=2, Wn=20, fs=fs, btype="high", ftype="butter"
        )
        self._zi = [signal.lfilter_zi(self._b, self._a) for _ in range(self._n_ch)]

    def _rescan_serial_ports(self) -> None:
        """Rescan the serial ports to update the combo box."""
        self.serialPortsComboBox.clear()
        self.serialPortsComboBox.addItems(serial_ports())

    def _serial_port_change(self) -> None:
        """Detect if the serial port has changed."""
        self._serial_port = self.serialPortsComboBox.currentText()
        self.startAcquisitionButton.setEnabled(self._serial_port != "")

    def _initialize_plot(self) -> None:
        """Render the initial plot."""
        # Reset graph
        self.graphWidget.clear()
        self.graphWidget.setYRange(0, 2000 * (self._n_ch - 1))
        self.graphWidget.getPlotItem().hideAxis("bottom")
        self.graphWidget.getPlotItem().hideAxis("left")
        # Initialize deques
        for i in range(-self._x.maxlen, 0):
            self._x.append(i / self._fs)
            self._y.append(np.zeros(self._n_ch))
        # Get colormap
        cm = pg.colormap.get("CET-C1")
        cm.setMappingMode("diverging")
        lut = cm.getLookupTable(nPts=self._n_ch, mode="qcolor")
        colors = [lut[i] for i in range(self._n_ch)]
        # Plot placeholder data
        y = np.asarray(self._y).T
        for i in range(self._n_ch):
            pen = pg.mkPen(color=colors[i])
            self._plots.append(self.graphWidget.plot(self._x, y[i] + 2000 * i, pen=pen))

    def _browse_json(self) -> None:
        """Browse to select the JSON file with the experiment configuration."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load JSON configuration",
            filter="*.json",
        )
        display_text = ""
        if file_path:
            self._config = load_validate_json(file_path)
            display_text = "JSON config invalid!" if self._config is None else file_path
        self.JSONLabel.setText(display_text)

    def _update_channels(self) -> None:
        """Update the number of channels depending on user selection."""
        ch_button = next(
            filter(
                lambda elem: isinstance(elem, QRadioButton) and elem.isChecked(),
                self.channelsGroupBox.children(),
            )
        )
        self._n_ch = int(ch_button.text())
        self._plots = []
        self._initialize_plot()  # redraw plot
        self._zi = [
            signal.lfilter_zi(self._b, self._a) for _ in range(self._n_ch)
        ]  # re-initialize filter

    def _start_acquisition(self) -> None:
        """Start the acquisition."""
        # Handle UI elements
        self.serialPortsGroupBox.setEnabled(False)
        self.channelsGroupBox.setEnabled(False)
        self.experimentGroupBox.setEnabled(False)
        self.startAcquisitionButton.setEnabled(False)
        self.stopAcquisitionButton.setEnabled(True)

        self._acq_controller = (
            DummyAcquisitionController(self._n_ch)
            if self._dummy
            else ESBAcquisitionController(self._serial_port, n_ch=self._n_ch)
        )
        self._acq_controller.connect_data_ready(self.grab_data)
        if self.experimentGroupBox.isChecked() and self._config is not None:
            # Output file
            exp_dir = os.path.join(os.path.dirname(self.JSONLabel.text()), "data")
            os.mkdir(exp_dir)
            out_file_name = self.experimentTextField.text()
            if out_file_name == "":
                out_file_name = (
                    f"acq_{datetime.datetime.now()}".replace(" ", "_")
                    .replace(":", "-")
                    .replace(".", "-")
                )
            out_file_name = f"{out_file_name}.bin"
            out_file_path = os.path.join(exp_dir, out_file_name)

            # Create gesture window and file controller
            self._gest_win = GeturesWindow(**self._config)
            self._gest_win.show()
            self._gest_win.trigger_sig.connect(self._acq_controller.update_trigger)
            self._file_controller = FileController(out_file_path, self._acq_controller)
            self._gest_win.stop_sig.connect(self._file_controller.stop_file_writer)

        self._acq_controller.start_acquisition()

    def _stop_acquisition(self) -> None:
        """Stop the acquisition."""
        self._acq_controller.stop_acquisition()

        if self._gest_win is not None:
            self._gest_win.close()
        # Handle UI elements
        self.serialPortsGroupBox.setEnabled(True)
        self.channelsGroupBox.setEnabled(True)
        self.experimentGroupBox.setEnabled(True)
        self.startAcquisitionButton.setEnabled(True)
        self.stopAcquisitionButton.setEnabled(False)

    @pyqtSlot(np.ndarray)
    def grab_data(self, data: np.ndarray):
        """This method is called automatically when the associated signal is received,
        it grabs data from the signal and plots it.

        Parameters
        ----------
        data : ndarray
            Data to plot.
        """
        for i in range(self._n_ch):
            data[:, i], self._zi[i] = signal.lfilter(
                self._b, self._a, data[:, i], zi=self._zi[i], axis = 0
            )

        for samples in data:
            self._x.append(self._x[-1] + 1 / self._fs)
            self._y.append(samples[: self._n_ch])

            if self._buf_count == 100:
                xs = list(self._x)
                ys = np.asarray(list(self._y)).T
                for i in range(self._n_ch):
                    self._plots[i].setData(xs, ys[i] + 2000 * i, skipFiniteCheck=True)
                self._buf_count = 0
            self._buf_count += 1
