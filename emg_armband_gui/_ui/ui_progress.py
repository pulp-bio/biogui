# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'progress.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
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
from PySide6.QtWidgets import QApplication, QLabel, QSizePolicy, QVBoxLayout, QWidget


class Ui_ProgressWidget(object):
    def setupUi(self, ProgressWidget):
        if not ProgressWidget.objectName():
            ProgressWidget.setObjectName("ProgressWidget")
        ProgressWidget.resize(400, 300)
        self.verticalLayout = QVBoxLayout(ProgressWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.progressLabel = QLabel(ProgressWidget)
        self.progressLabel.setObjectName("progressLabel")
        self.progressLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.progressLabel)

        self.retranslateUi(ProgressWidget)

        QMetaObject.connectSlotsByName(ProgressWidget)

    # setupUi

    def retranslateUi(self, ProgressWidget):
        ProgressWidget.setWindowTitle(
            QCoreApplication.translate("ProgressWidget", "Progress Widget", None)
        )
        self.progressLabel.setText("")

    # retranslateUi
