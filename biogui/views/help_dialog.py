# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Reusable minimal help dialog for parameter guidance."""

from __future__ import annotations

import base64
import io
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class HelpDialog(QDialog):
    """Minimalistic dialog to display contextual help for a parameter."""

    DIALOG_MIN_WIDTH = 720
    DIALOG_MIN_HEIGHT = 620
    DIALOG_DEFAULT_WIDTH = 820
    DIALOG_DEFAULT_HEIGHT = 700
    FORMULA_MAX_WIDTH_PX = 165

    def __init__(self, title: str, help_content: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(self.DIALOG_MIN_WIDTH, self.DIALOG_MIN_HEIGHT)
        self.resize(self.DIALOG_DEFAULT_WIDTH, self.DIALOG_DEFAULT_HEIGHT)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title_label = QLabel(title, self)
        title_label.setObjectName("helpTitleLabel")
        layout.addWidget(title_label)

        help_view = QTextBrowser(self)
        help_view.setOpenExternalLinks(False)
        help_view.setReadOnly(True)
        help_view.setHtml(self._build_main_html(help_content))
        layout.addWidget(help_view, stretch=1)

        close_button = QPushButton("Close", self)
        close_button.setDefault(True)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.setStyleSheet(
            """
            QDialog {
                background: #ffffff;
            }
            QLabel#helpTitleLabel {
                font-size: 15px;
                font-weight: 600;
                color: #222222;
            }
            QTextBrowser {
                border: 1px solid #d9d9df;
                border-radius: 8px;
                padding: 10px;
                background: #fcfcfe;
                color: #202226;
                font-size: 18px;
                line-height: 1.35em;
            }
            QPushButton {
                min-width: 90px;
                padding: 6px 12px;
            }
            """
        )

    def _build_main_html(self, content: dict) -> str:
        short = escape(content.get("short", ""))
        details = escape(content.get("details", ""))
        units = escape(content.get("units", ""))
        recommended = escape(content.get("recommended", ""))
        notes = escape(content.get("notes", ""))
        formula_latex_raw = str(content.get("formula_latex", "")).strip()

        sections = []
        if short:
            sections.append(f"<p><b>Summary:</b> {short}</p>")
        if units:
            sections.append(f"<p><b>Units:</b> {units}</p>")
        if recommended:
            sections.append(f"<p><b>Recommended:</b> {recommended}</p>")
        if details:
            sections.append(f"<p><b>Details:</b><br>{details}</p>")
        if formula_latex_raw:
            rendered = self._render_latex_to_png_data_uri(formula_latex_raw)
            if rendered is not None:
                sections.append(
                    "<p><b>Rendered:</b></p>"
                    f"<p style='margin-top:4px;margin-bottom:4px;text-align:center;'><img src='{rendered}' style='height:auto;max-width:{self.FORMULA_MAX_WIDTH_PX}px;'></p>"
                )
            else:
                sections.append("<p><i>Could not render formula.</i></p>")
        if notes:
            sections.append(f"<p><b>Notes:</b><br>{notes}</p>")

        return "".join(sections) or "<p>No help available.</p>"

    def _render_latex_to_png_data_uri(self, latex: str) -> str | None:
        """Render LaTeX as a single high-DPI PNG data URI (stable offline path)."""
        try:
            import matplotlib
            from matplotlib import mathtext
            from matplotlib.font_manager import FontProperties
        except Exception:
            return None

        png_buffer = io.BytesIO()
        try:
            with matplotlib.rc_context(
                {
                    "mathtext.fontset": "stix",
                    "mathtext.default": "regular",
                }
            ):
                mathtext.math_to_image(
                    f"${latex}$",
                    png_buffer,
                    dpi=600,
                    format="png",
                    prop=FontProperties(family="STIXGeneral", size=16),
                    color="black",
                )
        except Exception:
            return None

        data = png_buffer.getvalue()
        if not data:
            return None

        encoded = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{encoded}"
