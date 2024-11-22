# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'add_signal_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
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
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_AddSignalDialog(object):
    def setupUi(self, AddSignalDialog):
        if not AddSignalDialog.objectName():
            AddSignalDialog.setObjectName(u"AddSignalDialog")
        AddSignalDialog.setWindowModality(Qt.WindowModal)
        AddSignalDialog.resize(500, 702)
        AddSignalDialog.setModal(False)
        self.verticalLayout = QVBoxLayout(AddSignalDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout1 = QFormLayout()
        self.formLayout1.setObjectName(u"formLayout1")
        self.label1 = QLabel(AddSignalDialog)
        self.label1.setObjectName(u"label1")

        self.formLayout1.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.sigNameLabel = QLabel(AddSignalDialog)
        self.sigNameLabel.setObjectName(u"sigNameLabel")

        self.formLayout1.setWidget(0, QFormLayout.FieldRole, self.sigNameLabel)

        self.label2 = QLabel(AddSignalDialog)
        self.label2.setObjectName(u"label2")

        self.formLayout1.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.nChLabel = QLabel(AddSignalDialog)
        self.nChLabel.setObjectName(u"nChLabel")

        self.formLayout1.setWidget(1, QFormLayout.FieldRole, self.nChLabel)

        self.label3 = QLabel(AddSignalDialog)
        self.label3.setObjectName(u"label3")

        self.formLayout1.setWidget(2, QFormLayout.LabelRole, self.label3)

        self.freqLabel = QLabel(AddSignalDialog)
        self.freqLabel.setObjectName(u"freqLabel")

        self.formLayout1.setWidget(2, QFormLayout.FieldRole, self.freqLabel)


        self.verticalLayout.addLayout(self.formLayout1)

        self.filteringGroupBox = QGroupBox(AddSignalDialog)
        self.filteringGroupBox.setObjectName(u"filteringGroupBox")
        self.filteringGroupBox.setAlignment(Qt.AlignCenter)
        self.filteringGroupBox.setCheckable(True)
        self.filteringGroupBox.setChecked(False)
        self.formLayout2 = QFormLayout(self.filteringGroupBox)
        self.formLayout2.setObjectName(u"formLayout2")
        self.label4 = QLabel(self.filteringGroupBox)
        self.label4.setObjectName(u"label4")
        self.label4.setFrameShape(QFrame.NoFrame)

        self.formLayout2.setWidget(0, QFormLayout.LabelRole, self.label4)

        self.filtTypeComboBox = QComboBox(self.filteringGroupBox)
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.setObjectName(u"filtTypeComboBox")

        self.formLayout2.setWidget(0, QFormLayout.FieldRole, self.filtTypeComboBox)

        self.label5 = QLabel(self.filteringGroupBox)
        self.label5.setObjectName(u"label5")

        self.formLayout2.setWidget(1, QFormLayout.LabelRole, self.label5)

        self.freq1TextField = QLineEdit(self.filteringGroupBox)
        self.freq1TextField.setObjectName(u"freq1TextField")

        self.formLayout2.setWidget(1, QFormLayout.FieldRole, self.freq1TextField)

        self.label6 = QLabel(self.filteringGroupBox)
        self.label6.setObjectName(u"label6")

        self.formLayout2.setWidget(2, QFormLayout.LabelRole, self.label6)

        self.freq2TextField = QLineEdit(self.filteringGroupBox)
        self.freq2TextField.setObjectName(u"freq2TextField")
        self.freq2TextField.setEnabled(False)

        self.formLayout2.setWidget(2, QFormLayout.FieldRole, self.freq2TextField)

        self.label7 = QLabel(self.filteringGroupBox)
        self.label7.setObjectName(u"label7")

        self.formLayout2.setWidget(3, QFormLayout.LabelRole, self.label7)

        self.filtOrderTextField = QLineEdit(self.filteringGroupBox)
        self.filtOrderTextField.setObjectName(u"filtOrderTextField")

        self.formLayout2.setWidget(3, QFormLayout.FieldRole, self.filtOrderTextField)


        self.verticalLayout.addWidget(self.filteringGroupBox)

        self.fileSavingGroupBox = QGroupBox(AddSignalDialog)
        self.fileSavingGroupBox.setObjectName(u"fileSavingGroupBox")
        self.fileSavingGroupBox.setAlignment(Qt.AlignCenter)
        self.fileSavingGroupBox.setCheckable(True)
        self.fileSavingGroupBox.setChecked(False)
        self.formLayout3 = QFormLayout(self.fileSavingGroupBox)
        self.formLayout3.setObjectName(u"formLayout3")
        self.label8 = QLabel(self.fileSavingGroupBox)
        self.label8.setObjectName(u"label8")

        self.formLayout3.setWidget(1, QFormLayout.LabelRole, self.label8)

        self.browseOutDirButton = QPushButton(self.fileSavingGroupBox)
        self.browseOutDirButton.setObjectName(u"browseOutDirButton")

        self.formLayout3.setWidget(1, QFormLayout.FieldRole, self.browseOutDirButton)

        self.label9 = QLabel(self.fileSavingGroupBox)
        self.label9.setObjectName(u"label9")

        self.formLayout3.setWidget(2, QFormLayout.LabelRole, self.label9)

        self.outDirPathLabel = QLabel(self.fileSavingGroupBox)
        self.outDirPathLabel.setObjectName(u"outDirPathLabel")

        self.formLayout3.setWidget(2, QFormLayout.FieldRole, self.outDirPathLabel)

        self.label10 = QLabel(self.fileSavingGroupBox)
        self.label10.setObjectName(u"label10")

        self.formLayout3.setWidget(3, QFormLayout.LabelRole, self.label10)

        self.fileNameTextField = QLineEdit(self.fileSavingGroupBox)
        self.fileNameTextField.setObjectName(u"fileNameTextField")

        self.formLayout3.setWidget(3, QFormLayout.FieldRole, self.fileNameTextField)


        self.verticalLayout.addWidget(self.fileSavingGroupBox)

        self.plotGroupBox = QGroupBox(AddSignalDialog)
        self.plotGroupBox.setObjectName(u"plotGroupBox")
        self.plotGroupBox.setAlignment(Qt.AlignCenter)
        self.plotGroupBox.setFlat(False)
        self.plotGroupBox.setCheckable(True)
        self.plotGroupBox.setChecked(True)
        self.formLayout4 = QFormLayout(self.plotGroupBox)
        self.formLayout4.setObjectName(u"formLayout4")
        self.label11 = QLabel(self.plotGroupBox)
        self.label11.setObjectName(u"label11")

        self.formLayout4.setWidget(0, QFormLayout.LabelRole, self.label11)

        self.renderLenTextField = QLineEdit(self.plotGroupBox)
        self.renderLenTextField.setObjectName(u"renderLenTextField")

        self.formLayout4.setWidget(0, QFormLayout.FieldRole, self.renderLenTextField)

        self.label12 = QLabel(self.plotGroupBox)
        self.label12.setObjectName(u"label12")

        self.formLayout4.setWidget(1, QFormLayout.LabelRole, self.label12)

        self.chSpacingTextField = QLineEdit(self.plotGroupBox)
        self.chSpacingTextField.setObjectName(u"chSpacingTextField")

        self.formLayout4.setWidget(1, QFormLayout.FieldRole, self.chSpacingTextField)

        self.label13 = QLabel(self.plotGroupBox)
        self.label13.setObjectName(u"label13")

        self.formLayout4.setWidget(2, QFormLayout.LabelRole, self.label13)

        self.rangeModeComboBox = QComboBox(self.plotGroupBox)
        self.rangeModeComboBox.addItem("")
        self.rangeModeComboBox.addItem("")
        self.rangeModeComboBox.setObjectName(u"rangeModeComboBox")

        self.formLayout4.setWidget(2, QFormLayout.FieldRole, self.rangeModeComboBox)

        self.label14 = QLabel(self.plotGroupBox)
        self.label14.setObjectName(u"label14")
        self.label14.setEnabled(False)

        self.formLayout4.setWidget(3, QFormLayout.LabelRole, self.label14)

        self.minRangeTextField = QLineEdit(self.plotGroupBox)
        self.minRangeTextField.setObjectName(u"minRangeTextField")
        self.minRangeTextField.setEnabled(False)

        self.formLayout4.setWidget(3, QFormLayout.FieldRole, self.minRangeTextField)

        self.label15 = QLabel(self.plotGroupBox)
        self.label15.setObjectName(u"label15")
        self.label15.setEnabled(False)

        self.formLayout4.setWidget(4, QFormLayout.LabelRole, self.label15)

        self.maxRangeTextField = QLineEdit(self.plotGroupBox)
        self.maxRangeTextField.setObjectName(u"maxRangeTextField")
        self.maxRangeTextField.setEnabled(False)

        self.formLayout4.setWidget(4, QFormLayout.FieldRole, self.maxRangeTextField)


        self.verticalLayout.addWidget(self.plotGroupBox)

        self.buttonBox = QDialogButtonBox(AddSignalDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

        QWidget.setTabOrder(self.filteringGroupBox, self.filtTypeComboBox)
        QWidget.setTabOrder(self.filtTypeComboBox, self.freq1TextField)
        QWidget.setTabOrder(self.freq1TextField, self.freq2TextField)
        QWidget.setTabOrder(self.freq2TextField, self.filtOrderTextField)
        QWidget.setTabOrder(self.filtOrderTextField, self.fileSavingGroupBox)
        QWidget.setTabOrder(self.fileSavingGroupBox, self.browseOutDirButton)
        QWidget.setTabOrder(self.browseOutDirButton, self.fileNameTextField)
        QWidget.setTabOrder(self.fileNameTextField, self.plotGroupBox)
        QWidget.setTabOrder(self.plotGroupBox, self.renderLenTextField)
        QWidget.setTabOrder(self.renderLenTextField, self.chSpacingTextField)
        QWidget.setTabOrder(self.chSpacingTextField, self.rangeModeComboBox)
        QWidget.setTabOrder(self.rangeModeComboBox, self.minRangeTextField)
        QWidget.setTabOrder(self.minRangeTextField, self.maxRangeTextField)

        self.retranslateUi(AddSignalDialog)
        self.buttonBox.accepted.connect(AddSignalDialog.accept)
        self.buttonBox.rejected.connect(AddSignalDialog.reject)

        QMetaObject.connectSlotsByName(AddSignalDialog)
    # setupUi

    def retranslateUi(self, AddSignalDialog):
        AddSignalDialog.setWindowTitle(QCoreApplication.translate("AddSignalDialog", u"Add signal", None))
        self.label1.setText(QCoreApplication.translate("AddSignalDialog", u"Name:", None))
        self.sigNameLabel.setText("")
        self.label2.setText(QCoreApplication.translate("AddSignalDialog", u"Number of channels:", None))
        self.nChLabel.setText("")
        self.label3.setText(QCoreApplication.translate("AddSignalDialog", u"Sampling frequency (in sps):", None))
        self.freqLabel.setText("")
#if QT_CONFIG(tooltip)
        self.filteringGroupBox.setToolTip(QCoreApplication.translate("AddSignalDialog", u"Only for visualization, the raw signal will be saved to file", None))
#endif // QT_CONFIG(tooltip)
        self.filteringGroupBox.setTitle(QCoreApplication.translate("AddSignalDialog", u"Configure filtering", None))
        self.label4.setText(QCoreApplication.translate("AddSignalDialog", u"Type:", None))
        self.filtTypeComboBox.setItemText(0, QCoreApplication.translate("AddSignalDialog", u"highpass", None))
        self.filtTypeComboBox.setItemText(1, QCoreApplication.translate("AddSignalDialog", u"lowpass", None))
        self.filtTypeComboBox.setItemText(2, QCoreApplication.translate("AddSignalDialog", u"bandpass", None))
        self.filtTypeComboBox.setItemText(3, QCoreApplication.translate("AddSignalDialog", u"bandstop", None))

        self.label5.setText(QCoreApplication.translate("AddSignalDialog", u"First critical frequency (in sps):", None))
#if QT_CONFIG(tooltip)
        self.freq1TextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.freq1TextField.setPlaceholderText("")
        self.label6.setText(QCoreApplication.translate("AddSignalDialog", u"Second critical frequency (in sps):", None))
#if QT_CONFIG(tooltip)
        self.freq2TextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.freq2TextField.setPlaceholderText(QCoreApplication.translate("AddSignalDialog", u"For bandpass and bandstop only", None))
        self.label7.setText(QCoreApplication.translate("AddSignalDialog", u"Filter order:", None))
#if QT_CONFIG(tooltip)
        self.filtOrderTextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.filtOrderTextField.setPlaceholderText("")
        self.fileSavingGroupBox.setTitle(QCoreApplication.translate("AddSignalDialog", u"Configure file saving", None))
        self.label8.setText(QCoreApplication.translate("AddSignalDialog", u"Directory where the file will be saved:", None))
        self.browseOutDirButton.setText(QCoreApplication.translate("AddSignalDialog", u"Browse", None))
        self.label9.setText(QCoreApplication.translate("AddSignalDialog", u"Path to directory:", None))
        self.outDirPathLabel.setText("")
        self.label10.setText(QCoreApplication.translate("AddSignalDialog", u"File name:", None))
#if QT_CONFIG(tooltip)
        self.fileNameTextField.setToolTip(QCoreApplication.translate("AddSignalDialog", u"If empty, the signal name will be used", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.plotGroupBox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.plotGroupBox.setTitle(QCoreApplication.translate("AddSignalDialog", u"Configure plot", None))
        self.label11.setText(QCoreApplication.translate("AddSignalDialog", u"Render length (in s):", None))
        self.renderLenTextField.setText(QCoreApplication.translate("AddSignalDialog", u"4", None))
        self.label12.setText(QCoreApplication.translate("AddSignalDialog", u"Channel spacing (in a.u.):", None))
#if QT_CONFIG(tooltip)
        self.chSpacingTextField.setToolTip(QCoreApplication.translate("AddSignalDialog", u"Spacing between the channels in the signal unit (only for multi-channel signals)", None))
#endif // QT_CONFIG(tooltip)
        self.chSpacingTextField.setText(QCoreApplication.translate("AddSignalDialog", u"100", None))
        self.chSpacingTextField.setPlaceholderText("")
        self.label13.setText(QCoreApplication.translate("AddSignalDialog", u"Range mode:", None))
        self.rangeModeComboBox.setItemText(0, QCoreApplication.translate("AddSignalDialog", u"Automatic", None))
        self.rangeModeComboBox.setItemText(1, QCoreApplication.translate("AddSignalDialog", u"Manual", None))

        self.label14.setText(QCoreApplication.translate("AddSignalDialog", u"Minimum range (in a.u.):", None))
        self.label15.setText(QCoreApplication.translate("AddSignalDialog", u"Maximum range (in a.u.):", None))
    # retranslateUi

