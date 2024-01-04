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

import logging
from collections import deque

import numpy as np
import pyqtgraph as pg
import serial.tools.list_ports
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QDialog, QMainWindow, QMessageBox, QWidget

from ._streaming import StreamingController
from ._ui.ui_add_signal_dialog import Ui_AddSignalDialog
from ._ui.ui_main_window import Ui_MainWindow
from ._ui.ui_serial_conf_widget import Ui_SerialConfWidget
from ._ui.ui_signal_plots_widget import Ui_SignalPlotsWidget
from ._ui.ui_socket_conf_widget import Ui_SocketConfWidget


def _serialPorts() -> list[str]:
    """Lists serial port names.

    Returns
    -------
    list of str
        A list of the serial ports available on the system.
    """
    return [info[0] for info in serial.tools.list_ports.comports()]


class _SerialConfWidget(QWidget, Ui_SerialConfWidget):
    """Widget to configure the serial source."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self._rescanSerialPorts()
        self.rescanSerialPortsButton.clicked.connect(self._rescanSerialPorts)

    def _rescanSerialPorts(self) -> None:
        """Rescan the serial ports to update the combo box."""
        self.serialPortsComboBox.clear()
        self.serialPortsComboBox.addItems(_serialPorts())


class _SocketConfWidget(QWidget, Ui_SocketConfWidget):
    """Widget to configure the socket source."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        # Validation rules
        minPort, maxPort = 1024, 49151
        self.portTextField.setToolTip(f"Integer between {minPort} and {maxPort}")
        portValidator = QIntValidator(bottom=minPort, top=maxPort)
        self.portTextField.setValidator(portValidator)


class _AddSignalDialog(QDialog, Ui_AddSignalDialog):
    """Dialog for adding a new signal to plot.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self.buttonBox.accepted.connect(self._parseValidateForm)
        self.buttonBox.rejected.connect(self.close)
        self.filtTypeComboBox.currentTextChanged.connect(self._onFiltTypeChange)

        # Validation rules
        minCh, maxCh = 1, 64
        nDec = 3
        minFreq, maxFreq = 1 * 10 ** (-nDec), 20_000.0
        minOrd, maxOrd = 1, 8

        self.nChTextField.setToolTip(f"Integer between {minCh} and {maxCh}")
        nChValidator = QIntValidator(bottom=minCh, top=maxCh)
        self.nChTextField.setValidator(nChValidator)

        self.fsTextField.setToolTip(f"Float between {minFreq:.3f} and {maxFreq:.3f}")
        fsValidator = QDoubleValidator(bottom=minFreq, top=maxFreq, decimals=nDec)
        fsValidator.setNotation(QDoubleValidator.StandardNotation)  # type: ignore
        self.fsTextField.setValidator(fsValidator)

        self.freq1TextField.setToolTip(
            f"Float between {minFreq:.3f} and {maxFreq / 2:.3f}"
        )
        self.freq2TextField.setToolTip(
            f"Float between {minFreq:.3f} and {maxFreq / 2:.3f}"
        )
        freqValidator = QDoubleValidator(bottom=minFreq, top=maxFreq / 2, decimals=nDec)
        freqValidator.setNotation(QDoubleValidator.StandardNotation)  # type: ignore
        self.freq1TextField.setValidator(freqValidator)
        self.freq2TextField.setValidator(freqValidator)

        self.filtOrderTextField.setToolTip(f"Integer between {minOrd} and {maxOrd}")
        orderValidator = QIntValidator(bottom=minOrd, top=maxOrd)
        self.filtOrderTextField.setValidator(orderValidator)

        self._signalSettings = {}
        self._isValid = False
        self._errMessage = ""

    @property
    def signalSettings(self) -> dict:
        """dict: Property for getting the dictionary of the signal settings."""
        return self._signalSettings

    @property
    def isValid(self) -> bool:
        """bool: Property representing whether the form is valid."""
        return self._isValid

    @property
    def errMessage(self) -> str:
        """str: Property for getting the error message if the form is not valid."""
        return self._errMessage

    def _onFiltTypeChange(self) -> None:
        """Detect if filter type has changed."""
        filtType = self.filtTypeComboBox.currentText()
        # Disable field for second frequency depending on the filter type
        if filtType in ("highpass", "lowpass"):
            self.freq2TextField.setEnabled(False)
            self.freq2TextField.clear()
        else:
            self.freq2TextField.setEnabled(True)

    def _parseValidateForm(self) -> None:
        """Validate user input in the form."""
        # Check basic settings
        if not self.sigNameTextField.hasAcceptableInput():
            self._isValid = False
            self._errMessage = 'The "signal name" field is empty.'
            return
        self._signalSettings["sigName"] = self.sigNameTextField.text()

        if not self.nChTextField.hasAcceptableInput():
            self._isValid = False
            self._errMessage = 'The "number of channels" field is invalid.'
            return
        self._signalSettings["nCh"] = int(self.nChTextField.text())

        if not self.fsTextField.hasAcceptableInput():
            self._isValid = False
            self._errMessage = 'The "sampling frequency" field is invalid.'
            return
        self._signalSettings["fs"] = float(self.fsTextField.text())
        nyq_fs = self._signalSettings["fs"] // 2

        # Check filtering settings
        if self.filteringGroupBox.isChecked():
            self._signalSettings["filtType"] = self.filtTypeComboBox.currentText()

            if not self.freq1TextField.hasAcceptableInput():
                self._isValid = False
                self._errMessage = 'The "Frequency 1" field is invalid.'
                return
            freq1 = float(self.freq1TextField.text())

            if freq1 >= nyq_fs:
                self._isValid = False
                self._errMessage = "The 1st critical frequency cannot be higher than Nyquist frequency."
                return
            self._signalSettings["freqs"] = [freq1]

            if self.freq2TextField.isEnabled():
                if not self.freq2TextField.hasAcceptableInput():
                    self._isValid = False
                    self._errMessage = 'The "Frequency 2" field is invalid.'
                    return
                freq2 = float(self.freq2TextField.text())

                if freq2 >= nyq_fs:
                    self._isValid = False
                    self._errMessage = "The 2nd critical frequency cannot be higher than Nyquist frequency."
                    return
                if freq2 <= freq1:
                    self._isValid = False
                    self._errMessage = "The 2nd critical frequency cannot be lower than the 1st critical frequency."
                    return
                self._signalSettings["freqs"].append(float(self.freq2TextField.text()))

            if not self.filtOrderTextField.hasAcceptableInput():
                self._isValid = False
                self._errMessage = 'The "filter order" field is invalid.'
                return
            self._signalSettings["filtOrder"] = int(self.filtOrderTextField.text())

        self._isValid = True


class _SignalPlots(QWidget, Ui_SignalPlotsWidget):
    """Widget showing real-time plots of a signal.

    Parameters
    ----------
    sigName : str
        Name of the signal to display.
    nCh : int
        Number of channels.
    fs : float
        Sampling frequency.

    Attributes
    ----------
    _fs : float
        Sampling frequency.
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
    """

    def __init__(
        self, sigName: str, nCh: int, fs: float, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.setupUi(self)

        renderLength_ms = 1000  # 1s
        renderLength = int(round(renderLength_ms / 1000 * fs))
        self._xQueue = deque(maxlen=renderLength)
        self._yQueue = deque(maxlen=renderLength)
        self._nCh = nCh
        self._fs = fs
        self._bufferCount = 0
        self._bufferSize = 200
        self._plotSpacing = 1000

        # Initialize plots
        self.sigNameLabel.setText(sigName)
        self._plots = []
        self._initializePlots()

    @property
    def nCh(self) -> int:
        """int: Propertu for getting the number of channels."""
        return self._nCh

    def _initializePlots(self) -> None:
        """Render the initial plot."""
        # Reset graph
        self.graphWidget.clear()
        self.graphWidget.setYRange(0, self._plotSpacing * (self._nCh - 1))
        self.graphWidget.getPlotItem().hideAxis("bottom")  # type: ignore
        self.graphWidget.getPlotItem().hideAxis("left")  # type: ignore

        # Initialize queues
        for i in range(-self._xQueue.maxlen, 0):  # type: ignore
            self._xQueue.append(i / self._fs)
            self._yQueue.append(np.zeros(self._nCh))

        # Get colormap
        cm = pg.colormap.get("CET-C1")  # type: ignore
        cm.setMappingMode("diverging")  # type: ignore
        lut = cm.getLookupTable(nPts=self._nCh, mode="qcolor")  # type: ignore

        # Plot placeholder data
        ys = np.asarray(self._yQueue).T
        for i in range(self._nCh):
            pen = pg.mkPen(color=lut[i])
            self._plots.append(
                self.graphWidget.plot(
                    self._xQueue, ys[i] + self._plotSpacing * i, pen=pen
                )
            )

    def plotData(self, data: np.ndarray) -> None:
        """Plot the given data.

        Parameters
        ----------
        data : ndarray
            Data to plot.
        """
        for samples in data:
            self._xQueue.append(self._xQueue[-1] + 1 / self._fs)
            self._yQueue.append(samples)
        self._bufferCount += data.shape[0]

        if self._bufferCount >= self._bufferSize:
            ys = np.asarray(self._yQueue).T
            for i in range(self._nCh):
                self._plots[i].setData(
                    self._xQueue,
                    ys[i] + self._plotSpacing * (self._nCh - i),
                    skipFiniteCheck=True,
                )
            self._bufferCount = 0


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window.

    Parameters
    ----------


    Attributes
    ----------
    _sourceConfWidget : QWidget
        Widget for configuring the source (serial port or socket).
    _plotWidgets : list of _SignalPlots
        List of _SignalPlots objects.

    Class attributes
    ----------------
    startStreamingSig : Signal
        Qt signal emitted when streaming starts.
    stopStreamingSig : Signal
        Qt signal emitted when streaming stops.
    closeSig : Signal
        Qt signal emitted when the application is closed.
    dataReadySig : Signal
        Qt signal emitted when new data is available.
    dataReadyFltSig : Signal
        Qt signal emitted when new filtered data is available.
    """

    startStreamingSig = Signal()
    stopStreamingSig = Signal()
    closeSig = Signal()
    dataReadySig = Signal(np.ndarray)
    dataReadyFltSig = Signal(np.ndarray)

    def __init__(self) -> None:
        super().__init__()

        self.setupUi(self)

        # Handle source type
        self.sourceComboBox.currentTextChanged.connect(self._onSourceChange)
        self._sourceConfWidget = _SerialConfWidget(self)  # default is serial port
        self.sourceConfContainer.addWidget(self._sourceConfWidget)

        # Handle signal addition/removal/move
        self.addSignalButton.clicked.connect(self._addSignal)
        self.deleteSignalButton.clicked.connect(self._deleteSignal)
        self.signalList.itemClicked.connect(
            lambda: self.deleteSignalButton.setEnabled(True)
        )
        self.moveUpButton.clicked.connect(lambda: self._moveSignal(up=True))
        self.moveDownButton.clicked.connect(lambda: self._moveSignal(up=False))
        self.signalList.itemClicked.connect(self._enableMoveButtons)

        # Handle start/stop streaming
        self.startStreamingButton.clicked.connect(self._startStreaming)
        self.stopStreamingButton.clicked.connect(self._stopStreaming)

        # Streaming controller
        self._streamController = StreamingController(nCh=19, sampFreq=4000)
        self._streamController.commErrorSig.connect(self._displayAlert)
        self._streamController.dataReadyFltSig.connect(self._handleData)
        self._streamController.dataReadySig.connect(
            lambda d: self.dataReadySig.emit(d)
        )  # forward Qt Signal for raw data

        self._plotWidgets = []

    def _onSourceChange(self) -> None:
        """Detect if source type has changed."""
        # Clear container
        self.sourceConfContainer.removeWidget(self._sourceConfWidget)
        self._sourceConfWidget.deleteLater()

        # Add new widget
        sourceConfWidgetDict = {
            "Serial port": _SerialConfWidget,
            "Socket": _SocketConfWidget,
            "Dummy": QWidget,
        }
        self._sourceConfWidget = sourceConfWidgetDict[
            self.sourceComboBox.currentText()
        ](self)
        self.sourceConfContainer.addWidget(self._sourceConfWidget)

    def _addSignal(self) -> None:
        """Add a new signal."""
        # Open the dialog
        self._openAddSignalDialog()

    def _openAddSignalDialog(self, addSignalDialog: _AddSignalDialog | None = None):
        """Open the dialog for adding signals."""
        if addSignalDialog is None:
            addSignalDialog = _AddSignalDialog(self)

        accepted = addSignalDialog.exec()
        if accepted:
            # Check if input is valid
            if not addSignalDialog.isValid:
                QMessageBox.critical(
                    self,
                    "Invalid signal",
                    addSignalDialog.errMessage,
                    buttons=QMessageBox.Retry,  # type: ignore
                    defaultButton=QMessageBox.Retry,  # type: ignore
                )
                self._openAddSignalDialog(addSignalDialog)  # re-open dialog
                return

            # Display signal information
            sigName = addSignalDialog.signalSettings["sigName"]
            nCh = addSignalDialog.signalSettings["nCh"]
            fs = addSignalDialog.signalSettings["fs"]
            self.signalList.addItem(f"{sigName} - {nCh} channels @ {fs}sps")

            # Create plot widget
            plotWidget = _SignalPlots(sigName, nCh, fs, self)
            self._plotWidgets.append(plotWidget)
            self.plotsLayout.addWidget(plotWidget)
            # Re-adjust layout
            for i, plotWidget_ in enumerate(self._plotWidgets):
                self.plotsLayout.setStretch(i, plotWidget_.nCh)

    def _deleteSignal(self) -> None:
        """Delete the selected signal."""
        # Remove list item and plot widget
        idxToRemove = self.signalList.currentRow()
        self.signalList.takeItem(idxToRemove)
        plotWidgetToRemove = self._plotWidgets.pop(idxToRemove)
        self.plotsLayout.removeWidget(plotWidgetToRemove)
        plotWidgetToRemove.deleteLater()

        nSig = self.signalList.count()
        if nSig < 2:
            self.moveUpButton.setEnabled(False)
            self.moveDownButton.setEnabled(False)
            if nSig == 0:
                self.deleteSignalButton.setEnabled(False)

    def _enableMoveButtons(self) -> None:
        """Enable buttons to move signals up/down."""
        flag = self.signalList.count() >= 2
        self.moveUpButton.setEnabled(flag)
        self.moveDownButton.setEnabled(flag)

    def _moveSignal(self, up: bool) -> None:
        """Move signal up/down."""
        # Get the indexes of the elements to swap
        idxFrom = self.signalList.currentRow()
        idxTo = (
            max(0, idxFrom - 1) if up else min(self.signalList.count() - 1, idxFrom + 1)
        )
        if idxFrom == idxTo:
            return

        # Swap list items and plot widgets
        item = self.signalList.takeItem(idxFrom)
        self.signalList.insertItem(idxTo, item)
        plotWidget = self._plotWidgets.pop(idxFrom)
        self._plotWidgets.insert(idxTo, plotWidget)
        self.plotsLayout.removeWidget(plotWidget)
        self.plotsLayout.insertWidget(idxTo, plotWidget)
        # Re-adjust layout
        for i, plotWidget_ in enumerate(self._plotWidgets):
            self.plotsLayout.setStretch(i, plotWidget_.nCh)

    def _startStreaming(self) -> None:
        """Start streaming."""
        logging.info("MainWindow: streaming started.")

        # Attempt to create streaming controller

        # Handle UI elements
        self.startStreamingButton.setEnabled(False)
        self.stopStreamingButton.setEnabled(True)
        self.streamConfGroupBox.setEnabled(False)

        self.startStreamingSig.emit()
        self._streamController.startStreaming()

    def _stopStreaming(self) -> None:
        """Stop streaming."""
        self._streamController.stopStreaming()
        self.stopStreamingSig.emit()

        # Handle UI elements
        self.streamConfGroupBox.setEnabled(True)
        self.startStreamingButton.setEnabled(True)
        self.stopStreamingButton.setEnabled(False)

        logging.info("MainWindow: streaming stopped.")

    def _displayAlert(self) -> None:
        """Alert message displayed when communication fails."""
        self._alert = QMessageBox.critical(
            self,
            "Communication failed",
            "Could not communicate with the device.",
            buttons=QMessageBox.Retry,  # type: ignore
            defaultButton=QMessageBox.Retry,  # type: ignore
        )
        self._stopStreaming()

    @Slot(np.ndarray)
    def _handleData(self, data: np.ndarray) -> None:
        """Handler for the Qt Signal associated to the receiving of new data."""
        # Plot data
        i = 0
        for plotWidget in self._plotWidgets:
            plotWidget.plotData(data[:, i : i + plotWidget.nCh])
            i += plotWidget.nCh
        # Forward signal
        self.dataReadyFltSig.emit(data)
