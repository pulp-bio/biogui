# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Layout manager for signal plot widgets.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLayout, QVBoxLayout, QWidget


class PlotLayoutManager:
    """Manage plot widgets in single-column or two-column layout."""

    MODE_SINGLE = "single"
    MODE_TWO_COLUMN = "two_column"

    def __init__(self, container: QWidget) -> None:
        self._container = container
        self._outer = container.layout()
        if self._outer is None:
            self._outer = QVBoxLayout(container)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._widgets: list[QWidget] = []
        self._mode = self.MODE_SINGLE

    @property
    def mode(self) -> str:
        return self._mode

    def setTwoColumn(self, enabled: bool) -> None:
        """Switch between single-column and two-column layout."""
        mode = self.MODE_TWO_COLUMN if enabled else self.MODE_SINGLE
        if mode == self._mode:
            return
        self._mode = mode
        self._rebuild()

    def addWidget(self, widget: QWidget) -> None:
        self._widgets.append(widget)
        self._rebuild()

    def removeWidget(self, widget: QWidget) -> None:
        self._widgets.remove(widget)
        self._rebuild()

    def replaceWidget(self, oldWidget: QWidget, newWidget: QWidget) -> None:
        index = self._widgets.index(oldWidget)
        self._widgets[index] = newWidget
        self._rebuild()

    def _rebuild(self) -> None:
        self._clearLayout(self._outer)
        if not self._widgets:
            return

        if self._mode == self.MODE_SINGLE:
            column = QVBoxLayout()
            self._outer.addLayout(column)
            for widget in self._widgets:
                column.addWidget(widget)
            return

        grid = QVBoxLayout()
        self._outer.addLayout(grid)
        index = 0
        while index < len(self._widgets):
            remaining = len(self._widgets) - index
            row = QHBoxLayout()
            row.addWidget(self._widgets[index], 1)
            if remaining == 1:
                grid.addLayout(row)
                break
            row.addWidget(self._widgets[index + 1], 1)
            grid.addLayout(row)
            index += 2

    @staticmethod
    def _clearLayout(layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            if childLayout := item.layout():
                PlotLayoutManager._clearLayout(childLayout)
                childLayout.deleteLater()
