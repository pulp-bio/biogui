"""
Classes for the microphone data source.

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

from PySide6.QtCore import QByteArray, QIODevice
from PySide6.QtGui import QIntValidator
from PySide6.QtMultimedia import (
    QAudio,
    QAudioFormat,
    QAudioSource,
    QAudioDevice,
    QMediaDevices,
)
from PySide6.QtWidgets import QWidget

from ..ui.microphone_data_source_config_widget_ui import (
    Ui_MicrophoneDataSourceConfigWidget,
)
from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)


class MicrophoneConfigWidget(
    DataSourceConfigWidget, Ui_MicrophoneDataSourceConfigWidget
):
    """
    Widget to configure the system microphone audio source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)

        # Populate available input devices
        devices = QMediaDevices.audioInputs()
        self.audioDeviceComboBox.addItems([dev.description() for dev in devices])

        # Validation for sample rate (Hz)
        self.sampleRateTextField.setValidator(QIntValidator(8000, 192000, self))
        # Set default values
        self.sampleRateTextField.setText("48000")

        self.destroyed.connect(self.deleteLater)

    def validateConfig(self) -> DataSourceConfigResult:
        if not (device := self.audioDeviceComboBox.currentText()):
            return DataSourceConfigResult(
                DataSourceType.MIC,
                {},
                False,
                'The "audio device" field is empty.',
            )
        if not self.sampleRateTextField.hasAcceptableInput():
            return DataSourceConfigResult(
                DataSourceType.MIC,
                {},
                False,
                'The "sample rate" field is invalid.',
            )

        # check smapling rate supported by device
        devices = QMediaDevices.audioInputs()
        selected_device: QAudioDevice | None = next(
            (d for d in devices if d.description() == device),
            None,
        )
        if not selected_device:
            return DataSourceConfigResult(
                DataSourceType.MIC,
                {},
                False,
                "Selected audio device is not available.",
            )

        fmt = QAudioFormat()
        fmt.setSampleRate(int(self.sampleRateTextField.text()))
        # It might be modifiable in the future
        fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        if not selected_device.isFormatSupported(fmt):
            return DataSourceConfigResult(
                DataSourceType.MIC,
                {},
                False,
                f"Selected audio device does not support the sample rate of {self.sampleRateTextField.text()} Hz., sample rate must be between {selected_device.minimumSampleRate()} and {selected_device.maximumSampleRate()} Hz.",
            )

        return DataSourceConfigResult(
            dataSourceType=DataSourceType.MIC,
            dataSourceConfig={
                "deviceName": device,
                "sampleRate": int(self.sampleRateTextField.text()),
            },
            isValid=True,
            errMessage="",
        )

    def prefill(self, config: dict) -> None:
        if device := config.get("deviceName"):
            self.audioDeviceComboBox.setCurrentText(device)
        if rate := config.get("sampleRate"):
            self.sampleRateTextField.setText(str(rate))

    def getFieldsInTabOrder(self) -> list[QWidget]:
        return [
            self.audioDeviceComboBox,
            self.sampleRateTextField,
        ]


class MicrophoneDataSourceWorker(DataSourceWorker):
    """
    Collects audio data from the system microphone (mono) using QAudioSource.

    Constructor signature matches getDataSourceWorker factory:
      (packetSize, startSeq, stopSeq, deviceName, sampleRate)
    """

    def __init__(
        self,
        packetSize: int,
        startSeq: list[bytes],
        stopSeq: list[bytes],
        deviceName: str,
        sampleRate: int,
    ) -> None:
        super().__init__()
        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._deviceName = deviceName
        self._sampleRate = sampleRate

        # Setup audio format (mono, SignedInt16)
        fmt = QAudioFormat()
        fmt.setSampleRate(sampleRate)
        fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        # Select device (fallback to default)
        devices = QMediaDevices.audioInputs()
        self._device = next(
            (d for d in devices if d.description() == deviceName),
            QMediaDevices.defaultAudioInput(),
        )
        # Check format support
        if not self._device.isFormatSupported(fmt):
            fmt = self._device.preferredFormat()
        self.fmt = fmt

        # Use QAudioSource for input
        # self._audioSource = QAudioSource(self._device, self.fmt, self)
        self._buffer = QByteArray()
        self._ioDevice: QIODevice | None = None
        self.destroyed.connect(self.deleteLater)

    def __str__(self) -> str:
        return f"Microphone - {self._device.description()} @ {self._sampleRate}Hz"

    def startCollecting(self) -> None:
        """Begin streaming audio."""
        self._audioSource = QAudioSource(self._device, self.fmt, self)
        # Tune buffer size to match packetSize and reduce latency
        try:
            self._audioSource.setBufferSize(self._packetSize)
        except AttributeError:
            logging.warning(
                "DataWorker: setBufferSize not available on this Qt version."
            )(self._device, self.fmt, self)
        # Clean up any previous I/O device
        if self._ioDevice is not None:
            try:
                self._ioDevice.readyRead.disconnect(self._collectData)  # type: ignore
            except Exception:
                pass
            self._ioDevice.close()
            self._buffer.clear()

        # Ensure the audio source is stopped before restarting
        if self._audioSource.state() == QAudio.State.ActiveState:
            self._audioSource.stop()

        # Start and hook up the new I/O device
        self._ioDevice = self._audioSource.start()
        self._ioDevice.readyRead.connect(self._collectData)  # type: ignore
        logging.info("DataWorker: microphone audio collection started.")

    def stopCollecting(self) -> None:
        """Halt audio streaming."""
        # Stop the audio source
        if self._audioSource.state() == QAudio.State.ActiveState:
            self._audioSource.stop()

        # Disconnect and close the I/O device
        if self._ioDevice is not None:
            try:
                self._ioDevice.readyRead.disconnect(self._collectData)  # type: ignore
            except Exception:
                pass
            self._ioDevice.close()
            self._ioDevice = None

        # Clear any buffered data
        self._buffer.clear()
        logging.info("DataWorker: microphone audio collection stopped.")

    def _collectData(self) -> None:
        """Emit fixed-size packets from the audio buffer."""
        if not self._ioDevice:
            return

        # Accumulate new data
        self._buffer.append(self._ioDevice.readAll())

        # Emit all data packets in the buffer
        while self._buffer.size() >= self._packetSize:
            packet = self._buffer.left(self._packetSize)
            self.dataPacketReady.emit(packet.data())
            self._buffer.remove(0, self._packetSize)
