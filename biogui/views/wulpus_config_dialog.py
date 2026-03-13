# Copyright ETH Zurich - University of Bologna 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Dialog for configuring WULPUS hardware parameters.


Copyright 2025 Enzo Baraldi

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

import sys
from pathlib import Path

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QVBoxLayout

interfaces_path = Path(__file__).parent.parent.parent / "interfaces"
if str(interfaces_path) not in sys.path:
    sys.path.insert(0, str(interfaces_path))

from interface_wulpus import WulpusUssConfig

from biogui.views.wulpus_config_widget import WulpusConfigWidget


class WulpusConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WULPUS Configuration")
        self.resize(650, 750)

        layout = QVBoxLayout(self)
        self.configWidget = WulpusConfigWidget(self)
        layout.addWidget(self.configWidget)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
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
