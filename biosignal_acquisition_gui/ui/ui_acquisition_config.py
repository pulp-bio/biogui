# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'acquisition_config.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_AcquisitionConfig(object):
    def setupUi(self, AcquisitionConfig):
        if not AcquisitionConfig.objectName():
            AcquisitionConfig.setObjectName(u"AcquisitionConfig")
        AcquisitionConfig.resize(400, 200)
        self.verticalLayout = QVBoxLayout(AcquisitionConfig)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.acquisitionGroupBox = QGroupBox(AcquisitionConfig)
        self.acquisitionGroupBox.setObjectName(u"acquisitionGroupBox")
        self.acquisitionGroupBox.setAlignment(Qt.AlignCenter)
        self.acquisitionGroupBox.setCheckable(True)
        self.acquisitionGroupBox.setChecked(False)
        self.verticalLayout_3 = QVBoxLayout(self.acquisitionGroupBox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label1 = QLabel(self.acquisitionGroupBox)
        self.label1.setObjectName(u"label1")

        self.gridLayout.addWidget(self.label1, 0, 0, 1, 1)

        self.acquisitionTextField = QLineEdit(self.acquisitionGroupBox)
        self.acquisitionTextField.setObjectName(u"acquisitionTextField")

        self.gridLayout.addWidget(self.acquisitionTextField, 0, 1, 1, 1)

        self.label2 = QLabel(self.acquisitionGroupBox)
        self.label2.setObjectName(u"label2")

        self.gridLayout.addWidget(self.label2, 1, 0, 1, 1)

        self.browseJSONButton = QPushButton(self.acquisitionGroupBox)
        self.browseJSONButton.setObjectName(u"browseJSONButton")

        self.gridLayout.addWidget(self.browseJSONButton, 1, 1, 1, 1)

        self.gridLayout.setColumnStretch(0, 2)
        self.gridLayout.setColumnStretch(1, 1)

        self.verticalLayout_3.addLayout(self.gridLayout)

        self.JSONLabel = QLabel(self.acquisitionGroupBox)
        self.JSONLabel.setObjectName(u"JSONLabel")

        self.verticalLayout_3.addWidget(self.JSONLabel)


        self.verticalLayout.addWidget(self.acquisitionGroupBox)


        self.retranslateUi(AcquisitionConfig)

        QMetaObject.connectSlotsByName(AcquisitionConfig)
    # setupUi

    def retranslateUi(self, AcquisitionConfig):
        AcquisitionConfig.setWindowTitle(QCoreApplication.translate("AcquisitionConfig", u"Acquisition Widget", None))
        self.acquisitionGroupBox.setTitle(QCoreApplication.translate("AcquisitionConfig", u"Configure acquisition", None))
        self.label1.setText(QCoreApplication.translate("AcquisitionConfig", u"Output file name:", None))
#if QT_CONFIG(tooltip)
        self.acquisitionTextField.setToolTip(QCoreApplication.translate("AcquisitionConfig", u"If no name is provided, one based on the timestamp will be used", None))
#endif // QT_CONFIG(tooltip)
        self.label2.setText(QCoreApplication.translate("AcquisitionConfig", u"JSON with configuration:", None))
        self.browseJSONButton.setText(QCoreApplication.translate("AcquisitionConfig", u"Browse", None))
        self.JSONLabel.setText("")
    # retranslateUi

