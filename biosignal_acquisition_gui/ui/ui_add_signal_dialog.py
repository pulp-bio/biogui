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
        AddSignalDialog.resize(720, 600)
        AddSignalDialog.setModal(False)
        self.verticalLayout = QVBoxLayout(AddSignalDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label1 = QLabel(AddSignalDialog)
        self.label1.setObjectName(u"label1")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.sourceComboBox = QComboBox(AddSignalDialog)
        self.sourceComboBox.setObjectName(u"sourceComboBox")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.sourceComboBox)

        self.label2 = QLabel(AddSignalDialog)
        self.label2.setObjectName(u"label2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.sigNameTextField = QLineEdit(AddSignalDialog)
        self.sigNameTextField.setObjectName(u"sigNameTextField")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.sigNameTextField)

        self.label3 = QLabel(AddSignalDialog)
        self.label3.setObjectName(u"label3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label3)

        self.nChTextField = QLineEdit(AddSignalDialog)
        self.nChTextField.setObjectName(u"nChTextField")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.nChTextField)

        self.label4 = QLabel(AddSignalDialog)
        self.label4.setObjectName(u"label4")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label4)

        self.fsTextField = QLineEdit(AddSignalDialog)
        self.fsTextField.setObjectName(u"fsTextField")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.fsTextField)


        self.verticalLayout.addLayout(self.formLayout)

        self.filteringGroupBox = QGroupBox(AddSignalDialog)
        self.filteringGroupBox.setObjectName(u"filteringGroupBox")
        self.filteringGroupBox.setAlignment(Qt.AlignCenter)
        self.filteringGroupBox.setCheckable(True)
        self.formLayout_2 = QFormLayout(self.filteringGroupBox)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label5 = QLabel(self.filteringGroupBox)
        self.label5.setObjectName(u"label5")
        self.label5.setFrameShape(QFrame.NoFrame)

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label5)

        self.filtTypeComboBox = QComboBox(self.filteringGroupBox)
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.setObjectName(u"filtTypeComboBox")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.filtTypeComboBox)

        self.label6 = QLabel(self.filteringGroupBox)
        self.label6.setObjectName(u"label6")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label6)

        self.freq1TextField = QLineEdit(self.filteringGroupBox)
        self.freq1TextField.setObjectName(u"freq1TextField")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.freq1TextField)

        self.label7 = QLabel(self.filteringGroupBox)
        self.label7.setObjectName(u"label7")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label7)

        self.freq2TextField = QLineEdit(self.filteringGroupBox)
        self.freq2TextField.setObjectName(u"freq2TextField")
        self.freq2TextField.setEnabled(False)

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.freq2TextField)

        self.label8 = QLabel(self.filteringGroupBox)
        self.label8.setObjectName(u"label8")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.label8)

        self.filtOrderTextField = QLineEdit(self.filteringGroupBox)
        self.filtOrderTextField.setObjectName(u"filtOrderTextField")

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.filtOrderTextField)


        self.verticalLayout.addWidget(self.filteringGroupBox)

        self.groupBox = QGroupBox(AddSignalDialog)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setAlignment(Qt.AlignCenter)
        self.groupBox.setCheckable(True)
        self.groupBox.setChecked(False)
        self.formLayout_3 = QFormLayout(self.groupBox)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label9 = QLabel(self.groupBox)
        self.label9.setObjectName(u"label9")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label9)

        self.fileNameTextField = QLineEdit(self.groupBox)
        self.fileNameTextField.setObjectName(u"fileNameTextField")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.fileNameTextField)


        self.verticalLayout.addWidget(self.groupBox)

        self.chSpacingGroupBox = QGroupBox(AddSignalDialog)
        self.chSpacingGroupBox.setObjectName(u"chSpacingGroupBox")
        self.chSpacingGroupBox.setAlignment(Qt.AlignCenter)
        self.chSpacingGroupBox.setFlat(False)
        self.chSpacingGroupBox.setCheckable(False)
        self.chSpacingGroupBox.setChecked(False)
        self.formLayout_4 = QFormLayout(self.chSpacingGroupBox)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.label10 = QLabel(self.chSpacingGroupBox)
        self.label10.setObjectName(u"label10")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label10)

        self.chSpacingTextField = QLineEdit(self.chSpacingGroupBox)
        self.chSpacingTextField.setObjectName(u"chSpacingTextField")

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.chSpacingTextField)

        self.label11 = QLabel(self.chSpacingGroupBox)
        self.label11.setObjectName(u"label11")

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.label11)

        self.bufferSizeTextField = QLineEdit(self.chSpacingGroupBox)
        self.bufferSizeTextField.setObjectName(u"bufferSizeTextField")

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.bufferSizeTextField)


        self.verticalLayout.addWidget(self.chSpacingGroupBox)

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
        self.label1.setText(QCoreApplication.translate("AddSignalDialog", u"Source:", None))
        self.label2.setText(QCoreApplication.translate("AddSignalDialog", u"Name:", None))
#if QT_CONFIG(tooltip)
        self.sigNameTextField.setToolTip(QCoreApplication.translate("AddSignalDialog", u"Name of the signal to display in the GUI", None))
#endif // QT_CONFIG(tooltip)
        self.sigNameTextField.setPlaceholderText("")
        self.label3.setText(QCoreApplication.translate("AddSignalDialog", u"Number of channels:", None))
#if QT_CONFIG(tooltip)
        self.nChTextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.nChTextField.setPlaceholderText("")
        self.label4.setText(QCoreApplication.translate("AddSignalDialog", u"Sampling frequency (in sps):", None))
#if QT_CONFIG(tooltip)
        self.fsTextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.fsTextField.setPlaceholderText("")
#if QT_CONFIG(tooltip)
        self.filteringGroupBox.setToolTip(QCoreApplication.translate("AddSignalDialog", u"Only for visualization, the raw signal will be saved to file", None))
#endif // QT_CONFIG(tooltip)
        self.filteringGroupBox.setTitle(QCoreApplication.translate("AddSignalDialog", u"Configure filtering", None))
        self.label5.setText(QCoreApplication.translate("AddSignalDialog", u"Type:", None))
        self.filtTypeComboBox.setItemText(0, QCoreApplication.translate("AddSignalDialog", u"highpass", None))
        self.filtTypeComboBox.setItemText(1, QCoreApplication.translate("AddSignalDialog", u"lowpass", None))
        self.filtTypeComboBox.setItemText(2, QCoreApplication.translate("AddSignalDialog", u"bandpass", None))
        self.filtTypeComboBox.setItemText(3, QCoreApplication.translate("AddSignalDialog", u"bandstop", None))

        self.label6.setText(QCoreApplication.translate("AddSignalDialog", u"First critical frequency:", None))
#if QT_CONFIG(tooltip)
        self.freq1TextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.freq1TextField.setPlaceholderText("")
        self.label7.setText(QCoreApplication.translate("AddSignalDialog", u"Second critical frequency:", None))
#if QT_CONFIG(tooltip)
        self.freq2TextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.freq2TextField.setPlaceholderText(QCoreApplication.translate("AddSignalDialog", u"For bandpass and bandstop only", None))
        self.label8.setText(QCoreApplication.translate("AddSignalDialog", u"Filter order:", None))
#if QT_CONFIG(tooltip)
        self.filtOrderTextField.setToolTip(QCoreApplication.translate("AddSignalDialog", u"Order of the Butterworth filter (positive integer)", None))
#endif // QT_CONFIG(tooltip)
        self.filtOrderTextField.setPlaceholderText("")
        self.groupBox.setTitle(QCoreApplication.translate("AddSignalDialog", u"Configure file saving", None))
        self.label9.setText(QCoreApplication.translate("AddSignalDialog", u"File name:", None))
#if QT_CONFIG(tooltip)
        self.chSpacingGroupBox.setToolTip(QCoreApplication.translate("AddSignalDialog", u"Only for multi-channel signals", None))
#endif // QT_CONFIG(tooltip)
        self.chSpacingGroupBox.setTitle(QCoreApplication.translate("AddSignalDialog", u"Configure plot", None))
        self.label10.setText(QCoreApplication.translate("AddSignalDialog", u"Channel spacing:", None))
        self.chSpacingTextField.setText(QCoreApplication.translate("AddSignalDialog", u"1000", None))
        self.chSpacingTextField.setPlaceholderText("")
        self.label11.setText(QCoreApplication.translate("AddSignalDialog", u"Buffer size (ms):", None))
        self.bufferSizeTextField.setText(QCoreApplication.translate("AddSignalDialog", u"200", None))
        self.bufferSizeTextField.setPlaceholderText("")
    # retranslateUi

