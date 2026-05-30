# Copyright University of Bologna - ETH Zurich 2026
# Licensed under Apache v2.0 see LICENSE for details.
#
# SPDX-License-Identifier: Apache-2.0

"""
View for the main window.
"""

from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMainWindow, QWidget

from biogui.ui.ui_main_window import Ui_MainWindow
from biogui.utils import detectTheme

from .plot_layout_manager import PlotLayoutManager
from .sidebar_splitter import SidebarSplitter


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main window.

    Attributes
    ----------
    renderLenMs : int
        Length of the window in the plot (in ms).

    Class attributes
    ----------------
    renderLenChanged : Signal
        Qt Signal emitted when the render length changes.
    """

    renderLenChanged = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        # Setup UI
        self.setupUi(self)
        theme = detectTheme()
        self.deleteDataSourceButton.setIcon(
            QIcon.fromTheme("user-trash", QIcon(f":icons/{theme}/trash"))
        )
        self.editButton.setIcon(QIcon.fromTheme("edit-entry", QIcon(f":icons/{theme}/edit")))

        # Set default render length to 5 s
        self.renderLenComboBox.setCurrentText("5 s")
        self.renderLenMs = 5000
        self.renderLenComboBox.currentTextChanged.connect(self._onRenderLenChange)

        self._plotLayoutManager = PlotLayoutManager(self.plotsContainer)
        self._plotStatsVisible = True
        self._setupSidebarSplitter()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not getattr(self, "_sidebar_sizes_initialized", False):
            self._sidebarSplitter.setInitialSizes()
            self._sidebar_sizes_initialized = True

    def setupViewMenu(self) -> None:
        """Add View menu with plot layout options (call after other menus are created)."""
        viewMenu = self.menuBar().addMenu("View")
        self.actionTwoColumnPlots = QAction("Two-column layout", self)
        self.actionTwoColumnPlots.setCheckable(True)
        self.actionTwoColumnPlots.triggered.connect(self._onTwoColumnPlotsToggled)
        viewMenu.addAction(self.actionTwoColumnPlots)

        self.actionShowPlotStats = QAction("Show plot stats", self)
        self.actionShowPlotStats.setCheckable(True)
        self.actionShowPlotStats.setChecked(True)
        self.actionShowPlotStats.triggered.connect(self._onShowPlotStatsToggled)
        viewMenu.addAction(self.actionShowPlotStats)

    @Slot(bool)
    def _onShowPlotStatsToggled(self, visible: bool) -> None:
        self._plotStatsVisible = visible
        self._plotLayoutManager.setStatsVisible(visible)

    @Slot(bool)
    def _onTwoColumnPlotsToggled(self, enabled: bool) -> None:
        self._plotLayoutManager.setTwoColumn(enabled)

    def addPlotWidget(self, widget: QWidget) -> None:
        self._plotLayoutManager.addWidget(widget)
        if hasattr(widget, "setStatsVisible"):
            widget.setStatsVisible(self._plotStatsVisible)

    def removePlotWidget(self, widget: QWidget) -> None:
        self._plotLayoutManager.removeWidget(widget)

    def replacePlotWidget(self, oldWidget: QWidget, newWidget: QWidget) -> None:
        self._plotLayoutManager.replaceWidget(oldWidget, newWidget)
        if hasattr(newWidget, "setStatsVisible"):
            newWidget.setStatsVisible(self._plotStatsVisible)

    def _setupSidebarSplitter(self) -> None:
        """Replace sidebar/plots row with a draggable splitter."""
        layout = self.horizontalLayout1
        layout.removeWidget(self.sidebarPanel)
        layout.removeWidget(self.plotsContainer)

        self.sidebarPanel.setMinimumWidth(SidebarSplitter.MIN_SIDEBAR_WIDTH)
        self._sidebarSplitter = SidebarSplitter(self.centralWidget)
        self._sidebarSplitter.addWidget(self.sidebarPanel)
        self._sidebarSplitter.addWidget(self.plotsContainer)
        self._sidebarSplitter.finalizeSetup()
        layout.addWidget(self._sidebarSplitter)

        self.addAction(self.actionToggleSidebar)
        self.actionToggleSidebar.triggered.connect(self.toggleSidebar)
        self._sidebarSplitter.arrowClicked.connect(self.toggleSidebar)

    @Slot()
    def toggleSidebar(self) -> None:
        """Collapse or expand the left configuration panel."""
        self._sidebarSplitter.toggleSidebar()

    @Slot(str)
    def _onRenderLenChange(self, renderLen: str):
        """Detect if render length has changed."""
        renderLenMap = {
            "100 ms": 100,
            "200 ms": 200,
            "500 ms": 500,
            "1 s": 1000,
            "2 s": 2000,
            "5 s": 5000,
            "10 s": 10000,
        }

        self.renderLenMs = renderLenMap[renderLen]
        self.renderLenChanged.emit(renderLenMap[renderLen])
