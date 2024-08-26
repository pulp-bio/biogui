# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'add_data_source_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_AddDataSourceDialog(object):
    def setupUi(self, AddDataSourceDialog):
        if not AddDataSourceDialog.objectName():
            AddDataSourceDialog.setObjectName(u"AddDataSourceDialog")
        AddDataSourceDialog.resize(400, 200)
        self.verticalLayout = QVBoxLayout(AddDataSourceDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label1 = QLabel(AddDataSourceDialog)
        self.label1.setObjectName(u"label1")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.browseInterfaceModuleButton = QPushButton(AddDataSourceDialog)
        self.browseInterfaceModuleButton.setObjectName(u"browseInterfaceModuleButton")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.browseInterfaceModuleButton)

        self.label2 = QLabel(AddDataSourceDialog)
        self.label2.setObjectName(u"label2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.interfaceModulePathLabel = QLabel(AddDataSourceDialog)
        self.interfaceModulePathLabel.setObjectName(u"interfaceModulePathLabel")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.interfaceModulePathLabel)

        self.label4 = QLabel(AddDataSourceDialog)
        self.label4.setObjectName(u"label4")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label4)

        self.sourceComboBox = QComboBox(AddDataSourceDialog)
        self.sourceComboBox.setObjectName(u"sourceComboBox")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.sourceComboBox)


        self.verticalLayout.addLayout(self.formLayout)

        self.sourceConfigContainer = QVBoxLayout()
        self.sourceConfigContainer.setObjectName(u"sourceConfigContainer")

        self.verticalLayout.addLayout(self.sourceConfigContainer)

        self.buttonBox = QDialogButtonBox(AddDataSourceDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(AddDataSourceDialog)
        self.buttonBox.accepted.connect(AddDataSourceDialog.accept)
        self.buttonBox.rejected.connect(AddDataSourceDialog.reject)

        QMetaObject.connectSlotsByName(AddDataSourceDialog)
    # setupUi

    def retranslateUi(self, AddDataSourceDialog):
        AddDataSourceDialog.setWindowTitle(QCoreApplication.translate("AddDataSourceDialog", u"Add data source", None))
        self.label1.setText(QCoreApplication.translate("AddDataSourceDialog", u"Interface module:", None))
#if QT_CONFIG(tooltip)
        self.browseInterfaceModuleButton.setToolTip(QCoreApplication.translate("AddDataSourceDialog", u"The module must contain a function called \"decodeFn\" that converts bytes into a sequence of signals", None))
#endif // QT_CONFIG(tooltip)
        self.browseInterfaceModuleButton.setText(QCoreApplication.translate("AddDataSourceDialog", u"Browse", None))
        self.label2.setText(QCoreApplication.translate("AddDataSourceDialog", u"Path to module:", None))
        self.interfaceModulePathLabel.setText("")
        self.label4.setText(QCoreApplication.translate("AddDataSourceDialog", u"Source:", None))
#if QT_CONFIG(tooltip)
        self.sourceComboBox.setToolTip(QCoreApplication.translate("AddDataSourceDialog", u"List of available serial ports", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

