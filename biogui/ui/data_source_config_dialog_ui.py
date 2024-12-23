# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'data_source_config_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_DataSourceConfigDialog(object):
    def setupUi(self, DataSourceConfigDialog):
        if not DataSourceConfigDialog.objectName():
            DataSourceConfigDialog.setObjectName(u"DataSourceConfigDialog")
        DataSourceConfigDialog.resize(400, 310)
        self.verticalLayout = QVBoxLayout(DataSourceConfigDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFormAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label1 = QLabel(DataSourceConfigDialog)
        self.label1.setObjectName(u"label1")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.browseInterfaceModuleButton = QPushButton(DataSourceConfigDialog)
        self.browseInterfaceModuleButton.setObjectName(u"browseInterfaceModuleButton")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.browseInterfaceModuleButton)

        self.label2 = QLabel(DataSourceConfigDialog)
        self.label2.setObjectName(u"label2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.interfaceModulePathLabel = QLabel(DataSourceConfigDialog)
        self.interfaceModulePathLabel.setObjectName(u"interfaceModulePathLabel")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.interfaceModulePathLabel)

        self.label3 = QLabel(DataSourceConfigDialog)
        self.label3.setObjectName(u"label3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label3)

        self.sourceComboBox = QComboBox(DataSourceConfigDialog)
        self.sourceComboBox.setObjectName(u"sourceComboBox")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.sourceComboBox)


        self.verticalLayout.addLayout(self.formLayout)

        self.sourceConfigContainer = QVBoxLayout()
        self.sourceConfigContainer.setObjectName(u"sourceConfigContainer")

        self.verticalLayout.addLayout(self.sourceConfigContainer)

        self.fileSavingGroupBox = QGroupBox(DataSourceConfigDialog)
        self.fileSavingGroupBox.setObjectName(u"fileSavingGroupBox")
        self.fileSavingGroupBox.setAlignment(Qt.AlignCenter)
        self.fileSavingGroupBox.setCheckable(True)
        self.fileSavingGroupBox.setChecked(False)
        self.formLayout3 = QFormLayout(self.fileSavingGroupBox)
        self.formLayout3.setObjectName(u"formLayout3")
        self.formLayout3.setFormAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label4 = QLabel(self.fileSavingGroupBox)
        self.label4.setObjectName(u"label4")

        self.formLayout3.setWidget(1, QFormLayout.LabelRole, self.label4)

        self.browseOutDirButton = QPushButton(self.fileSavingGroupBox)
        self.browseOutDirButton.setObjectName(u"browseOutDirButton")

        self.formLayout3.setWidget(1, QFormLayout.FieldRole, self.browseOutDirButton)

        self.label5 = QLabel(self.fileSavingGroupBox)
        self.label5.setObjectName(u"label5")

        self.formLayout3.setWidget(2, QFormLayout.LabelRole, self.label5)

        self.outDirPathLabel = QLabel(self.fileSavingGroupBox)
        self.outDirPathLabel.setObjectName(u"outDirPathLabel")

        self.formLayout3.setWidget(2, QFormLayout.FieldRole, self.outDirPathLabel)

        self.label6 = QLabel(self.fileSavingGroupBox)
        self.label6.setObjectName(u"label6")

        self.formLayout3.setWidget(3, QFormLayout.LabelRole, self.label6)

        self.fileNameTextField = QLineEdit(self.fileSavingGroupBox)
        self.fileNameTextField.setObjectName(u"fileNameTextField")

        self.formLayout3.setWidget(3, QFormLayout.FieldRole, self.fileNameTextField)


        self.verticalLayout.addWidget(self.fileSavingGroupBox)

        self.buttonBox = QDialogButtonBox(DataSourceConfigDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

        QWidget.setTabOrder(self.browseInterfaceModuleButton, self.sourceComboBox)
        QWidget.setTabOrder(self.sourceComboBox, self.fileSavingGroupBox)
        QWidget.setTabOrder(self.fileSavingGroupBox, self.browseOutDirButton)
        QWidget.setTabOrder(self.browseOutDirButton, self.fileNameTextField)

        self.retranslateUi(DataSourceConfigDialog)

        QMetaObject.connectSlotsByName(DataSourceConfigDialog)
    # setupUi

    def retranslateUi(self, DataSourceConfigDialog):
        DataSourceConfigDialog.setWindowTitle(QCoreApplication.translate("DataSourceConfigDialog", u"Data Source Configuration", None))
        self.label1.setText(QCoreApplication.translate("DataSourceConfigDialog", u"Interface module:", None))
#if QT_CONFIG(tooltip)
        self.browseInterfaceModuleButton.setToolTip(QCoreApplication.translate("DataSourceConfigDialog", u"The module must contain a function called \"decodeFn\" that converts bytes into a sequence of signals", None))
#endif // QT_CONFIG(tooltip)
        self.browseInterfaceModuleButton.setText(QCoreApplication.translate("DataSourceConfigDialog", u"Browse", None))
        self.label2.setText(QCoreApplication.translate("DataSourceConfigDialog", u"Path to module:", None))
        self.interfaceModulePathLabel.setText("")
        self.label3.setText(QCoreApplication.translate("DataSourceConfigDialog", u"Source:", None))
#if QT_CONFIG(tooltip)
        self.sourceComboBox.setToolTip(QCoreApplication.translate("DataSourceConfigDialog", u"List of available serial ports", None))
#endif // QT_CONFIG(tooltip)
        self.fileSavingGroupBox.setTitle(QCoreApplication.translate("DataSourceConfigDialog", u"Configure file saving", None))
        self.label4.setText(QCoreApplication.translate("DataSourceConfigDialog", u"Output directory:", None))
        self.browseOutDirButton.setText(QCoreApplication.translate("DataSourceConfigDialog", u"Browse", None))
        self.label5.setText(QCoreApplication.translate("DataSourceConfigDialog", u"Path to directory:", None))
        self.outDirPathLabel.setText("")
        self.label6.setText(QCoreApplication.translate("DataSourceConfigDialog", u"File name:", None))
#if QT_CONFIG(tooltip)
        self.fileNameTextField.setToolTip(QCoreApplication.translate("DataSourceConfigDialog", u"If empty, the signal name will be used", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

