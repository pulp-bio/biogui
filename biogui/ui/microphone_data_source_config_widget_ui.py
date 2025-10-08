# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'microphone_data_source_config_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QLabel,
    QLineEdit, QSizePolicy, QWidget)

class Ui_MicrophoneDataSourceConfigWidget(object):
    def setupUi(self, MicrophoneDataSourceConfigWidget):
        if not MicrophoneDataSourceConfigWidget.objectName():
            MicrophoneDataSourceConfigWidget.setObjectName(u"MicrophoneDataSourceConfigWidget")
        MicrophoneDataSourceConfigWidget.resize(361, 52)
        self.widget = QWidget(MicrophoneDataSourceConfigWidget)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(0, 0, 361, 50))
        self.formLayout = QFormLayout(self.widget)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.audioDeviceComboBox = QComboBox(self.widget)
        self.audioDeviceComboBox.setObjectName(u"audioDeviceComboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.audioDeviceComboBox)

        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label)

        self.sampleRateTextField = QLineEdit(self.widget)
        self.sampleRateTextField.setObjectName(u"sampleRateTextField")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.sampleRateTextField)


        self.retranslateUi(MicrophoneDataSourceConfigWidget)

        QMetaObject.connectSlotsByName(MicrophoneDataSourceConfigWidget)
    # setupUi

    def retranslateUi(self, MicrophoneDataSourceConfigWidget):
        MicrophoneDataSourceConfigWidget.setWindowTitle(QCoreApplication.translate("MicrophoneDataSourceConfigWidget", u"Form", None))
        self.label_3.setText(QCoreApplication.translate("MicrophoneDataSourceConfigWidget", u"Input device:", None))
        self.label.setText(QCoreApplication.translate("MicrophoneDataSourceConfigWidget", u"Sampling frequency:", None))
        self.sampleRateTextField.setText("")
    # retranslateUi

