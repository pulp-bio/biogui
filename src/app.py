import json
import os
import sys
from collections import deque

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox, QRadioButton

from acq_controller import AcquisitionController, serial_ports
from gesture_window import GeturesWindow

os.chdir("src")
ui_class, base_class = pg.Qt.loadUiType("main_window.ui")


def load_validate_json(file_path: str) -> dict | None:
    """Load and validate a JSON file representing the experiment configuration.

    Parameters
    ----------
    file_path : str
        Path the the JSON file.

    Returns
    -------
    dict or None
        Dictionary corresponding to the configuration, or None if it's not valid.
    """
    with open(file_path) as f:
        config = json.load(f)
    # Check keys
    provided_keys = set(config.keys())
    valid_keys = set(("gestures", "n_reps", "duration_ms", "image_folder"))
    if provided_keys != valid_keys:
        return None
    # Check paths
    if not os.path.isdir(config["image_folder"]):
        return None
    for image_path in config["gestures"].values():
        image_path = os.path.join(config["image_folder"], image_path)
        if not (
            os.path.isfile(image_path)
            and (image_path.endswith(".png") or image_path.endswith(".jpg"))
        ):
            return None

    return config


class GraphWindow(ui_class, base_class):
    """Main window showing the real time plot.

    Parameters
    ----------
    fs : int
        Sampling frequency.
    queue_mem : int
        Memory of the internal deques.

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
    _plots : list of PlotItems
        List containing a PlotItem for each channel.
    _gest_win : GeturesWindow
        Window for gesture visualization.
    """

    def __init__(self, fs: int, queue_mem: int):
        super().__init__()

        self._fs = fs
        self._x = deque(maxlen=queue_mem)
        self._y = deque(maxlen=queue_mem)
        self._buf_count = 0

        self.setupUi(self)

        # Serial ports
        self.rescan_serial_ports()
        self.rescanSerialPortsButton.clicked.connect(self.rescan_serial_ports)
        self._serial_port = self.serialPortsComboBox.currentText()

        # Number of channels
        ch_buttons = filter(
            lambda elem: isinstance(elem, QRadioButton),
            self.channelsGroupBox.children(),
        )
        for ch_button in ch_buttons:
            ch_button.clicked.connect(self.update_channels)
            if ch_button.isChecked():
                self._n_ch = int(ch_button.text())  # set initial number of channels

        # Plot
        self._plots = []
        self._initialize_plot()

        # Experiments
        self._gest_win = None
        self._config = None
        self.browseJSONButton.clicked.connect(self._browse_json)

        # Acquisition
        self._acq_controller = None
        self.startAcquisitionButton.clicked.connect(self.start_acquisition)
        self.stopAcquisitionButton.clicked.connect(self.stop_acquisition)

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
        self._config = load_validate_json(file_path)

        display_text = "JSON config invalid!" if self._config is None else file_path
        self.JSONLabel.setText(display_text)

    def rescan_serial_ports(self) -> None:
        """Rescan the serial ports to update the combo box."""
        self.serialPortsComboBox.clear()
        self.serialPortsComboBox.addItems(serial_ports())

    def update_channels(self) -> None:
        """Update the number of channels depending on user selection."""
        ch_button = next(
            filter(
                lambda elem: isinstance(elem, QRadioButton) and elem.isChecked(),
                self.channelsGroupBox.children(),
            )
        )
        self._n_ch = int(ch_button.text())
        self._initialize_plot()  # redraw plot

    @pyqtSlot(np.ndarray)
    def grab_data(self, data: np.ndarray):
        """This method is called automatically when the associated signal is received,
        it grabs data from the signal and plots it.

        Parameters
        ----------
        data : ndarray
            Data to plot.
        """
        for samples in data:
            self._x.append(self._x[-1] + 1 / self._fs)
            self._y.append(samples)

            if self._buf_count == 50:
                xs = list(self._x)
                ys = np.asarray(list(self._y)).T
                for i in range(self._n_ch):
                    self._plots[i].setData(xs, ys[i] + 2000 * i, skipFiniteCheck=True)
                self._buf_count = 0
            self._buf_count += 1

    def start_acquisition(self) -> None:
        """Start the acquisition."""
        if self.experimentGroupBox.isChecked() and self._config is not None:
            self._gest_win = GeturesWindow(**self._config)
            self._gest_win.show()
        # Handle UI elements
        self.serialPortsGroupBox.setEnabled(False)
        self.channelsGroupBox.setEnabled(False)
        self.experimentGroupBox.setEnabled(False)
        self.startAcquisitionButton.setEnabled(False)
        self.stopAcquisitionButton.setEnabled(True)

        self._acq_controller = AcquisitionController(self._serial_port, n_ch=self._n_ch, fs=self._fs, n_samp=1)
        self._acq_controller.preprocess_worker.data_ready_sig.connect(self.grab_data)
        self._acq_controller.start_acquisition()

    def stop_acquisition(self) -> None:
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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    graph_win = GraphWindow(fs=4000, queue_mem=2000)
    graph_win.show()

    # data_controller = DataController(
    #     serial_kw={"serial_port": "COM16"},
    #     file_kw={"file_path": "serial.bin"},
    #     preprocess_kw={"n_samp": 1},
    # )

    # data_controller.preprocess_worker.data_ready_sig.connect(graph_win.grab_data)
    # graph_win.close_sig.connect(data_controller.stop_acquistion)
    # gest_win.trigger_sig.connect(data_controller.update_trigger)
    # gest_win.stop_sig.connect(data_controller.stop_file_writer)

    # data_controller.start_threads()

    sys.exit(app.exec())
