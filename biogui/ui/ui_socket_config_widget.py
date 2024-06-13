# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'socket_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    QTime,
    QUrl,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QWidget,
)


class Ui_SocketConfigWidget(object):
    def setupUi(self, SocketConfigWidget):
        if not SocketConfigWidget.objectName():
            SocketConfigWidget.setObjectName("SocketConfigWidget")
        SocketConfigWidget.resize(400, 300)
        self.formLayout = QFormLayout(SocketConfigWidget)
        self.formLayout.setObjectName("formLayout")
        self.label3 = QLabel(SocketConfigWidget)
        self.label3.setObjectName("label3")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label3)

        self.portTextField = QLineEdit(SocketConfigWidget)
        self.portTextField.setObjectName("portTextField")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.portTextField)

        self.retranslateUi(SocketConfigWidget)

        QMetaObject.connectSlotsByName(SocketConfigWidget)

    # setupUi

    def retranslateUi(self, SocketConfigWidget):
        SocketConfigWidget.setWindowTitle(
            QCoreApplication.translate(
                "SocketConfigWidget", "Socket Configuration Widget", None
            )
        )
        self.label3.setText(
            QCoreApplication.translate("SocketConfigWidget", "Port:", None)
        )

    # retranslateUi
