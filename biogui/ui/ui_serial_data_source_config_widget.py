# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'serial_data_source_config_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QWidget)
import biogui_rc

class Ui_SerialDataSourceConfigWidget(object):
    def setupUi(self, SerialDataSourceConfigWidget):
        if not SerialDataSourceConfigWidget.objectName():
            SerialDataSourceConfigWidget.setObjectName(u"SerialDataSourceConfigWidget")
        SerialDataSourceConfigWidget.resize(400, 57)
        self.formLayout = QFormLayout(SerialDataSourceConfigWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.label1 = QLabel(SerialDataSourceConfigWidget)
        self.label1.setObjectName(u"label1")
        self.label1.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.serialPortsComboBox = QComboBox(SerialDataSourceConfigWidget)
        self.serialPortsComboBox.setObjectName(u"serialPortsComboBox")

        self.horizontalLayout.addWidget(self.serialPortsComboBox)

        self.rescanSerialPortsButton = QPushButton(SerialDataSourceConfigWidget)
        self.rescanSerialPortsButton.setObjectName(u"rescanSerialPortsButton")
        icon = QIcon(QIcon.fromTheme(u"view-refresh"))
        self.rescanSerialPortsButton.setIcon(icon)

        self.horizontalLayout.addWidget(self.rescanSerialPortsButton)

        self.horizontalLayout.setStretch(0, 4)
        self.horizontalLayout.setStretch(1, 1)

        self.formLayout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.horizontalLayout)

        QWidget.setTabOrder(self.serialPortsComboBox, self.rescanSerialPortsButton)

        self.retranslateUi(SerialDataSourceConfigWidget)

        QMetaObject.connectSlotsByName(SerialDataSourceConfigWidget)
    # setupUi

    def retranslateUi(self, SerialDataSourceConfigWidget):
        SerialDataSourceConfigWidget.setWindowTitle(QCoreApplication.translate("SerialDataSourceConfigWidget", u"Serial Data Source Configuration", None))
        self.label1.setText(QCoreApplication.translate("SerialDataSourceConfigWidget", u"Serial port:", None))
#if QT_CONFIG(tooltip)
        self.serialPortsComboBox.setToolTip(QCoreApplication.translate("SerialDataSourceConfigWidget", u"List of available serial ports", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.rescanSerialPortsButton.setToolTip(QCoreApplication.translate("SerialDataSourceConfigWidget", u"Rescan serial ports", None))
#endif // QT_CONFIG(tooltip)
        self.rescanSerialPortsButton.setText("")
    # retranslateUi

