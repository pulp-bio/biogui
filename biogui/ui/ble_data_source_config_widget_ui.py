# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ble_data_source_config_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QLineEdit, QPushButton,
    QSizePolicy, QWidget)

class Ui_BLEDataSourceConfigWidget(object):
    def setupUi(self, BLEDataSourceConfigWidget):
        if not BLEDataSourceConfigWidget.objectName():
            BLEDataSourceConfigWidget.setObjectName(u"BLEDataSourceConfigWidget")
        BLEDataSourceConfigWidget.resize(400, 300)
        self.deviceComboBox = QComboBox(BLEDataSourceConfigWidget)
        self.deviceComboBox.setObjectName(u"deviceComboBox")
        self.deviceComboBox.setGeometry(QRect(60, 40, 82, 28))
        self.scanButton = QPushButton(BLEDataSourceConfigWidget)
        self.scanButton.setObjectName(u"scanButton")
        self.scanButton.setGeometry(QRect(190, 40, 83, 29))
        self.serviceComboBox = QComboBox(BLEDataSourceConfigWidget)
        self.serviceComboBox.setObjectName(u"serviceComboBox")
        self.serviceComboBox.setGeometry(QRect(60, 90, 82, 28))
        self.charComboBox = QComboBox(BLEDataSourceConfigWidget)
        self.charComboBox.setObjectName(u"charComboBox")
        self.charComboBox.setGeometry(QRect(60, 120, 82, 28))
        self.connectButton = QPushButton(BLEDataSourceConfigWidget)
        self.connectButton.setObjectName(u"connectButton")
        self.connectButton.setGeometry(QRect(230, 250, 83, 29))
        self.serviceUuidLineEdit = QLineEdit(BLEDataSourceConfigWidget)
        self.serviceUuidLineEdit.setObjectName(u"serviceUuidLineEdit")
        self.serviceUuidLineEdit.setGeometry(QRect(50, 170, 113, 28))
        self.charUuidLineEdit = QLineEdit(BLEDataSourceConfigWidget)
        self.charUuidLineEdit.setObjectName(u"charUuidLineEdit")
        self.charUuidLineEdit.setGeometry(QRect(50, 210, 113, 28))

        self.retranslateUi(BLEDataSourceConfigWidget)

        QMetaObject.connectSlotsByName(BLEDataSourceConfigWidget)
    # setupUi

    def retranslateUi(self, BLEDataSourceConfigWidget):
        BLEDataSourceConfigWidget.setWindowTitle(QCoreApplication.translate("BLEDataSourceConfigWidget", u"Form", None))
        self.scanButton.setText(QCoreApplication.translate("BLEDataSourceConfigWidget", u"Scan", None))
        self.connectButton.setText(QCoreApplication.translate("BLEDataSourceConfigWidget", u"Connect", None))
    # retranslateUi

