# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fifo_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
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


class Ui_FIFOConfigWidget(object):
    def setupUi(self, FIFOConfigWidget):
        if not FIFOConfigWidget.objectName():
            FIFOConfigWidget.setObjectName("FIFOConfigWidget")
        FIFOConfigWidget.resize(400, 300)
        self.formLayout = QFormLayout(FIFOConfigWidget)
        self.formLayout.setObjectName("formLayout")
        self.label = QLabel(FIFOConfigWidget)
        self.label.setObjectName("label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.fifoPathTextField = QLineEdit(FIFOConfigWidget)
        self.fifoPathTextField.setObjectName("fifoPathTextField")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.fifoPathTextField)

        self.retranslateUi(FIFOConfigWidget)

        QMetaObject.connectSlotsByName(FIFOConfigWidget)

    # setupUi

    def retranslateUi(self, FIFOConfigWidget):
        FIFOConfigWidget.setWindowTitle(
            QCoreApplication.translate(
                "FIFOConfigWidget", "FIFO Configuration Widget", None
            )
        )
        self.label.setText(
            QCoreApplication.translate("FIFOConfigWidget", "Path to FIFO:", None)
        )

    # retranslateUi
