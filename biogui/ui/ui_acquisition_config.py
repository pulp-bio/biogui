# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'acquisition_config.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QGroupBox, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_AcquisitionConfig(object):
    def setupUi(self, AcquisitionConfig):
        if not AcquisitionConfig.objectName():
            AcquisitionConfig.setObjectName(u"AcquisitionConfig")
        AcquisitionConfig.resize(400, 132)
        self.verticalLayout = QVBoxLayout(AcquisitionConfig)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.acquisitionGroupBox = QGroupBox(AcquisitionConfig)
        self.acquisitionGroupBox.setObjectName(u"acquisitionGroupBox")
        self.acquisitionGroupBox.setAlignment(Qt.AlignCenter)
        self.acquisitionGroupBox.setCheckable(True)
        self.acquisitionGroupBox.setChecked(False)
        self.formLayout = QFormLayout(self.acquisitionGroupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.label1 = QLabel(self.acquisitionGroupBox)
        self.label1.setObjectName(u"label1")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label1)

        self.browseJSONButton = QPushButton(self.acquisitionGroupBox)
        self.browseJSONButton.setObjectName(u"browseJSONButton")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.browseJSONButton)

        self.label2 = QLabel(self.acquisitionGroupBox)
        self.label2.setObjectName(u"label2")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label2)

        self.configJSONPathLabel = QLabel(self.acquisitionGroupBox)
        self.configJSONPathLabel.setObjectName(u"configJSONPathLabel")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.configJSONPathLabel)


        self.verticalLayout.addWidget(self.acquisitionGroupBox)


        self.retranslateUi(AcquisitionConfig)

        QMetaObject.connectSlotsByName(AcquisitionConfig)
    # setupUi

    def retranslateUi(self, AcquisitionConfig):
        AcquisitionConfig.setWindowTitle(QCoreApplication.translate("AcquisitionConfig", u"Acquisition Widget", None))
        self.acquisitionGroupBox.setTitle(QCoreApplication.translate("AcquisitionConfig", u"Configure acquisition", None))
        self.label1.setText(QCoreApplication.translate("AcquisitionConfig", u"JSON with configuration:", None))
        self.browseJSONButton.setText(QCoreApplication.translate("AcquisitionConfig", u"Browse", None))
        self.label2.setText(QCoreApplication.translate("AcquisitionConfig", u"Path to JSON:", None))
        self.configJSONPathLabel.setText("")
    # retranslateUi

