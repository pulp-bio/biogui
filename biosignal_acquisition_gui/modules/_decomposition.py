"""This module contains the MU extraction controller and widgets.


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

import logging
from collections import deque

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QFileDialog, QWidget

from .._ui.ui_decomposition_config import Ui_DecompositionConfig
from .._ui.ui_mu_plot import Ui_MUPlot
from ..main_window import MainWindow


def extend_signal(x: np.ndarray, f_ext: int = 1) -> np.ndarray:
    """Extend signal with delayed replicas by a given extension factor.

    Parameters
    ----------
    x : ndarray
        A signal with shape:
        - (n_samples,);
        - (n_samples, n_channels).
    f_ext : int, default=1
        Extension factor.

    Returns
    -------
    ndarray
        Extended signal with shape (n_samples - f_ext + 1, f_ext * n_channels).
    """
    n_samp, n_ch = x.shape
    n_ch_ext = f_ext * n_ch

    x_ext = np.zeros(shape=(n_samp - f_ext + 1, n_ch_ext), dtype=x.dtype)
    for i in range(f_ext):
        x_ext[:, i * n_ch : (i + 1) * n_ch] = x[f_ext - i - 1 : n_samp - i]
    return x_ext


class ORICAWorker(QObject):
    """Class implementing ORICA.

    Attributes
    ----------
    _n : int
        Iteration count.
    _approx : bool
        Whether to use the approximate orthogonalization.

    Class attributes
    ----------------
    decompSig : Signal
        Qt signal emitted when decomposition is performed.
    """

    decompSig = Signal(np.ndarray)

    def __init__(self) -> None:
        super().__init__()

        self._n = 1
        self._approx = False

        self._f_ext = 32  # TODO
        self._bufferSize = 512  # TODO: 128ms @ 4ksps
        self._bufferCount = 0
        self._queue = deque()

        self._lambda_0 = None
        self._gamma = None
        self._whiteMtx = None
        self._sepMtx = None

    @property
    def lambda_0(self) -> float:
        """float: Property representing the initial forgetting factor."""
        return self._lambda_0

    @lambda_0.setter
    def lambda_0(self, lambda0: float) -> None:
        self._lambda_0 = lambda0

    @property
    def gamma(self) -> float:
        """float: Property representing the decaying factor."""
        return self._gamma

    @gamma.setter
    def gamma(self, gamma: float) -> None:
        self._gamma = gamma

    @property
    def whiteMtx(self) -> np.ndarray:
        """ndarray: Property representing the estimated whitening matrix."""
        return self._whiteMtx

    @whiteMtx.setter
    def whiteMtx(self, whiteMtx: np.ndarray) -> None:
        self._whiteMtx = whiteMtx

    @property
    def sepMtx(self) -> np.ndarray:
        """ndarray: Property representing the estimated separation matrix."""
        return self._sepMtx

    @sepMtx.setter
    def sepMtx(self, sepMtx: np.ndarray) -> None:
        self._sepMtx = sepMtx

    @Slot(np.ndarray)
    def decompose(self, data: np.ndarray) -> None:
        """Decompose the given signal.

        Parameters
        ----------
        data : ndarray
            Data to decompose.
        """

        # Contrast function for super-gaussian sources
        def gFn(x_):
            return -2 * np.tanh(x_)

        def symOrth(w_: np.ndarray) -> np.ndarray:
            eigVals, eigVecs = np.linalg.eigh(w_ @ w_.T)

            # Improve numerical stability
            # eigVals = np.clip(eigVals, min=np.finfo(w_.dtype).tiny)

            dMtx = np.diag(1.0 / np.sqrt(eigVals))
            return eigVecs @ dMtx @ eigVecs.T @ w_

        def symOrthApprox(w_: np.ndarray) -> np.ndarray:
            maxIter = 8

            for _ in range(maxIter):
                w_ /= np.linalg.norm(w_, ord=1).item()
                w_ = 3 / 2 * w_ - 1 / 2 * w_ @ w_.T @ w_

            return w_

        for samples in data:
            self._queue.append(samples)
        self._bufferCount += data.shape[0]

        if self._bufferCount >= self._bufferSize:
            dataTmp = np.asarray(self._queue)
            x = extend_signal(dataTmp, self._f_ext).T
            nSamp = x.shape[1]

            lambda_n = self._lambda_0 / self._n**self._gamma
            if lambda_n < 1e-4:
                lambda_n = 1e-4
            beta = (1 - lambda_n) / lambda_n

            # Whitening
            whiteMtxOld = self._whiteMtx
            v = whiteMtxOld @ x
            covMtx = v @ v.T / nSamp
            normFactor = beta + (v * v).sum().item() / nSamp
            self._whiteMtx = (
                1 / (1 - lambda_n) * (whiteMtxOld - covMtx / normFactor @ whiteMtxOld)
            )
            v = self._whiteMtx @ x

            # Separation
            sepMtxOld = self._sepMtx
            y = sepMtxOld @ v
            g = gFn(y)
            covMtx = y @ g.T / nSamp
            normFactor = beta + (g * y).sum().item() / nSamp
            self._sepMtx = (
                1 / (1 - lambda_n) * (sepMtxOld - covMtx / normFactor @ sepMtxOld)
            )
            self._sepMtx = (
                symOrthApprox(self._sepMtx) if self._approx else symOrth(self._sepMtx)
            )
            y = self._sepMtx @ v

            self._n += 1  # n_samp

            self.decompSig.emit(y.T)

            self._bufferCount = 0
            self._queue.clear()


class _MUPlotWidget(QWidget, Ui_MUPlot):
    """Widget showing the MU spike trains.

    Parameters
    ----------
    nMu : int
        Number of motor units.

    Attributes
    ----------
    _xQueue : deque
        Queue for X values.
    _yQueue : deque
        Queue for Y values.
    _bufferCount : int
        Counter for the plot buffer.
    _bufferSize : int
        Size of the buffer for plotting samples.
    _plotSpacing : int
        Spacing between each channel in the plot.
    _plots : list of PlotItems
        List containing a PlotItem for each channel.

    Class attributes
    ----------------
    closeSig : Signal
        Qt signal emitted when the widget is closed.
    """

    closeSig = Signal()

    def __init__(self, nMu: int):
        super().__init__()

        self.setupUi(self)

        self._nMu = nMu
        renderLength = 3000
        self._xQueue = deque(maxlen=renderLength)
        self._yQueue = deque(maxlen=renderLength)
        self._bufferCount = 0
        self._bufferSize = 200
        self._plotSpacing = 100

        # Plot
        self._plots = []
        self._initializePlot()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.closeSig.emit()
        event.accept()

    def _initializePlot(self) -> None:
        """Render the initial plot."""
        # Reset graph
        self.graphWidget.clear()
        self.graphWidget.setYRange(0, self._plotSpacing * (self._nMu - 1))
        self.graphWidget.getPlotItem().hideAxis("bottom")
        self.graphWidget.getPlotItem().hideAxis("left")
        # Initialize queues
        for i in range(-self._xQueue.maxlen, 0):
            self._xQueue.append(i)
            self._yQueue.append(np.zeros(self._nMu))
        # Get colormap
        cm = pg.colormap.get("CET-C1")
        cm.setMappingMode("diverging")
        lut = cm.getLookupTable(nPts=self._nMu, mode="qcolor")
        colors = [lut[i] for i in range(self._nMu)]
        # Plot placeholder data
        ys = np.asarray(self._yQueue).T
        for i in range(self._nMu):
            pen = pg.mkPen(color=colors[i])
            self._plots.append(
                self.graphWidget.plot(
                    self._xQueue, ys[i] + self._plotSpacing * i, pen=pen
                )
            )

    @Slot(np.ndarray)
    def _plotData(self, data: np.ndarray):
        """This method is called automatically when the associated signal is received,
        it grabs data from the signal and plots it.

        Parameters
        ----------
        data : ndarray
            Data to plot.
        """
        for samples in data:
            self._xQueue.append(self._xQueue[-1] + 1)
            self._yQueue.append(samples)
        self._bufferCount += data.shape[0]

        if self._bufferCount >= self._bufferSize:
            ys = np.asarray(self._yQueue).T
            for i in range(self._nMu):
                self._plots[i].setData(
                    self._xQueue, ys[i] + self._plotSpacing * i, skipFiniteCheck=True
                )
            self._bufferCount = 0


class _DecompositionConfigWidget(QWidget, Ui_DecompositionConfig):
    """Widget providing configuration options for the decomposition.

    Attributes
    ----------
    model : dict of {str : ndarray} or None
        Dictionary representing the parameters of the BSS model.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setupUi(self)

        self.model = None
        self.browseDecompModelButton.clicked.connect(self._browseModel)

    def _browseModel(self) -> None:
        """Browse to select the .npz file with the BSS model."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load BSS model",
            filter="*.npz",
        )
        displayText = ""
        if filePath:
            with np.load(filePath) as data:
                self.model = {k: v for k, v in data.items()}
            displayText = "NPZ file invalid!" if self.model is None else filePath
        self.decompModelLabel.setText(displayText)


class DecompositionController(QObject):
    """Controller for the decomposition.

    Attributes
    ----------
    confWidget : _DecompositionConfigWidget
        Instance of _DecompositionConfigWidget.
    _muPlotWidget : _MUPlotWidget or None
        Instance of _MUPlotWidget.

    Class attributes
    ----------------
    _dataReadySig : Signal
        Qt signal that forwards the dataReadySig signal from MainWindow.
    """

    _dataReadySig = Signal(np.ndarray)

    def __init__(self) -> None:
        super().__init__()

        self.confWidget = _DecompositionConfigWidget()

        self._muPlotWidget = None

        self._oricaWorker = ORICAWorker()
        self._oricaThread = QThread()
        self._oricaWorker.moveToThread(self._oricaThread)

    def subscribe(self, mainWin: MainWindow) -> None:
        """Subscribe to instance of MainWindow.

        Parameters
        ----------
        mainWin : MainWindow
            Instance of MainWindow.
        """
        mainWin.addConfWidget(self.confWidget)
        mainWin.startStreamingSig.connect(self._startDecomposition)
        mainWin.stopStreamingSig.connect(self._stopDecomposition)
        mainWin.closeSig.connect(self._stopDecomposition)
        mainWin.dataReadyFltSig.connect(self._oricaWorker.decompose)

    def _startDecomposition(self) -> None:
        """Start the decomposition."""
        if (
            self.confWidget.decompGroupBox.isChecked()
            and self.confWidget.model is not None
        ):
            logging.info("DecompositionController: decomposition started.")
            self.confWidget.decompGroupBox.setEnabled(False)

            self._muPlotWidget = _MUPlotWidget(
                nMu=self.confWidget.model["sepMtx"].shape[0]
            )
            self._muPlotWidget.closeSig.connect(self._actualStopDecomposition)
            self._oricaWorker.decompSig.connect(self._muPlotWidget._plotData)
            self._muPlotWidget.show()

            lambda_0 = self.confWidget.lambdaTextField.text()
            lambda_0 = (
                float(lambda_0) if lambda_0.replace(".", "", 1).isdigit() else 1e-3
            )  # force default value
            gamma = self.confWidget.gammaTextField.text()
            gamma = (
                float(gamma) if gamma.replace(".", "", 1).isdigit() else 0.0
            )  # force default value
            self._oricaWorker.lambda_0 = lambda_0
            self._oricaWorker.gamma = gamma
            self._oricaWorker.whiteMtx = self.confWidget.model["whiteMtx"]
            self._oricaWorker.sepMtx = self.confWidget.model["sepMtx"]

            self._oricaThread.start()

    def _stopDecomposition(self) -> None:
        """Stop the decomposition by exploiting MUPlotWidget close event."""
        self._muPlotWidget.close()  # the close event calls the actual stopAcquisition

    def _actualStopDecomposition(self) -> None:
        """Stop the decomposition."""
        if self._oricaThread.isRunning():
            self._oricaThread.quit()
            self._oricaThread.wait()

            logging.info("DecompositionController: decomposition stopped.")
            self.confWidget.decompGroupBox.setEnabled(True)
