# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'signal_plots_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

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
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsView,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Ui_SignalPlotsWidget(object):
    def setupUi(self, SignalPlotsWidget):
        if not SignalPlotsWidget.objectName():
            SignalPlotsWidget.setObjectName("SignalPlotsWidget")
        SignalPlotsWidget.resize(400, 300)
        self.verticalLayout = QVBoxLayout(SignalPlotsWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.sigNameLabel = QLabel(SignalPlotsWidget)
        self.sigNameLabel.setObjectName("sigNameLabel")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.sigNameLabel.setFont(font)
        self.sigNameLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.sigNameLabel)

        self.view = QGraphicsView(SignalPlotsWidget)
        self.view.setObjectName("view")

        self.verticalLayout.addWidget(self.view)

        self.retranslateUi(SignalPlotsWidget)

        QMetaObject.connectSlotsByName(SignalPlotsWidget)

    # setupUi

    def retranslateUi(self, SignalPlotsWidget):
        SignalPlotsWidget.setWindowTitle(
            QCoreApplication.translate("SignalPlotsWidget", "Form", None)
        )
        self.sigNameLabel.setText("")

    # retranslateUi
