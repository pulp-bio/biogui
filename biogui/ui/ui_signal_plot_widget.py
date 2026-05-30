# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'signal_plot_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QSizePolicy,
    QVBoxLayout, QWidget)

from pyqtgraph import PlotWidget

class Ui_SignalPlotWidget(object):
    def setupUi(self, SignalPlotWidget):
        if not SignalPlotWidget.objectName():
            SignalPlotWidget.setObjectName(u"SignalPlotWidget")
        SignalPlotWidget.resize(400, 300)
        self.verticalLayout = QVBoxLayout(SignalPlotWidget)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(4, 4, 4, 4)
        self.graphWidget = PlotWidget(SignalPlotWidget)
        self.graphWidget.setObjectName(u"graphWidget")

        self.verticalLayout.addWidget(self.graphWidget)

        self.statsBar = QWidget(SignalPlotWidget)
        self.statsBar.setObjectName(u"statsBar")
        self.horizontalLayout = QHBoxLayout(self.statsBar)
        self.horizontalLayout.setSpacing(8)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label1 = QLabel(self.statsBar)
        self.label1.setObjectName(u"label1")
        self.label1.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.label1)

        self.spsLabel = QLabel(self.statsBar)
        self.spsLabel.setObjectName(u"spsLabel")

        self.horizontalLayout.addWidget(self.spsLabel)

        self.label2 = QLabel(self.statsBar)
        self.label2.setObjectName(u"label2")
        self.label2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.label2)

        self.timeLabel = QLabel(self.statsBar)
        self.timeLabel.setObjectName(u"timeLabel")

        self.horizontalLayout.addWidget(self.timeLabel)


        self.verticalLayout.addWidget(self.statsBar)


        self.retranslateUi(SignalPlotWidget)

        QMetaObject.connectSlotsByName(SignalPlotWidget)
    # setupUi

    def retranslateUi(self, SignalPlotWidget):
        SignalPlotWidget.setWindowTitle(QCoreApplication.translate("SignalPlotWidget", u"Signal Plot Widget", None))
        self.label1.setText(QCoreApplication.translate("SignalPlotWidget", u"Sampling rate:", None))
        self.spsLabel.setText(QCoreApplication.translate("SignalPlotWidget", u"0 sps", None))
        self.label2.setText(QCoreApplication.translate("SignalPlotWidget", u"Time:", None))
        self.timeLabel.setText(QCoreApplication.translate("SignalPlotWidget", u"0.00 s", None))
    # retranslateUi

