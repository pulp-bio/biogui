# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tcp_config_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QLabel, QLineEdit,
    QSizePolicy, QWidget)

class Ui_TCPConfigWidget(object):
    def setupUi(self, TCPConfigWidget):
        if not TCPConfigWidget.objectName():
            TCPConfigWidget.setObjectName(u"TCPConfigWidget")
        TCPConfigWidget.resize(400, 300)
        self.formLayout = QFormLayout(TCPConfigWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(TCPConfigWidget)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.portTextField = QLineEdit(TCPConfigWidget)
        self.portTextField.setObjectName(u"portTextField")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.portTextField)


        self.retranslateUi(TCPConfigWidget)

        QMetaObject.connectSlotsByName(TCPConfigWidget)
    # setupUi

    def retranslateUi(self, TCPConfigWidget):
        TCPConfigWidget.setWindowTitle(QCoreApplication.translate("TCPConfigWidget", u"TCP Configuration Widget", None))
        self.label.setText(QCoreApplication.translate("TCPConfigWidget", u"Port:", None))
    # retranslateUi

