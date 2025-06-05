from __future__ import annotations
import logging

from PySide6.QtCore import QObject, Signal, QByteArray
from PySide6.QtBluetooth import (
    QBluetoothDeviceDiscoveryAgent,
    QBluetoothDeviceInfo,
    QBluetoothUuid,
    QLowEnergyController,
    QLowEnergyService,
    QLowEnergyCharacteristic,
    QBluetoothAddress
)
from PySide6.QtWidgets import QWidget, QMessageBox

from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)
from ..ui.ble_data_source_config_widget_ui import Ui_BLEDataSourceConfigWidget

# Modified BLEConfigWidget to use createCentral()
class BLEConfigWidget(DataSourceConfigWidget, Ui_BLEDataSourceConfigWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)

        # Bluetooth LE device discovery
        self._agent = QBluetoothDeviceDiscoveryAgent(self)
        self.scanButton.clicked.connect(self._startScan)
        self._agent.deviceDiscovered.connect(self._onDeviceDiscovered)

        # UI LE controller
        self._uiController: QLowEnergyController | None = None
        self._serviceObjects: dict[str, QLowEnergyService] = {}

        # Selection signals
        self.deviceComboBox.currentIndexChanged.connect(self._onDeviceSelected)
        self.serviceComboBox.currentIndexChanged.connect(self._onServiceSelected)
        self.connectButton.clicked.connect(self._onConnect)

    def _startScan(self) -> None:
        self.deviceComboBox.clear()
        self.serviceComboBox.clear()
        self.charComboBox.clear()
        if self._uiController:
            self._uiController.disconnectFromDevice()
            self._uiController.deleteLater()
            self._uiController = None
        self._agent.start()

    def _onDeviceDiscovered(self, info: QBluetoothDeviceInfo) -> None:
        # Store full device info for later use
        display = f"{info.name()} ({info.address().toString()})"
        self.deviceComboBox.addItem(display, info)

    def _onDeviceSelected(self, index: int) -> None:
        if index < 0:
            return
        # Retrieve the full QBluetoothDeviceInfo
        info: QBluetoothDeviceInfo = self.deviceComboBox.itemData(index)
        self.serviceComboBox.clear()
        self.charComboBox.clear()
        if self._uiController:
            self._uiController.disconnectFromDevice()
            self._uiController.deleteLater()
            self._uiController = None
        # Use factory method for central role
        self._uiController = QLowEnergyController.createCentral(info, self)
        self._uiController.connected.connect(self._onUITConnected)
        self._uiController.errorOccurred.connect(lambda err: self._showError(str(err)))
        self._uiController.connectToDevice()

    def _onUITConnected(self) -> None:
        if not self._uiController:
            return
        self._uiController.serviceDiscovered.connect(self._onServiceDiscoveredUI)
        self._uiController.discoveryFinished.connect(self._onServiceDiscoveryFinishedUI)
        self._uiController.discoverServices()

    def _onServiceDiscoveredUI(self, uuid: QBluetoothUuid) -> None:
        self.serviceComboBox.addItem(uuid.toString(), uuid)

    def _onServiceDiscoveryFinishedUI(self) -> None:
        if self.serviceComboBox.count() == 0:
            self._showError("No BLE services found on device.")

    def _onServiceSelected(self, index: int) -> None:
        self.charComboBox.clear()
        if index < 0 or not self._uiController:
            return
        uuid: QBluetoothUuid = self.serviceComboBox.itemData(index)
        if uuid.toString() not in self._serviceObjects:
            svc = self._uiController.createServiceObject(uuid, self)
            self._serviceObjects[uuid.toString()] = svc
            svc.stateChanged.connect(self._onServiceStateChangedUI)
            svc.discoverDetails()
        else:
            self._populateCharacteristics(self._serviceObjects[uuid.toString()])

    def _onServiceStateChangedUI(self, state) -> None:
        from PySide6.QtBluetooth import QLowEnergyService

        svc = self.sender()
        if state == QLowEnergyService.ServiceDiscovered and isinstance(svc, QLowEnergyService):
            self._populateCharacteristics(svc)

    def _populateCharacteristics(self, svc: QLowEnergyService) -> None:
        for char in svc.characteristics():
            self.charComboBox.addItem(char.uuid().toString(), char.uuid())

    def _showError(self, message: str) -> None:
        QMessageBox.critical(self, "BLE Error", message)

    def _onConnect(self) -> None:
        if self.deviceComboBox.currentIndex() < 0:
            self._showError("No device selected.")
            return
        if self.serviceComboBox.currentIndex() < 0:
            self._showError("No service selected.")
            return
        if self.charComboBox.currentIndex() < 0:
            self._showError("No characteristic selected.")
            return
        svc_uuid = self.serviceComboBox.itemData(self.serviceComboBox.currentIndex()).toString()
        chr_uuid = self.charComboBox.itemData(self.charComboBox.currentIndex()).toString()
        self.serviceUuidLineEdit.setText(svc_uuid)
        self.charUuidLineEdit.setText(chr_uuid)
        self.configured.emit()

    def validateConfig(self) -> DataSourceConfigResult:
        if self.deviceComboBox.currentIndex() < 0:
            return DataSourceConfigResult(
                DataSourceType.BLE, {}, False, "No BLE device selected."
            )
        if not (self.serviceUuidLineEdit.hasAcceptableInput() and self.charUuidLineEdit.hasAcceptableInput()):
            return DataSourceConfigResult(
                DataSourceType.BLE, {}, False, "Invalid service or characteristic UUID."
            )
        return DataSourceConfigResult(
            DataSourceType.BLE,
            {
                "deviceAddress": self.deviceComboBox.currentData().address().toString(),
                "serviceUuid":    self.serviceUuidLineEdit.text(),
                "charUuid":       self.charUuidLineEdit.text(),
            },
            True,
            "",
        )

    def prefill(self, config: dict) -> None:
        pass

    def getFieldsInTabOrder(self) -> list[QWidget]:
        return [
            self.scanButton,
            self.deviceComboBox,
            self.serviceComboBox,
            self.charComboBox,
            self.connectButton,
            self.serviceUuidLineEdit,
            self.charUuidLineEdit,
        ]

class BLEDataSourceWorker(DataSourceWorker):
    """
    DataSourceWorker for a BLE peripheral characteristic.
    Emits dataPacketReady(bytes) whenever the characteristic notifies.
    """

    def __init__(self, deviceAddress: str, serviceUuid: str, charUuid: str) -> None:
        super().__init__()
        self._deviceAddress = deviceAddress
        self._svcUuid  = QBluetoothUuid(serviceUuid)
        self._chrUuid  = QBluetoothUuid(charUuid)

        self._controller: QLowEnergyController | None = None
        self._service:    QLowEnergyService    | None = None
        self._characteristic: QLowEnergyCharacteristic | None = None
        self._stopFlag = False

    def __str__(self) -> str:
        return f"BLE – {self._deviceAddress}"

    def startCollecting(self) -> None:
        self._stopFlag = False
        # Reconstruct QBluetoothDeviceInfo for central controller
        addr = QBluetoothDeviceInfo(QBluetoothAddress(self._deviceAddress))
        self._controller = QLowEnergyController.createCentral(addr, self)
        self._controller.connected.connect(self._onConnected)
        self._controller.errorOccurred.connect(
            lambda err: self.errorOccurred.emit(str(err))
        )
        self._controller.connectToDevice()

    def _onConnected(self) -> None:
        if not self._controller:
            return
        self._controller.serviceDiscovered.connect(self._onServiceDiscovered)
        self._controller.discoveryFinished.connect(self._onDiscoveryFinished)
        self._controller.discoverServices()

    def _onServiceDiscovered(self, uuid: QBluetoothUuid) -> None:
        if uuid == self._svcUuid and self._controller:
            self._service = self._controller.createServiceObject(uuid, self)

    def _onDiscoveryFinished(self) -> None:
        if not self._service:
            self.errorOccurred.emit("BLE service not found")
            return

        self._service.stateChanged.connect(self._onServiceStateChanged)
        self._service.characteristicChanged.connect(self._onCharacteristicChanged)
        self._service.discoverDetails()

    def _onServiceStateChanged(self, state) -> None:
        from PySide6.QtBluetooth import QLowEnergyService
        if state == QLowEnergyService.ServiceDiscovered and self._service:
            self._characteristic = self._service.characteristic(self._chrUuid)
            if not self._characteristic.isValid():
                self.errorOccurred.emit("BLE characteristic not found")
                return
            desc = self._characteristic.descriptor(
                QBluetoothUuid.DescriptorType.ClientCharacteristicConfiguration
            )
            if desc.isValid():
                self._service.writeDescriptor(desc, QByteArray(b"\x01\x00"))

    def _onCharacteristicChanged(
        self, char: QLowEnergyCharacteristic, value: QByteArray
    ) -> None:
        self.dataPacketReady.emit(bytes(value))

    def stopCollecting(self) -> None:
        self._stopFlag = True
        if self._service and self._characteristic:
            desc = self._characteristic.descriptor(
                QBluetoothUuid.DescriptorType.ClientCharacteristicConfiguration
            )
            if desc.isValid():
                self._service.writeDescriptor(desc, QByteArray(b"\x00\x00"))
        if self._controller:
            self._controller.disconnectFromDevice()
            self._controller.deleteLater()
        if self._service:
            self._service.deleteLater()
