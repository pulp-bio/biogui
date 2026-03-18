# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'unix_socket_data_source_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 5.15.18
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_UnixSocketDataSourceConfigWidget(object):
    def setupUi(self, UnixSocketDataSourceConfigWidget):
        if not UnixSocketDataSourceConfigWidget.objectName():
            UnixSocketDataSourceConfigWidget.setObjectName(u"UnixSocketDataSourceConfigWidget")
        UnixSocketDataSourceConfigWidget.resize(400, 44)
        self.formLayout = QFormLayout(UnixSocketDataSourceConfigWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(UnixSocketDataSourceConfigWidget)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.label.setWordWrap(False)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.socketPathTextField = QLineEdit(UnixSocketDataSourceConfigWidget)
        self.socketPathTextField.setObjectName(u"socketPathTextField")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.socketPathTextField)


        self.retranslateUi(UnixSocketDataSourceConfigWidget)

        QMetaObject.connectSlotsByName(UnixSocketDataSourceConfigWidget)
    # setupUi

    def retranslateUi(self, UnixSocketDataSourceConfigWidget):
        UnixSocketDataSourceConfigWidget.setWindowTitle(QCoreApplication.translate("UnixSocketDataSourceConfigWidget", u"Local Socket Data Source Configuration", None))
        self.label.setText(QCoreApplication.translate("UnixSocketDataSourceConfigWidget", u"Socket path:", None))
    # retranslateUi
