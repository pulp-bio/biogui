# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'local_socket_data_source_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
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

class Ui_LocalSocketDataSourceConfigWidget(object):
    def setupUi(self, LocalSocketDataSourceConfigWidget):
        if not LocalSocketDataSourceConfigWidget.objectName():
            LocalSocketDataSourceConfigWidget.setObjectName(u"LocalSocketDataSourceConfigWidget")
        LocalSocketDataSourceConfigWidget.resize(400, 44)
        self.formLayout = QFormLayout(LocalSocketDataSourceConfigWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(LocalSocketDataSourceConfigWidget)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.label.setWordWrap(False)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.socketPathTextField = QLineEdit(LocalSocketDataSourceConfigWidget)
        self.socketPathTextField.setObjectName(u"socketPathTextField")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.socketPathTextField)


        self.retranslateUi(LocalSocketDataSourceConfigWidget)

        QMetaObject.connectSlotsByName(LocalSocketDataSourceConfigWidget)
    # setupUi

    def retranslateUi(self, LocalSocketDataSourceConfigWidget):
        LocalSocketDataSourceConfigWidget.setWindowTitle(QCoreApplication.translate("LocalSocketDataSourceConfigWidget", u"Local Socket Data Source Configuration", None))
        self.label.setText(QCoreApplication.translate("LocalSocketDataSourceConfigWidget", u"Socket path:", None))
    # retranslateUi

