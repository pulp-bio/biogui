# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'trigger_config.ui'
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

class Ui_TriggerConfig(object):
    def setupUi(self, TriggerConfig):
        if not TriggerConfig.objectName():
            TriggerConfig.setObjectName(u"TriggerConfig")
        TriggerConfig.resize(400, 132)
        self.verticalLayout = QVBoxLayout(TriggerConfig)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.triggerGroupBox = QGroupBox(TriggerConfig)
        self.triggerGroupBox.setObjectName(u"triggerGroupBox")
        self.triggerGroupBox.setAlignment(Qt.AlignCenter)
        self.triggerGroupBox.setCheckable(True)
        self.triggerGroupBox.setChecked(False)
        self.formLayout = QFormLayout(self.triggerGroupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.label1 = QLabel(self.triggerGroupBox)
        self.label1.setObjectName(u"label1")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label1)

        self.browseJSONButton = QPushButton(self.triggerGroupBox)
        self.browseJSONButton.setObjectName(u"browseJSONButton")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.browseJSONButton)

        self.label2 = QLabel(self.triggerGroupBox)
        self.label2.setObjectName(u"label2")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label2)

        self.configJSONPathLabel = QLabel(self.triggerGroupBox)
        self.configJSONPathLabel.setObjectName(u"configJSONPathLabel")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.configJSONPathLabel)


        self.verticalLayout.addWidget(self.triggerGroupBox)


        self.retranslateUi(TriggerConfig)

        QMetaObject.connectSlotsByName(TriggerConfig)
    # setupUi

    def retranslateUi(self, TriggerConfig):
        TriggerConfig.setWindowTitle(QCoreApplication.translate("TriggerConfig", u"Trigger configuration widget", None))
        self.triggerGroupBox.setTitle(QCoreApplication.translate("TriggerConfig", u"Configure triggers", None))
        self.label1.setText(QCoreApplication.translate("TriggerConfig", u"JSON with configuration:", None))
        self.browseJSONButton.setText(QCoreApplication.translate("TriggerConfig", u"Browse", None))
        self.label2.setText(QCoreApplication.translate("TriggerConfig", u"Path to JSON:", None))
        self.configJSONPathLabel.setText("")
    # retranslateUi

