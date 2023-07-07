import os
import sys
from collections import deque

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QCloseEvent, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

from data_controller import DataController

os.chdir("src")
ui_class, base_class = pg.Qt.loadUiType("main_window.ui")


class GraphWindow(ui_class, base_class):
    """Main window showing the real time plot.

    Parameters
    ----------
    n_ch : int, default=16
        Number of channels.
    fs : int, default=4000
        Sampling frequency.
    queue_mem : int
        Memory of the internal deques.

    Attributes
    ----------
    graphWidget : PlotWidget
        Widget encompassing the plot.
    _x : deque
        Deque for X values.
    _y : deque
        Deque for Y values.
    _n_ch : int
        Number of channels.
    _fs : int
        Sampling frequency.
    _plots : list of PlotItems
        List containing a PlotItem for each channel.
    """

    close_sig = pyqtSignal()

    def __init__(self, n_ch: int, fs: int, queue_mem: int):
        super().__init__()

        self._n_ch = n_ch
        self._fs = fs
        # Initialize deques
        self._x = deque(maxlen=queue_mem)
        self._y = deque(maxlen=queue_mem)
        for i in range(-queue_mem, 0):
            self._x.append(i / fs)
            self._y.append(np.zeros(n_ch))

        self.setupUi(self)

        # Handle color palette
        cm = pg.colormap.get("CET-C1")
        cm.setMappingMode("diverging")
        lut = cm.getLookupTable(nPts=n_ch, mode="qcolor")
        colors = [lut[i] for i in range(n_ch)]

        # Initialize graph widget
        self.graphWidget.setYRange(-2000, 30000)
        self.graphWidget.getPlotItem().hideAxis("bottom")
        self.graphWidget.getPlotItem().hideAxis("left")

        # Plot placeholder data
        self._plots = []
        y = np.asarray(self._y).T
        for i in range(n_ch):
            pen = pg.mkPen(color=colors[i])
            self._plots.append(self.graphWidget.plot(self._x, y[i] + 2000 * i, pen=pen))
        self._buf_count = 0

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

    def closeEvent(self, event: QCloseEvent) -> None:
        event.accept()
        self.close_sig.emit()


class GeturesWindow(QWidget):
    """Widget showing the gestures to perform.

    Parameters
    ----------
    image_folder : str
        Path to the folder containing the images of each gesture (start.png, stop.png, <idx>.png).
    gesture_duration_ms : int, default=5000
        Gesture duration (in ms).

    Attributes
    ----------
    _image_folder : str
        Path to the folder containing the images of each gesture.
    _label : QLabel
        Label containing the image widget.
    _pixmap : QPixmap
        Image widget.
    _gestures_label : list of ints
        List of gestures encoded as integers.
    _timer : QTimer
        Timer.
    _toggle_timer : bool
        Pause/start the timer.
    _trial_idx : int
        Trial index.
    """

    trigger_sig = pyqtSignal(int)
    stop_sig = pyqtSignal()

    def __init__(self, image_folder: str, gesture_duration_ms: int = 5000) -> None:
        super().__init__()

        self.setWindowTitle("Gesture Viewer")
        self.resize(480, 480)

        self._image_folder = image_folder

        self._label = QLabel(self)
        self._pixmap = QPixmap(os.path.join(self._image_folder, "start.png"))
        self._pixmap = self._pixmap.scaled(self.width(), self.height())
        self._label.setPixmap(self._pixmap)
        self._gestures_label = list(range(1, 9))
        self._gestures_label = sorted(self._gestures_label * 3)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.showImage)
        self._toggle_timer = True
        self._trial_idx = 0
        self._timer.start(gesture_duration_ms)

    def showImage(self):
        if self._trial_idx == len(self._gestures_label):
            self.close()
        elif self._toggle_timer:
            self._pixmap = QPixmap(
                os.path.join(self._image_folder, f"{self._gestures_label[self._trial_idx]}.png")
            )
            self._pixmap = self._pixmap.scaled(self.width(), self.height())
            self._label.setPixmap(self._pixmap)

            self._toggle_timer = False
            self.trigger_sig.emit(self._gestures_label[self._trial_idx])
            self._trial_idx += 1
        else:
            self._pixmap = QPixmap(os.path.join(self._image_folder, "stop.png"))
            self._pixmap = self._pixmap.scaled(self.width(), self.height())
            self._label.setPixmap(self._pixmap)

            self._toggle_timer = True
            self.trigger_sig.emit(0)

    def closeEvent(self, event):
        self._timer.stop()
        self.stop_sig.emit()
        event.accept()


if __name__ == "__main__":
    # movements = [
    #     "open hand",
    #     "fist (power grip)",
    #     "index pointed",
    #     "ok (thumb up)",
    #     "right flexion (wrist supination)",
    #     "left flexion (wristpronation)",
    #     "horns",
    #     "shaka",
    # ]

    app = QApplication(sys.argv)

    graph_win = GraphWindow(n_ch=16, fs=4000, queue_mem=2000)
    graph_win.show()
    gest_win = GeturesWindow(image_folder="hand_mov")
    gest_win.show()

    data_controller = DataController(
        serial_kw={"serial_port": "COM16"},
        file_kw={"file_path": "serial.bin"},
        preprocess_kw={"n_samp": 1},
    )

    data_controller.preprocess_worker.data_ready_sig.connect(graph_win.grab_data)
    graph_win.close_sig.connect(data_controller.stop_acquistion)
    gest_win.trigger_sig.connect(data_controller.update_trigger)
    gest_win.stop_sig.connect(data_controller.stop_file_writer)

    data_controller.start_threads()

    sys.exit(app.exec())
