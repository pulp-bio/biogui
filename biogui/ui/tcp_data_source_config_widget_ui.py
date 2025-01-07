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

class Ui_TCPDataSourceConfigWidget(object):
    def setupUi(self, TCPDataSourceConfigWidget):
        if not TCPDataSourceConfigWidget.objectName():
            TCPDataSourceConfigWidget.setObjectName(u"TCPDataSourceConfigWidget")
        TCPDataSourceConfigWidget.resize(400, 300)
        self.formLayout = QFormLayout(TCPDataSourceConfigWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(TCPDataSourceConfigWidget)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.portTextField = QLineEdit(TCPDataSourceConfigWidget)
        self.portTextField.setObjectName(u"portTextField")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.portTextField)


        self.retranslateUi(TCPDataSourceConfigWidget)

        QMetaObject.connectSlotsByName(TCPDataSourceConfigWidget)
    # setupUi

    def retranslateUi(self, TCPDataSourceConfigWidget):
        TCPDataSourceConfigWidget.setWindowTitle(QCoreApplication.translate("TCPDataSourceConfigWidget", u"TCP Data Source Configuration", None))
        self.label.setText(QCoreApplication.translate("TCPDataSourceConfigWidget", u"Port:", None))
    # retranslateUi

