# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'add_source_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_AddSourceDialog(object):
    def setupUi(self, AddSourceDialog):
        if not AddSourceDialog.objectName():
            AddSourceDialog.setObjectName(u"AddSourceDialog")
        AddSourceDialog.resize(480, 320)
        self.verticalLayout = QVBoxLayout(AddSourceDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label1 = QLabel(AddSourceDialog)
        self.label1.setObjectName(u"label1")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.browseInterfaceModuleButton = QPushButton(AddSourceDialog)
        self.browseInterfaceModuleButton.setObjectName(u"browseInterfaceModuleButton")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.browseInterfaceModuleButton)

        self.label2 = QLabel(AddSourceDialog)
        self.label2.setObjectName(u"label2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.interfaceModulePathLabel = QLabel(AddSourceDialog)
        self.interfaceModulePathLabel.setObjectName(u"interfaceModulePathLabel")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.interfaceModulePathLabel)

        self.label4 = QLabel(AddSourceDialog)
        self.label4.setObjectName(u"label4")
        self.label4.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label4)

        self.sourceComboBox = QComboBox(AddSourceDialog)
        self.sourceComboBox.setObjectName(u"sourceComboBox")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.sourceComboBox)


        self.verticalLayout.addLayout(self.formLayout)

        self.sourceConfigContainer = QVBoxLayout()
        self.sourceConfigContainer.setObjectName(u"sourceConfigContainer")

        self.verticalLayout.addLayout(self.sourceConfigContainer)

        self.buttonBox = QDialogButtonBox(AddSourceDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

        self.verticalLayout.setStretch(1, 1)
        QWidget.setTabOrder(self.browseInterfaceModuleButton, self.sourceComboBox)

        self.retranslateUi(AddSourceDialog)
        self.buttonBox.accepted.connect(AddSourceDialog.accept)
        self.buttonBox.rejected.connect(AddSourceDialog.reject)

        QMetaObject.connectSlotsByName(AddSourceDialog)
    # setupUi

    def retranslateUi(self, AddSourceDialog):
        AddSourceDialog.setWindowTitle(QCoreApplication.translate("AddSourceDialog", u"Add source", None))
        self.label1.setText(QCoreApplication.translate("AddSourceDialog", u"Interface module:", None))
#if QT_CONFIG(tooltip)
        self.browseInterfaceModuleButton.setToolTip(QCoreApplication.translate("AddSourceDialog", u"The module must contain a function called \"decodeFn\" that converts bytes into a sequence of signals", None))
#endif // QT_CONFIG(tooltip)
        self.browseInterfaceModuleButton.setText(QCoreApplication.translate("AddSourceDialog", u"Browse", None))
        self.label2.setText(QCoreApplication.translate("AddSourceDialog", u"Path to module:", None))
        self.interfaceModulePathLabel.setText("")
        self.label4.setText(QCoreApplication.translate("AddSourceDialog", u"Source:", None))
#if QT_CONFIG(tooltip)
        self.sourceComboBox.setToolTip(QCoreApplication.translate("AddSourceDialog", u"List of available serial ports", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

