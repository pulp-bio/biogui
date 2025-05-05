# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'processing_config_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_ProcessingConfigWidget(object):
    def setupUi(self, ProcessingConfigWidget):
        if not ProcessingConfigWidget.objectName():
            ProcessingConfigWidget.setObjectName(u"ProcessingConfigWidget")
        ProcessingConfigWidget.resize(400, 500)
        self.verticalLayout1 = QVBoxLayout(ProcessingConfigWidget)
        self.verticalLayout1.setObjectName(u"verticalLayout1")
        self.customProcessingGroupBox = QGroupBox(ProcessingConfigWidget)
        self.customProcessingGroupBox.setObjectName(u"customProcessingGroupBox")
        self.customProcessingGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.customProcessingGroupBox.setCheckable(True)
        self.customProcessingGroupBox.setChecked(False)
        self.verticalLayout2 = QVBoxLayout(self.customProcessingGroupBox)
        self.verticalLayout2.setObjectName(u"verticalLayout2")
        self.formLayout2 = QFormLayout()
        self.formLayout2.setObjectName(u"formLayout2")
        self.browseProcessingModuleButton = QPushButton(self.customProcessingGroupBox)
        self.browseProcessingModuleButton.setObjectName(u"browseProcessingModuleButton")

        self.formLayout2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.browseProcessingModuleButton)

        self.processingModulePathLabel = QLabel(self.customProcessingGroupBox)
        self.processingModulePathLabel.setObjectName(u"processingModulePathLabel")
        self.processingModulePathLabel.setWordWrap(True)

        self.formLayout2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.processingModulePathLabel)

        self.label2 = QLabel(self.customProcessingGroupBox)
        self.label2.setObjectName(u"label2")
        self.label2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label2)

        self.socketPortTextField = QLineEdit(self.customProcessingGroupBox)
        self.socketPortTextField.setObjectName(u"socketPortTextField")

        self.formLayout2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.socketPortTextField)

        self.label3 = QLabel(self.customProcessingGroupBox)
        self.label3.setObjectName(u"label3")
        self.label3.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout2.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label3)

        self.dataSourceComboBox = QComboBox(self.customProcessingGroupBox)
        self.dataSourceComboBox.setObjectName(u"dataSourceComboBox")
        self.dataSourceComboBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        self.formLayout2.setWidget(3, QFormLayout.ItemRole.FieldRole, self.dataSourceComboBox)

        self.label1 = QLabel(self.customProcessingGroupBox)
        self.label1.setObjectName(u"label1")

        self.formLayout2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label1)

        self.socketAddressTextField = QLineEdit(self.customProcessingGroupBox)
        self.socketAddressTextField.setObjectName(u"socketAddressTextField")

        self.formLayout2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.socketAddressTextField)


        self.verticalLayout2.addLayout(self.formLayout2)

        self.signalsGroupBox = QGroupBox(self.customProcessingGroupBox)
        self.signalsGroupBox.setObjectName(u"signalsGroupBox")
        self.signalsGroupBox.setEnabled(True)
        self.verticalLayout3 = QVBoxLayout(self.signalsGroupBox)
        self.verticalLayout3.setObjectName(u"verticalLayout3")

        self.verticalLayout2.addWidget(self.signalsGroupBox)


        self.verticalLayout1.addWidget(self.customProcessingGroupBox)

        QWidget.setTabOrder(self.customProcessingGroupBox, self.socketAddressTextField)
        QWidget.setTabOrder(self.socketAddressTextField, self.socketPortTextField)
        QWidget.setTabOrder(self.socketPortTextField, self.browseProcessingModuleButton)
        QWidget.setTabOrder(self.browseProcessingModuleButton, self.dataSourceComboBox)

        self.retranslateUi(ProcessingConfigWidget)

        QMetaObject.connectSlotsByName(ProcessingConfigWidget)
    # setupUi

    def retranslateUi(self, ProcessingConfigWidget):
        ProcessingConfigWidget.setWindowTitle(QCoreApplication.translate("ProcessingConfigWidget", u"Processing Configuration Widget", None))
        self.customProcessingGroupBox.setTitle(QCoreApplication.translate("ProcessingConfigWidget", u"Configure custom processing", None))
#if QT_CONFIG(tooltip)
        self.browseProcessingModuleButton.setToolTip(QCoreApplication.translate("ProcessingConfigWidget", u"The module must contain specific fields", None))
#endif // QT_CONFIG(tooltip)
        self.browseProcessingModuleButton.setText(QCoreApplication.translate("ProcessingConfigWidget", u"Browse processing module", None))
        self.processingModulePathLabel.setText("")
#if QT_CONFIG(tooltip)
        self.label2.setToolTip(QCoreApplication.translate("ProcessingConfigWidget", u"For the process to which the results will be sent", None))
#endif // QT_CONFIG(tooltip)
        self.label2.setText(QCoreApplication.translate("ProcessingConfigWidget", u"Socket port:", None))
        self.label3.setText(QCoreApplication.translate("ProcessingConfigWidget", u"Data source:", None))
        self.label1.setText(QCoreApplication.translate("ProcessingConfigWidget", u"Socket address:", None))
        self.signalsGroupBox.setTitle(QCoreApplication.translate("ProcessingConfigWidget", u"Signals to process", None))
    # retranslateUi

