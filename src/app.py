import sys
from collections import deque

import numpy as np
import pyqtgraph as pg
from PyQt6 import QtGui
from PyQt6.QtCore import QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QCloseEvent, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QWidget

from data_controller import DataController


class GraphWindow(QMainWindow):
    """Widget showing the real time plot.

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
    _x : deque
        Deque for X values.
    _y : deque
        Deque for Y values.
    _n_ch : int
        Number of channels.
    _fs : int
        Sampling frequency.
    _graph : PlotWidget
        Widget encompassing the plot.
    _plots : list of PlotItems
        List containing a PlotItem for each channel.
    """

    close_sig = pyqtSignal()

    def __init__(self, n_ch: int, fs: int, queue_mem: int):
        super(GraphWindow, self).__init__()

        # Handle color palette
        cm = pg.colormap.get("CET-C1")
        cm.setMappingMode("diverging")
        lut = cm.getLookupTable(nPts=n_ch, mode="qcolor")
        colors = [lut[i] for i in range(n_ch)]

        self._n_ch = n_ch
        self._fs = fs
        # Initialize deques
        self._x = deque(maxlen=queue_mem)
        self._y = deque(maxlen=queue_mem)
        for i in range(-queue_mem, 0):
            self._x.append(i / fs)
            self._y.append(np.zeros(n_ch))

        # Create graph widget
        self._graph = pg.PlotWidget()
        self._graph.setYRange(-2000, 30000)
        self._graph.getPlotItem().hideAxis("bottom")
        self._graph.getPlotItem().hideAxis("left")
        self.setCentralWidget(self._graph)

        # Plot placeholder data
        self._plots = []
        y = np.asarray(self._y).T
        for i in range(n_ch):
            pen = pg.mkPen(color=colors[i])
            self._plots.append(self._graph.plot(self._x, y[i] + 2 * i, pen=pen))
        self._i = 0

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

            if self._i == 50:
                xs = list(self._x)
                ys = np.asarray(list(self._y)).T
                for i in range(self._n_ch):
                    self._plots[i].setData(xs, ys[i] + 2000 * i, skipFiniteCheck=True)
                self._i = 0
            self._i += 1

    def closeEvent(self, event: QCloseEvent) -> None:
        self.close_sig.emit()
        event.accept()


class GeturesWindow(QWidget):
    """"""

    signal_trigger = pyqtSignal(int)
    signal_close_file = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.title = "Image Viewer"
        self.setWindowTitle(self.title)
        # self.image_folder = f"C:\\Users\pierangelomaria.rap2\Documents\hand_mov\\"
        self.image_folder = ".\\src\hand_mov\\"
        self.label = QLabel(self)
        self.pixmap = QPixmap(f"{self.image_folder}start.png")
        self.resize(840, 840)
        self.pixmap = self.pixmap.scaled(self.width(), self.height())
        self.label.setPixmap(self.pixmap)
        movements = [
            "open hand",
            "fist (power grip)",
            "index pointed",
            "ok (thumb up)",
            "right flexion (wrist supination)",
            "left flexion (wristpronation)",
            "horns",
            "shaka",
        ]
        movements = [ele for ele in movements for i in range(3)]
        self.gesturesLabel = list(range(1, 9))
        self.gesturesLabel = sorted(self.gesturesLabel * 3)
        # self.setCentralWidget(self.label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.showImage)
        self.startStop = False
        self.i = 0
        self.startTimer()
        self.closeWidget = False

    def showImage(self):
        if self.i == 3:
            self.closeWidget = True
            self.close()
        if self.startStop:
            self.pixmap = QPixmap(
                f"{self.image_folder}{self.gesturesLabel[self.i]}.png"
            )
            self.pixmap = self.pixmap.scaled(self.width(), self.height())
            self.label.setPixmap(self.pixmap)
            self.label.resize(self.width(), self.height())
            self.label.setPixmap(self.pixmap)
            self.startStop = False
            self.signal_trigger.emit(self.gesturesLabel[self.i])
            self.i += 1
        else:
            self.pixmap = QPixmap(f"{self.image_folder}Stop.png")
            self.pixamp = self.pixmap.scaled(840, 840)

            self.label.setPixmap(self.pixmap)
            self.startStop = True
            self.signal_trigger.emit(0)

    def startTimer(self):
        self.timer.start(5000)

    def closeEvent(self, event):
        self.timer.stop()
        self.signal_close_file.emit()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    graph_win = GraphWindow(n_ch=16, fs=4000, queue_mem=1000)
    graph_win.showMaximized()
    gest_win = GeturesWindow()
    gest_win.show()

    data_controller = DataController(
        serial_kw={"serial_port": "COM16"},
        file_kw={"file_path": "serial.bin"},
        preprocess_kw={"n_samp": 1},
    )

    data_controller.preprocess_worker.data_ready_sig.connect(graph_win.grab_data)
    graph_win.close_sig.connect(data_controller.stop_acquistion)
    gest_win.signal_trigger.connect(data_controller.update_trigger)
    gest_win.signal_close_file.connect(data_controller.stop_file_writer)

    data_controller.start_threads()

    sys.exit(app.exec())
