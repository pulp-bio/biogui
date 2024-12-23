# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fifo_data_source_config_widget.ui'
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

class Ui_FifoDataSourceConfigWidget(object):
    def setupUi(self, FifoDataSourceConfigWidget):
        if not FifoDataSourceConfigWidget.objectName():
            FifoDataSourceConfigWidget.setObjectName(u"FifoDataSourceConfigWidget")
        FifoDataSourceConfigWidget.resize(400, 300)
        self.formLayout = QFormLayout(FifoDataSourceConfigWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(FifoDataSourceConfigWidget)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.fifoPathTextField = QLineEdit(FifoDataSourceConfigWidget)
        self.fifoPathTextField.setObjectName(u"fifoPathTextField")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.fifoPathTextField)


        self.retranslateUi(FifoDataSourceConfigWidget)

        QMetaObject.connectSlotsByName(FifoDataSourceConfigWidget)
    # setupUi

    def retranslateUi(self, FifoDataSourceConfigWidget):
        FifoDataSourceConfigWidget.setWindowTitle(QCoreApplication.translate("FifoDataSourceConfigWidget", u"FIFO Configuration Widget", None))
        self.label.setText(QCoreApplication.translate("FifoDataSourceConfigWidget", u"Path to FIFO:", None))
    # retranslateUi

