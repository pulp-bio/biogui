# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fifo_config_widget.ui'
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

class Ui_FifoConfigView(object):
    def setupUi(self, FifoConfigView):
        if not FifoConfigView.objectName():
            FifoConfigView.setObjectName(u"FifoConfigView")
        FifoConfigView.resize(400, 300)
        self.formLayout = QFormLayout(FifoConfigView)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(FifoConfigView)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.fifoPathTextField = QLineEdit(FifoConfigView)
        self.fifoPathTextField.setObjectName(u"fifoPathTextField")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.fifoPathTextField)


        self.retranslateUi(FifoConfigView)

        QMetaObject.connectSlotsByName(FifoConfigView)
    # setupUi

    def retranslateUi(self, FifoConfigView):
        FifoConfigView.setWindowTitle(QCoreApplication.translate("FifoConfigView", u"FIFO Configuration Widget", None))
        self.label.setText(QCoreApplication.translate("FifoConfigView", u"Path to FIFO:", None))
    # retranslateUi

