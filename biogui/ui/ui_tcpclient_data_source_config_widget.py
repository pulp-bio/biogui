# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tcp_data_source_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QLabel, QLineEdit,
    QSizePolicy, QWidget)

class Ui_TCPClientDataSourceConfigWidget(object):
    def setupUi(self, TCPClientDataSourceConfigWidget):
        if not TCPClientDataSourceConfigWidget.objectName():
            TCPClientDataSourceConfigWidget.setObjectName(u"TCPClientDataSourceConfigWidget")
        TCPClientDataSourceConfigWidget.resize(400, 44)
        self.formLayout = QFormLayout(TCPClientDataSourceConfigWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(TCPClientDataSourceConfigWidget)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.socketPortTextField = QLineEdit(TCPClientDataSourceConfigWidget)
        self.socketPortTextField.setObjectName(u"socketPortTextField")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.socketPortTextField)


        self.retranslateUi(TCPClientDataSourceConfigWidget)

        QMetaObject.connectSlotsByName(TCPClientDataSourceConfigWidget)
    # setupUi

    def retranslateUi(self, TCPClientDataSourceConfigWidget):
        TCPClientDataSourceConfigWidget.setWindowTitle(QCoreApplication.translate("TCPClientDataSourceConfigWidget", u"TCP Client Data Source Configuration", None))
        self.label.setText(QCoreApplication.translate("TCPClientDataSourceConfigWidget", u"Socket port:", None))
    # retranslateUi

