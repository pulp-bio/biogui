# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
Draggable sidebar splitter with click-to-collapse handle.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent, QPainter, QPolygon
from PySide6.QtWidgets import QSplitter, QSplitterHandle, QWidget


class SidebarSplitterHandle(QSplitterHandle):
    """Splitter handle: drag to resize, click (without drag) to collapse/expand."""

    ARROW_SIZE = 6
    DRAG_THRESHOLD = 5

    arrowClicked = Signal()

    def __init__(self, orientation: Qt.Orientation, parent: QSplitter) -> None:
        super().__init__(orientation, parent)
        self._press_pos: QPoint | None = None
        self._drag_started = False
        self.setCursor(Qt.CursorShape.SplitHCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.pos()
            self._drag_started = False
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._press_pos is None:
            super().mouseMoveEvent(event)
            return

        if not self._drag_started:
            if (event.pos() - self._press_pos).manhattanLength() < self.DRAG_THRESHOLD:
                event.accept()
                return
            self._drag_started = True
            super().mousePressEvent(
                QMouseEvent(
                    QEvent.Type.MouseButtonPress,
                    self._press_pos,
                    self.mapToGlobal(self._press_pos),
                    Qt.MouseButton.LeftButton,
                    Qt.MouseButton.LeftButton,
                    event.modifiers(),
                )
            )

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos is not None:
            if self._drag_started:
                super().mouseReleaseEvent(event)
            else:
                self.arrowClicked.emit()
                event.accept()
            self._press_pos = None
            self._drag_started = False
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().color(self.palette().ColorRole.Window))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = self.palette().color(self.palette().ColorRole.WindowText)
        painter.setPen(color)

        splitter = self.splitter()
        collapsed = isinstance(splitter, SidebarSplitter) and splitter.isSidebarCollapsed()
        self._drawArrow(painter, self.rect(), points_left=not collapsed)

    @staticmethod
    def _drawArrow(painter: QPainter, rect, *, points_left: bool) -> None:
        center = rect.center()
        half = SidebarSplitterHandle.ARROW_SIZE
        if points_left:
            points = [
                QPoint(center.x() + half // 2, center.y() - half),
                QPoint(center.x() - half // 2, center.y()),
                QPoint(center.x() + half // 2, center.y() + half),
            ]
        else:
            points = [
                QPoint(center.x() - half // 2, center.y() - half),
                QPoint(center.x() + half // 2, center.y()),
                QPoint(center.x() - half // 2, center.y() + half),
            ]
        painter.setBrush(painter.pen().color())
        painter.drawPolygon(QPolygon(points))


class SidebarSplitter(QSplitter):
    """Horizontal splitter for the sidebar with a custom collapse handle."""

    DEFAULT_SIDEBAR_WIDTH = 380
    MIN_SIDEBAR_WIDTH = 200
    HANDLE_WIDTH = 16

    arrowClicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._saved_sidebar_width = self.DEFAULT_SIDEBAR_WIDTH
        self._collapsed = False
        self.setHandleWidth(self.HANDLE_WIDTH)
        self.splitterMoved.connect(self._onSplitterMoved)

    def finalizeSetup(self) -> None:
        """Call after both panels are added to the splitter."""
        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)
        self.setChildrenCollapsible(False)
        self.setCollapsible(0, True)
        self.setCollapsible(1, False)
        self._applyExpandedConstraints()

    def createHandle(self) -> QSplitterHandle:
        handle = SidebarSplitterHandle(self.orientation(), self)
        handle.arrowClicked.connect(self.arrowClicked.emit)
        handle.setToolTip("Drag to resize sidebar, click to collapse (Ctrl+B)")
        return handle

    def isSidebarCollapsed(self) -> bool:
        return self._collapsed

    def setInitialSizes(self) -> None:
        total = max(self.width(), self.DEFAULT_SIDEBAR_WIDTH * 3)
        sidebar = min(self._saved_sidebar_width, total - self.handleWidth())
        self.setSizes([sidebar, total - sidebar])

    def collapseSidebar(self) -> None:
        sidebar = self.widget(0)
        if sidebar is None or self._collapsed:
            return

        sizes = self.sizes()
        if sizes and sizes[0] > 0:
            self._saved_sidebar_width = sizes[0]

        self._collapsed = True
        sidebar.setMinimumWidth(0)
        sidebar.setMaximumWidth(0)
        total = sum(sizes) if sizes else self.width()
        self.setSizes([0, total])
        self._refreshHandles()

    def expandSidebar(self) -> None:
        sidebar = self.widget(0)
        if sidebar is None or not self._collapsed:
            return

        self._collapsed = False
        self._applyExpandedConstraints()
        total = sum(self.sizes()) or self.width()
        sidebar_width = min(
            max(self._saved_sidebar_width, self.MIN_SIDEBAR_WIDTH),
            total - self.handleWidth(),
        )
        self.setSizes([sidebar_width, total - sidebar_width])
        self._refreshHandles()

    def toggleSidebar(self) -> None:
        if self._collapsed:
            self.expandSidebar()
        else:
            self.collapseSidebar()

    def _applyExpandedConstraints(self) -> None:
        sidebar = self.widget(0)
        if sidebar is None:
            return
        sidebar.setMinimumWidth(self.MIN_SIDEBAR_WIDTH)
        sidebar.setMaximumWidth(16777215)

    def _onSplitterMoved(self, _pos: int, _index: int) -> None:
        if self._collapsed:
            return
        sizes = self.sizes()
        if sizes and sizes[0] >= self.MIN_SIDEBAR_WIDTH:
            self._saved_sidebar_width = sizes[0]

    def _refreshHandles(self) -> None:
        handle = self.handle(1)
        if handle is not None:
            handle.update()
