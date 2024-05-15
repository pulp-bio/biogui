# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'signal_plots_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QSizePolicy, QVBoxLayout, QWidget)

from pyqtgraph import PlotWidget

class Ui_SignalPlotsWidget(object):
    def setupUi(self, SignalPlotsWidget):
        if not SignalPlotsWidget.objectName():
            SignalPlotsWidget.setObjectName(u"SignalPlotsWidget")
        SignalPlotsWidget.resize(400, 300)
        self.verticalLayout = QVBoxLayout(SignalPlotsWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.graphWidget = PlotWidget(SignalPlotsWidget)
        self.graphWidget.setObjectName(u"graphWidget")

        self.verticalLayout.addWidget(self.graphWidget)


        self.retranslateUi(SignalPlotsWidget)

        QMetaObject.connectSlotsByName(SignalPlotsWidget)
    # setupUi

    def retranslateUi(self, SignalPlotsWidget):
        SignalPlotsWidget.setWindowTitle(QCoreApplication.translate("SignalPlotsWidget", u"Form", None))
    # retranslateUi

