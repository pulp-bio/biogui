# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Legacy WULPUS module controller backed by the curated platform implementation.
"""

from __future__ import annotations

from types import MappingProxyType

from PySide6.QtCore import QObject
from PySide6.QtGui import QStandardItem
from PySide6.QtWidgets import QMessageBox

from biogui.controllers import MainController
from biogui.platforms.wulpus import (
    WULPUS_PLATFORM,
    WulpusConfigWidget,
    build_interface_module,
    create_default_config,
    read_current_config,
)
from biogui.views import MainWindow


class WulpusConfigController(QObject):
    """Legacy module entry point that reuses the curated WULPUS platform hooks."""

    def __init__(
        self, streamingControllers: MappingProxyType, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._streamingControllers = streamingControllers
        self._confWidget = WulpusConfigWidget()
        self._mainController: MainController | None = None
        self._confWidget.applyConfigButton.clicked.connect(self._applyConfigHandler)

    def _iter_wulpus_data_sources(self):
        """Iterate over configured data sources that use the curated WULPUS platform."""
        if self._mainController is None:
            return

        for dataSourceId, dataSourceConfig in self._mainController._config.items():
            interfaceModule = dataSourceConfig.get("interfaceModule")
            platformConfig = getattr(interfaceModule, "platformConfig", None)
            if platformConfig is not None and platformConfig.id == WULPUS_PLATFORM.id:
                yield dataSourceId, dataSourceConfig

    def _findDataSourceItem(self, dataSourceId: str) -> QStandardItem | None:
        """Return the top-level tree item corresponding to the given data source."""
        if self._mainController is None:
            return None

        for row in range(self._mainController.dataSourceModel.rowCount()):
            item = self._mainController.dataSourceModel.item(row)
            if item is None:
                continue
            if self._mainController._getDataSourceIdFromItem(item) == dataSourceId:
                return item

        return None

    def subscribe(self, mainController: MainController, mainWin: MainWindow) -> None:
        """Subscribe to the main controller."""
        mainWin.moduleContainer.layout().addWidget(self._confWidget)  # type: ignore
        self._mainController = mainController

        currentConfig = None
        for _, dataSourceConfig in self._iter_wulpus_data_sources():
            currentConfig = read_current_config(dataSourceConfig["interfaceModule"])
            if currentConfig is not None:
                break

        self._confWidget.load_config(currentConfig or create_default_config())

    def unsubscribe(self, mainController: MainController, mainWin: MainWindow) -> None:
        """Unsubscribe from the main controller."""
        mainWin.moduleContainer.layout().removeWidget(self._confWidget)  # type: ignore
        self._confWidget.deleteLater()
        self._mainController = None

    def _applyConfigHandler(self) -> None:
        """Apply the widget configuration to all configured WULPUS data sources."""
        if self._mainController is None:
            return

        wulpusSources = list(self._iter_wulpus_data_sources())
        if not wulpusSources:
            QMessageBox.warning(
                self._confWidget,
                "Configuration Error",
                "No WULPUS data source found in the configuration.",
            )
            return

        try:
            newConfig = self._confWidget.get_current_config()
            self._confWidget.statusLabel.setText("Status: Configuration validated")
        except Exception as err:
            self._confWidget.statusLabel.setText(f"Status: Error - {err}")
            QMessageBox.critical(
                self._confWidget,
                "Configuration Error",
                f"Invalid configuration: {err}",
            )
            return

        for dataSourceId, oldDataSourceConfig in wulpusSources:
            itemToEdit = self._findDataSourceItem(dataSourceId)
            if itemToEdit is None:
                continue

            newDataSourceConfig = {
                key: value for key, value in oldDataSourceConfig.items() if key != "sigsConfigs"
            }
            newDataSourceConfig["interfaceModule"] = build_interface_module(
                oldDataSourceConfig["interfaceModule"],
                newConfig,
            )
            self._mainController._applyEditedDataSourceConfig(
                itemToEdit=itemToEdit,
                oldDataSourceConfig=oldDataSourceConfig,
                newDataSourceConfig=newDataSourceConfig,
            )

        self._confWidget.statusLabel.setText(
            f"Status: Applied configuration to {len(wulpusSources)} WULPUS source(s)"
        )
