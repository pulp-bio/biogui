# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'add_source_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_AddSourceDialog(object):
    def setupUi(self, AddSourceDialog):
        if not AddSourceDialog.objectName():
            AddSourceDialog.setObjectName(u"AddSourceDialog")
        AddSourceDialog.resize(312, 200)
        self.verticalLayout = QVBoxLayout(AddSourceDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label2 = QLabel(AddSourceDialog)
        self.label2.setObjectName(u"label2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.decodeModulePathLabel = QLabel(AddSourceDialog)
        self.decodeModulePathLabel.setObjectName(u"decodeModulePathLabel")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.decodeModulePathLabel)

        self.label3 = QLabel(AddSourceDialog)
        self.label3.setObjectName(u"label3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label3)

        self.packetSizeTextField = QLineEdit(AddSourceDialog)
        self.packetSizeTextField.setObjectName(u"packetSizeTextField")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.packetSizeTextField)

        self.label4 = QLabel(AddSourceDialog)
        self.label4.setObjectName(u"label4")
        self.label4.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label4)

        self.sourceComboBox = QComboBox(AddSourceDialog)
        self.sourceComboBox.setObjectName(u"sourceComboBox")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.sourceComboBox)

        self.browseDecodeModuleButton = QPushButton(AddSourceDialog)
        self.browseDecodeModuleButton.setObjectName(u"browseDecodeModuleButton")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.browseDecodeModuleButton)

        self.label1 = QLabel(AddSourceDialog)
        self.label1.setObjectName(u"label1")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)


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

        self.retranslateUi(AddSourceDialog)
        self.buttonBox.accepted.connect(AddSourceDialog.accept)
        self.buttonBox.rejected.connect(AddSourceDialog.reject)

        QMetaObject.connectSlotsByName(AddSourceDialog)
    # setupUi

    def retranslateUi(self, AddSourceDialog):
        AddSourceDialog.setWindowTitle(QCoreApplication.translate("AddSourceDialog", u"Add source", None))
        self.label2.setText(QCoreApplication.translate("AddSourceDialog", u"Path to module:", None))
        self.decodeModulePathLabel.setText("")
        self.label3.setText(QCoreApplication.translate("AddSourceDialog", u"Packet size:", None))
#if QT_CONFIG(tooltip)
        self.packetSizeTextField.setToolTip(QCoreApplication.translate("AddSourceDialog", u"Number of bytes in each packet", None))
#endif // QT_CONFIG(tooltip)
        self.label4.setText(QCoreApplication.translate("AddSourceDialog", u"Source:", None))
#if QT_CONFIG(tooltip)
        self.sourceComboBox.setToolTip(QCoreApplication.translate("AddSourceDialog", u"List of available serial ports", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.browseDecodeModuleButton.setToolTip(QCoreApplication.translate("AddSourceDialog", u"The module must contain a function called \"decodeFn\" that converts bytes into a sequence of signals", None))
#endif // QT_CONFIG(tooltip)
        self.browseDecodeModuleButton.setText(QCoreApplication.translate("AddSourceDialog", u"Browse", None))
        self.label1.setText(QCoreApplication.translate("AddSourceDialog", u"Module with decode function:", None))
    # retranslateUi

