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
    QLayout, QLineEdit, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_DataSourceConfigDialog(object):
    def setupUi(self, DataSourceConfigDialog):
        if not DataSourceConfigDialog.objectName():
            DataSourceConfigDialog.setObjectName(u"DataSourceConfigDialog")
        DataSourceConfigDialog.resize(400, 300)
        self.verticalLayout = QVBoxLayout(DataSourceConfigDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.browseInterfaceModuleButton = QPushButton(DataSourceConfigDialog)
        self.browseInterfaceModuleButton.setObjectName(u"browseInterfaceModuleButton")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.browseInterfaceModuleButton)

        self.interfaceModulePathLabel = QLabel(DataSourceConfigDialog)
        self.interfaceModulePathLabel.setObjectName(u"interfaceModulePathLabel")
        self.interfaceModulePathLabel.setWordWrap(True)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.interfaceModulePathLabel)

        self.label1 = QLabel(DataSourceConfigDialog)
        self.label1.setObjectName(u"label1")
        self.label1.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label1)

        self.dataSourceComboBox = QComboBox(DataSourceConfigDialog)
        self.dataSourceComboBox.setObjectName(u"dataSourceComboBox")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.dataSourceComboBox)


        self.verticalLayout.addLayout(self.formLayout)

        self.dataSourceConfigContainer = QVBoxLayout()
        self.dataSourceConfigContainer.setObjectName(u"dataSourceConfigContainer")

        self.verticalLayout.addLayout(self.dataSourceConfigContainer)

        self.fileSavingGroupBox = QGroupBox(DataSourceConfigDialog)
        self.fileSavingGroupBox.setObjectName(u"fileSavingGroupBox")
        self.fileSavingGroupBox.setAlignment(Qt.AlignCenter)
        self.fileSavingGroupBox.setCheckable(True)
        self.fileSavingGroupBox.setChecked(False)
        self.formLayout_2 = QFormLayout(self.fileSavingGroupBox)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.browseOutDirButton = QPushButton(self.fileSavingGroupBox)
        self.browseOutDirButton.setObjectName(u"browseOutDirButton")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.browseOutDirButton)

        self.outDirPathLabel = QLabel(self.fileSavingGroupBox)
        self.outDirPathLabel.setObjectName(u"outDirPathLabel")
        self.outDirPathLabel.setWordWrap(True)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.outDirPathLabel)

        self.label2 = QLabel(self.fileSavingGroupBox)
        self.label2.setObjectName(u"label2")
        self.label2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.fileNameTextField = QLineEdit(self.fileSavingGroupBox)
        self.fileNameTextField.setObjectName(u"fileNameTextField")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.fileNameTextField)


        self.verticalLayout.addWidget(self.fileSavingGroupBox)

        self.buttonBox = QDialogButtonBox(DataSourceConfigDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(DataSourceConfigDialog)

        QMetaObject.connectSlotsByName(DataSourceConfigDialog)
    # setupUi

    def retranslateUi(self, DataSourceConfigDialog):
        DataSourceConfigDialog.setWindowTitle(QCoreApplication.translate("DataSourceConfigDialog", u"Data Source Configuration", None))
#if QT_CONFIG(tooltip)
        self.browseInterfaceModuleButton.setToolTip(QCoreApplication.translate("DataSourceConfigDialog", u"The module must contain specific fields", None))
#endif // QT_CONFIG(tooltip)
        self.browseInterfaceModuleButton.setText(QCoreApplication.translate("DataSourceConfigDialog", u"Browse interface module", None))
        self.interfaceModulePathLabel.setText("")
        self.label1.setText(QCoreApplication.translate("DataSourceConfigDialog", u"Data source:", None))
#if QT_CONFIG(tooltip)
        self.dataSourceComboBox.setToolTip(QCoreApplication.translate("DataSourceConfigDialog", u"List of available data sources", None))
#endif // QT_CONFIG(tooltip)
        self.fileSavingGroupBox.setTitle(QCoreApplication.translate("DataSourceConfigDialog", u"Configure file saving", None))
        self.browseOutDirButton.setText(QCoreApplication.translate("DataSourceConfigDialog", u"Browse output directory", None))
        self.outDirPathLabel.setText("")
        self.label2.setText(QCoreApplication.translate("DataSourceConfigDialog", u"File name:", None))
#if QT_CONFIG(tooltip)
        self.fileNameTextField.setToolTip(QCoreApplication.translate("DataSourceConfigDialog", u"A timestamp corresponding to the start of the acquisition will be appended to the signal name", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

