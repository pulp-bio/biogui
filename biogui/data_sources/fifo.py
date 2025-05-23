"""
Classes for the FIFO data source.


Copyright 2024 Mattia Orlandi, Pierangelo Maria Rapa

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

from PySide6.QtWidgets import QWidget

from ..ui.fifo_data_source_config_widget_ui import Ui_FifoDataSourceConfigWidget
from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)


class FIFOConfigWidget(DataSourceConfigWidget, Ui_FifoDataSourceConfigWidget):
    """
    Widget to configure the FIFO source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self.destroyed.connect(self.deleteLater)

    def validateConfig(self) -> DataSourceConfigResult:
        """
        Validate the configuration.

        Returns
        -------
        DataSourceConfigResult
            Configuration result.
        """
        if self.fifoPathTextField.text() == "":
            return DataSourceConfigResult(
                dataSourceType=DataSourceType.FIFO,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "path to FIFO" field is empty.',
            )

        return DataSourceConfigResult(
            dataSourceType=DataSourceType.FIFO,
            dataSourceConfig={"fifoPath": self.fifoPathTextField.text()},
            isValid=True,
            errMessage="",
        )

    def prefill(self, config: dict) -> None:
        """Pre-fill the form with the provided configuration.

        Parameters
        ----------
        config : dict
            Dictionary with the configuration.
        """
        if "fifoPath" in config:
            self.fifoPathTextField.setText(config["fifoPath"])

    def getFieldsInTabOrder(self) -> list[QWidget]:
        """
        Get the list of fields in tab order.

        Returns
        -------
        list of QWidgets
            List of the QWidgets in tab order.
        """
        return [self.fifoPathTextField]


class FIFODataSourceWorker(DataSourceWorker):
    """
    Concrete DataSourceWorker that collects data from a FIFO.

    Parameters
    ----------
    packetSize : int
        Number of bytes in the packet.
    startSeq : list of bytes
        Sequence of commands to start the source.
    stopSeq : list of bytes
        Sequence of commands to stop the source.
    fifoPath : str
        Path to the FIFO.

    Attributes
    ----------
    _packetSize : int
        Number of bytes in the packet (for compatibility with other data sources).
    _startSeq : list of bytes
        Sequence of commands to start the source.
    _stopSeq : list of bytes
        Sequence of commands to stop the source.
    _stopReadingFlag : bool
        Flag indicating to stop reading data.

    Class attributes
    ----------------
    dataPacketReady : Signal
        Qt Signal emitted when new data is collected.
    errorOccurred : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(
        self,
        packetSize: int,
        startSeq: list[bytes],
        stopSeq: list[bytes],
        fifoPath: str,
    ) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._fifoPath = fifoPath
        self._stopReadingFlag = False

        self.destroyed.connect(self.deleteLater)

    def __str__(self):
        return f"FIFO - {self._fifoPath}"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        self._stopReadingFlag = False

        logging.info("DataWorker: data reading started.")

        try:
            with open(self._fifoPath, "rb") as f:
                while not self._stopReadingFlag:
                    data = f.read(self._packetSize)

                    self.dataPacketReady.emit(data)
        except OSError as e:
            errMsg = f"Cannot open FIFO due to the following exception:\n{e}."
            self.errorOccurred.emit(errMsg)
            logging.error(f"DataSourceWorker: {errMsg}")
            return

        logging.info("DataWorker: data reading stopped.")

    def stopCollecting(self) -> None:
        """Stop data collection."""
        self._stopReadingFlag = True
