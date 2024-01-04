# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'serial_conf_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QWidget)

class Ui_SerialConfWidget(object):
    def setupUi(self, SerialConfWidget):
        if not SerialConfWidget.objectName():
            SerialConfWidget.setObjectName(u"SerialConfWidget")
        SerialConfWidget.resize(400, 300)
        self.horizontalLayout = QHBoxLayout(SerialConfWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(SerialConfWidget)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.serialPortsComboBox = QComboBox(SerialConfWidget)
        self.serialPortsComboBox.setObjectName(u"serialPortsComboBox")

        self.horizontalLayout.addWidget(self.serialPortsComboBox)

        self.rescanSerialPortsButton = QPushButton(SerialConfWidget)
        self.rescanSerialPortsButton.setObjectName(u"rescanSerialPortsButton")

        self.horizontalLayout.addWidget(self.rescanSerialPortsButton)

        self.horizontalLayout.setStretch(0, 3)
        self.horizontalLayout.setStretch(1, 2)
        self.horizontalLayout.setStretch(2, 1)

        self.retranslateUi(SerialConfWidget)

        QMetaObject.connectSlotsByName(SerialConfWidget)
    # setupUi

    def retranslateUi(self, SerialConfWidget):
        SerialConfWidget.setWindowTitle(QCoreApplication.translate("SerialConfWidget", u"Serial Configuration Widget", None))
        self.label.setText(QCoreApplication.translate("SerialConfWidget", u"Serial port:", None))
        self.rescanSerialPortsButton.setText(QCoreApplication.translate("SerialConfWidget", u"Rescan", None))
    # retranslateUi

