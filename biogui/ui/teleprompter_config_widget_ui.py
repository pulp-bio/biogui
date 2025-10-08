# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'teleprompter_config_widget.ui'
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

class Ui_TeleprompterConfigWidget(object):
    def setupUi(self, TeleprompterConfigWidget):
        if not TeleprompterConfigWidget.objectName():
            TeleprompterConfigWidget.setObjectName(u"TeleprompterConfigWidget")
        TeleprompterConfigWidget.resize(400, 123)
        self.verticalLayout = QVBoxLayout(TeleprompterConfigWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.teleprompterGroupBox = QGroupBox(TeleprompterConfigWidget)
        self.teleprompterGroupBox.setObjectName(u"teleprompterGroupBox")
        self.teleprompterGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.teleprompterGroupBox.setCheckable(True)
        self.teleprompterGroupBox.setChecked(False)
        self.formLayout = QFormLayout(self.teleprompterGroupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.browseTeleprompterConfigButton = QPushButton(self.teleprompterGroupBox)
        self.browseTeleprompterConfigButton.setObjectName(u"browseTeleprompterConfigButton")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.browseTeleprompterConfigButton)

        self.teleprompterConfigPathLabel = QLabel(self.teleprompterGroupBox)
        self.teleprompterConfigPathLabel.setObjectName(u"teleprompterConfigPathLabel")
        self.teleprompterConfigPathLabel.setWordWrap(True)

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.teleprompterConfigPathLabel)


        self.verticalLayout.addWidget(self.teleprompterGroupBox)


        self.retranslateUi(TeleprompterConfigWidget)

        QMetaObject.connectSlotsByName(TeleprompterConfigWidget)
    # setupUi

    def retranslateUi(self, TeleprompterConfigWidget):
        TeleprompterConfigWidget.setWindowTitle(QCoreApplication.translate("TeleprompterConfigWidget", u"Trigger Configuration Widget", None))
        self.teleprompterGroupBox.setTitle(QCoreApplication.translate("TeleprompterConfigWidget", u"Configure triggers", None))
#if QT_CONFIG(tooltip)
        self.browseTeleprompterConfigButton.setToolTip(QCoreApplication.translate("TeleprompterConfigWidget", u"The JSON file must contain specific fields", None))
#endif // QT_CONFIG(tooltip)
        self.browseTeleprompterConfigButton.setText(QCoreApplication.translate("TeleprompterConfigWidget", u"Browse JSON file", None))
        self.teleprompterConfigPathLabel.setText("")
    # retranslateUi

