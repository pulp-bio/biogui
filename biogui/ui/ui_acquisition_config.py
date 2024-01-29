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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_AcquisitionConfig(object):
    def setupUi(self, AcquisitionConfig):
        if not AcquisitionConfig.objectName():
            AcquisitionConfig.setObjectName(u"AcquisitionConfig")
        AcquisitionConfig.resize(400, 202)
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

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.label2 = QLabel(self.acquisitionGroupBox)
        self.label2.setObjectName(u"label2")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label2)

        self.acquisitionTextField = QLineEdit(self.acquisitionGroupBox)
        self.acquisitionTextField.setObjectName(u"acquisitionTextField")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.acquisitionTextField)

        self.label3 = QLabel(self.acquisitionGroupBox)
        self.label3.setObjectName(u"label3")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label3)

        self.browseJSONButton = QPushButton(self.acquisitionGroupBox)
        self.browseJSONButton.setObjectName(u"browseJSONButton")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.browseJSONButton)

        self.label4 = QLabel(self.acquisitionGroupBox)
        self.label4.setObjectName(u"label4")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label4)

        self.configJSONPathLabel = QLabel(self.acquisitionGroupBox)
        self.configJSONPathLabel.setObjectName(u"configJSONPathLabel")

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.configJSONPathLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.signalComboBox = QComboBox(self.acquisitionGroupBox)
        self.signalComboBox.setObjectName(u"signalComboBox")

        self.horizontalLayout.addWidget(self.signalComboBox)

        self.rescanSignalsButton = QPushButton(self.acquisitionGroupBox)
        self.rescanSignalsButton.setObjectName(u"rescanSignalsButton")
        icon = QIcon(QIcon.fromTheme(u"view-refresh"))
        self.rescanSignalsButton.setIcon(icon)

        self.horizontalLayout.addWidget(self.rescanSignalsButton)

        self.horizontalLayout.setStretch(0, 4)
        self.horizontalLayout.setStretch(1, 1)

        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout)


        self.verticalLayout.addWidget(self.acquisitionGroupBox)


        self.retranslateUi(AcquisitionConfig)

        QMetaObject.connectSlotsByName(AcquisitionConfig)
    # setupUi

    def retranslateUi(self, AcquisitionConfig):
        AcquisitionConfig.setWindowTitle(QCoreApplication.translate("AcquisitionConfig", u"Acquisition Widget", None))
        self.acquisitionGroupBox.setTitle(QCoreApplication.translate("AcquisitionConfig", u"Configure acquisition", None))
        self.label1.setText(QCoreApplication.translate("AcquisitionConfig", u"Signal:", None))
        self.label2.setText(QCoreApplication.translate("AcquisitionConfig", u"Output file name:", None))
#if QT_CONFIG(tooltip)
        self.acquisitionTextField.setToolTip(QCoreApplication.translate("AcquisitionConfig", u"If no name is provided, one based on the timestamp will be used", None))
#endif // QT_CONFIG(tooltip)
        self.label3.setText(QCoreApplication.translate("AcquisitionConfig", u"JSON with configuration:", None))
        self.browseJSONButton.setText(QCoreApplication.translate("AcquisitionConfig", u"Browse", None))
        self.label4.setText(QCoreApplication.translate("AcquisitionConfig", u"Path to JSON:", None))
        self.configJSONPathLabel.setText("")
#if QT_CONFIG(tooltip)
        self.rescanSignalsButton.setToolTip(QCoreApplication.translate("AcquisitionConfig", u"Rescan signals", None))
#endif // QT_CONFIG(tooltip)
        self.rescanSignalsButton.setText("")
    # retranslateUi

