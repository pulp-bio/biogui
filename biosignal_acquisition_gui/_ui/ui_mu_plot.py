# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mu_plot.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from pyqtgraph import PlotWidget
from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    QTime,
    QUrl,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import QApplication, QSizePolicy, QVBoxLayout, QWidget


class Ui_MUPlot(object):
    def setupUi(self, MUPlot):
        if not MUPlot.objectName():
            MUPlot.setObjectName("MUPlot")
        MUPlot.resize(1080, 720)
        self.verticalLayout = QVBoxLayout(MUPlot)
        self.verticalLayout.setObjectName("verticalLayout")
        self.graphWidget = PlotWidget(MUPlot)
        self.graphWidget.setObjectName("graphWidget")

        self.verticalLayout.addWidget(self.graphWidget)

        self.retranslateUi(MUPlot)

        QMetaObject.connectSlotsByName(MUPlot)

    # setupUi

    def retranslateUi(self, MUPlot):
        MUPlot.setWindowTitle(
            QCoreApplication.translate("MUPlot", "MU Plot Widget", None)
        )

    # retranslateUi
