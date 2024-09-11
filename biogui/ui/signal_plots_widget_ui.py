# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'signal_plots_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
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

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label1 = QLabel(SignalPlotsWidget)
        self.label1.setObjectName(u"label1")
        self.label1.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.label1)

        self.spsLabel = QLabel(SignalPlotsWidget)
        self.spsLabel.setObjectName(u"spsLabel")

        self.horizontalLayout.addWidget(self.spsLabel)

        self.label2 = QLabel(SignalPlotsWidget)
        self.label2.setObjectName(u"label2")
        self.label2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.label2)

        self.timeLabel = QLabel(SignalPlotsWidget)
        self.timeLabel.setObjectName(u"timeLabel")

        self.horizontalLayout.addWidget(self.timeLabel)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(SignalPlotsWidget)

        QMetaObject.connectSlotsByName(SignalPlotsWidget)
    # setupUi

    def retranslateUi(self, SignalPlotsWidget):
        SignalPlotsWidget.setWindowTitle(QCoreApplication.translate("SignalPlotsWidget", u"Form", None))
        self.label1.setText(QCoreApplication.translate("SignalPlotsWidget", u"Sampling rate:", None))
        self.spsLabel.setText(QCoreApplication.translate("SignalPlotsWidget", u"0 sps", None))
        self.label2.setText(QCoreApplication.translate("SignalPlotsWidget", u"Time:", None))
        self.timeLabel.setText(QCoreApplication.translate("SignalPlotsWidget", u"0.00 s", None))
    # retranslateUi

