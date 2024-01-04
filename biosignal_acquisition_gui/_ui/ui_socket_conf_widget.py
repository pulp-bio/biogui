# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'socket_conf_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QLabel,
    QLineEdit, QSizePolicy, QWidget)

class Ui_SocketConfWidget(object):
    def setupUi(self, SocketConfWidget):
        if not SocketConfWidget.objectName():
            SocketConfWidget.setObjectName(u"SocketConfWidget")
        SocketConfWidget.resize(400, 300)
        self.formLayout = QFormLayout(SocketConfWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.label1 = QLabel(SocketConfWidget)
        self.label1.setObjectName(u"label1")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.serialPortsComboBox = QComboBox(SocketConfWidget)
        self.serialPortsComboBox.addItem("")
        self.serialPortsComboBox.addItem("")
        self.serialPortsComboBox.setObjectName(u"serialPortsComboBox")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.serialPortsComboBox)

        self.label3 = QLabel(SocketConfWidget)
        self.label3.setObjectName(u"label3")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label3)

        self.portTextField = QLineEdit(SocketConfWidget)
        self.portTextField.setObjectName(u"portTextField")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.portTextField)


        self.retranslateUi(SocketConfWidget)

        QMetaObject.connectSlotsByName(SocketConfWidget)
    # setupUi

    def retranslateUi(self, SocketConfWidget):
        SocketConfWidget.setWindowTitle(QCoreApplication.translate("SocketConfWidget", u"Socket Configuration Widget", None))
        self.label1.setText(QCoreApplication.translate("SocketConfWidget", u"Protocol:", None))
        self.serialPortsComboBox.setItemText(0, QCoreApplication.translate("SocketConfWidget", u"TCP", None))
        self.serialPortsComboBox.setItemText(1, QCoreApplication.translate("SocketConfWidget", u"UDP", None))

        self.label3.setText(QCoreApplication.translate("SocketConfWidget", u"Port:", None))
    # retranslateUi

