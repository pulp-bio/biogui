# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Dialog for configuring WULPUS hardware parameters.
"""

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QVBoxLayout

from biogui.platforms.wulpus import WulpusUssConfig
from biogui.views.wulpus_config_widget import WulpusConfigWidget


class WulpusConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WULPUS Configuration")
        self.resize(650, 750)

        layout = QVBoxLayout(self)
        self.configWidget = WulpusConfigWidget(self)
        layout.addWidget(self.configWidget)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)  # type: ignore
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

        self._config = None

    def accept(self):
        try:
            self._config = self.configWidget.get_current_config()
            self.configWidget.statusLabel.setText("Status: Configuration validated")
            super().accept()
        except Exception as e:
            self.configWidget.statusLabel.setText(f"Status: Error - {str(e)}")
            QMessageBox.critical(self, "Configuration Error", f"Invalid configuration: {str(e)}")

    def get_config(self) -> WulpusUssConfig | None:
        return self._config
