# biogui/biogui/views/wulpus_config_dialog.py
# Ersetze die ganze Datei mit:

"""Dialog for configuring WULPUS hardware parameters."""

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
            config = self.configWidget.get_current_config()
            self._config = config
            self.configWidget.statusLabel.setText("Status: Configuration validated")
            super().accept()
        except Exception as e:
            self.configWidget.statusLabel.setText(f"Status: Error - {str(e)}")
            QMessageBox.critical(
                self, "Configuration Error", f"Invalid configuration: {str(e)}"
            )

    def get_config(self) -> WulpusUssConfig | None:
        return self._config
