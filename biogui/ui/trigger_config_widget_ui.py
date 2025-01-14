# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'trigger_config_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QGroupBox, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_TriggerConfigWidget(object):
    def setupUi(self, TriggerConfigWidget):
        if not TriggerConfigWidget.objectName():
            TriggerConfigWidget.setObjectName(u"TriggerConfigWidget")
        TriggerConfigWidget.resize(400, 108)
        self.verticalLayout = QVBoxLayout(TriggerConfigWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.triggerGroupBox = QGroupBox(TriggerConfigWidget)
        self.triggerGroupBox.setObjectName(u"triggerGroupBox")
        self.triggerGroupBox.setAlignment(Qt.AlignCenter)
        self.triggerGroupBox.setCheckable(True)
        self.triggerGroupBox.setChecked(False)
        self.formLayout = QFormLayout(self.triggerGroupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.browseTriggerConfigButton = QPushButton(self.triggerGroupBox)
        self.browseTriggerConfigButton.setObjectName(u"browseTriggerConfigButton")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.browseTriggerConfigButton)

        self.triggerConfigPathLabel = QLabel(self.triggerGroupBox)
        self.triggerConfigPathLabel.setObjectName(u"triggerConfigPathLabel")
        self.triggerConfigPathLabel.setWordWrap(True)

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.triggerConfigPathLabel)


        self.verticalLayout.addWidget(self.triggerGroupBox)


        self.retranslateUi(TriggerConfigWidget)

        QMetaObject.connectSlotsByName(TriggerConfigWidget)
    # setupUi

    def retranslateUi(self, TriggerConfigWidget):
        TriggerConfigWidget.setWindowTitle(QCoreApplication.translate("TriggerConfigWidget", u"Trigger Configuration Widget", None))
        self.triggerGroupBox.setTitle(QCoreApplication.translate("TriggerConfigWidget", u"Configure triggers", None))
        self.browseTriggerConfigButton.setText(QCoreApplication.translate("TriggerConfigWidget", u"Browse JSON file", None))
        self.triggerConfigPathLabel.setText("")
    # retranslateUi

