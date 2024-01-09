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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QWidget)

class Ui_SerialConfWidget(object):
    def setupUi(self, SerialConfWidget):
        if not SerialConfWidget.objectName():
            SerialConfWidget.setObjectName(u"SerialConfWidget")
        SerialConfWidget.resize(400, 300)
        self.formLayout = QFormLayout(SerialConfWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.label1 = QLabel(SerialConfWidget)
        self.label1.setObjectName(u"label1")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.serialPortsComboBox = QComboBox(SerialConfWidget)
        self.serialPortsComboBox.setObjectName(u"serialPortsComboBox")

        self.horizontalLayout.addWidget(self.serialPortsComboBox)

        self.rescanSerialPortsButton = QPushButton(SerialConfWidget)
        self.rescanSerialPortsButton.setObjectName(u"rescanSerialPortsButton")
        icon = QIcon()
        iconThemeName = u"view-refresh"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.rescanSerialPortsButton.setIcon(icon)

        self.horizontalLayout.addWidget(self.rescanSerialPortsButton)

        self.horizontalLayout.setStretch(0, 4)
        self.horizontalLayout.setStretch(1, 1)

        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout)

        self.label2 = QLabel(SerialConfWidget)
        self.label2.setObjectName(u"label2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.baudRateTextField = QLineEdit(SerialConfWidget)
        self.baudRateTextField.setObjectName(u"baudRateTextField")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.baudRateTextField)


        self.retranslateUi(SerialConfWidget)

        QMetaObject.connectSlotsByName(SerialConfWidget)
    # setupUi

    def retranslateUi(self, SerialConfWidget):
        SerialConfWidget.setWindowTitle(QCoreApplication.translate("SerialConfWidget", u"Serial Configuration Widget", None))
        self.label1.setText(QCoreApplication.translate("SerialConfWidget", u"Serial port:", None))
#if QT_CONFIG(tooltip)
        self.rescanSerialPortsButton.setToolTip(QCoreApplication.translate("SerialConfWidget", u"Rescan serial ports", None))
#endif // QT_CONFIG(tooltip)
        self.rescanSerialPortsButton.setText("")
        self.label2.setText(QCoreApplication.translate("SerialConfWidget", u"Baud rate:", None))
    # retranslateUi

