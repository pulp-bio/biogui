# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'add_signal_dialog.ui'
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
    QDialogButtonBox, QFormLayout, QFrame, QGroupBox,
    QLabel, QLineEdit, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_AddSignalDialog(object):
    def setupUi(self, AddSignalDialog):
        if not AddSignalDialog.objectName():
            AddSignalDialog.setObjectName(u"AddSignalDialog")
        AddSignalDialog.setWindowModality(Qt.WindowModal)
        AddSignalDialog.resize(640, 358)
        AddSignalDialog.setModal(False)
        self.verticalLayout = QVBoxLayout(AddSignalDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label1 = QLabel(AddSignalDialog)
        self.label1.setObjectName(u"label1")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.sigNameTextField = QLineEdit(AddSignalDialog)
        self.sigNameTextField.setObjectName(u"sigNameTextField")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.sigNameTextField)

        self.label2 = QLabel(AddSignalDialog)
        self.label2.setObjectName(u"label2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.nChTextField = QLineEdit(AddSignalDialog)
        self.nChTextField.setObjectName(u"nChTextField")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.nChTextField)

        self.label3 = QLabel(AddSignalDialog)
        self.label3.setObjectName(u"label3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label3)

        self.fsTextField = QLineEdit(AddSignalDialog)
        self.fsTextField.setObjectName(u"fsTextField")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.fsTextField)


        self.verticalLayout.addLayout(self.formLayout)

        self.filteringGroupBox = QGroupBox(AddSignalDialog)
        self.filteringGroupBox.setObjectName(u"filteringGroupBox")
        self.filteringGroupBox.setAlignment(Qt.AlignCenter)
        self.filteringGroupBox.setCheckable(True)
        self.formLayout_2 = QFormLayout(self.filteringGroupBox)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label4 = QLabel(self.filteringGroupBox)
        self.label4.setObjectName(u"label4")
        self.label4.setFrameShape(QFrame.NoFrame)

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label4)

        self.filtTypeComboBox = QComboBox(self.filteringGroupBox)
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.setObjectName(u"filtTypeComboBox")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.filtTypeComboBox)

        self.label = QLabel(self.filteringGroupBox)
        self.label.setObjectName(u"label")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label)

        self.freq1TextField = QLineEdit(self.filteringGroupBox)
        self.freq1TextField.setObjectName(u"freq1TextField")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.freq1TextField)

        self.label_2 = QLabel(self.filteringGroupBox)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_2)

        self.freq2TextField = QLineEdit(self.filteringGroupBox)
        self.freq2TextField.setObjectName(u"freq2TextField")
        self.freq2TextField.setEnabled(False)

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.freq2TextField)

        self.label_3 = QLabel(self.filteringGroupBox)
        self.label_3.setObjectName(u"label_3")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.label_3)

        self.filtOrderTextField = QLineEdit(self.filteringGroupBox)
        self.filtOrderTextField.setObjectName(u"filtOrderTextField")

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.filtOrderTextField)


        self.verticalLayout.addWidget(self.filteringGroupBox)

        self.buttonBox = QDialogButtonBox(AddSignalDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(AddSignalDialog)
        self.buttonBox.accepted.connect(AddSignalDialog.accept)
        self.buttonBox.rejected.connect(AddSignalDialog.reject)

        QMetaObject.connectSlotsByName(AddSignalDialog)
    # setupUi

    def retranslateUi(self, AddSignalDialog):
        AddSignalDialog.setWindowTitle(QCoreApplication.translate("AddSignalDialog", u"Add signal", None))
        self.label1.setText(QCoreApplication.translate("AddSignalDialog", u"Name:", None))
#if QT_CONFIG(tooltip)
        self.sigNameTextField.setToolTip(QCoreApplication.translate("AddSignalDialog", u"Name of the signal to display in the GUI", None))
#endif // QT_CONFIG(tooltip)
        self.sigNameTextField.setPlaceholderText("")
        self.label2.setText(QCoreApplication.translate("AddSignalDialog", u"Number of channels:", None))
#if QT_CONFIG(tooltip)
        self.nChTextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.nChTextField.setPlaceholderText("")
        self.label3.setText(QCoreApplication.translate("AddSignalDialog", u"Sampling frequency (in sps):", None))
#if QT_CONFIG(tooltip)
        self.fsTextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.fsTextField.setPlaceholderText("")
        self.filteringGroupBox.setTitle(QCoreApplication.translate("AddSignalDialog", u"Configure filtering", None))
        self.label4.setText(QCoreApplication.translate("AddSignalDialog", u"Type:", None))
        self.filtTypeComboBox.setItemText(0, QCoreApplication.translate("AddSignalDialog", u"highpass", None))
        self.filtTypeComboBox.setItemText(1, QCoreApplication.translate("AddSignalDialog", u"lowpass", None))
        self.filtTypeComboBox.setItemText(2, QCoreApplication.translate("AddSignalDialog", u"bandpass", None))
        self.filtTypeComboBox.setItemText(3, QCoreApplication.translate("AddSignalDialog", u"bandstop", None))

        self.label.setText(QCoreApplication.translate("AddSignalDialog", u"First critical frequency:", None))
#if QT_CONFIG(tooltip)
        self.freq1TextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.freq1TextField.setPlaceholderText("")
        self.label_2.setText(QCoreApplication.translate("AddSignalDialog", u"Second critical frequency:", None))
#if QT_CONFIG(tooltip)
        self.freq2TextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.freq2TextField.setPlaceholderText(QCoreApplication.translate("AddSignalDialog", u"For bandpass and bandstop only", None))
        self.label_3.setText(QCoreApplication.translate("AddSignalDialog", u"Filter order:", None))
#if QT_CONFIG(tooltip)
        self.filtOrderTextField.setToolTip(QCoreApplication.translate("AddSignalDialog", u"Order of the Butterworth filter (positive integer)", None))
#endif // QT_CONFIG(tooltip)
        self.filtOrderTextField.setPlaceholderText("")
    # retranslateUi

