# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'signal_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QFrame,
    QGroupBox, QLabel, QLineEdit, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_SignalConfigWidget(object):
    def setupUi(self, SignalConfigWidget):
        if not SignalConfigWidget.objectName():
            SignalConfigWidget.setObjectName(u"SignalConfigWidget")
        SignalConfigWidget.resize(475, 559)
        self.verticalLayout = QVBoxLayout(SignalConfigWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout1 = QFormLayout()
        self.formLayout1.setObjectName(u"formLayout1")
        self.formLayout1.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.label1 = QLabel(SignalConfigWidget)
        self.label1.setObjectName(u"label1")

        self.formLayout1.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label1)

        self.sigNameLabel = QLabel(SignalConfigWidget)
        self.sigNameLabel.setObjectName(u"sigNameLabel")

        self.formLayout1.setWidget(0, QFormLayout.ItemRole.FieldRole, self.sigNameLabel)

        self.label2 = QLabel(SignalConfigWidget)
        self.label2.setObjectName(u"label2")

        self.formLayout1.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label2)

        self.nChLabel = QLabel(SignalConfigWidget)
        self.nChLabel.setObjectName(u"nChLabel")

        self.formLayout1.setWidget(1, QFormLayout.ItemRole.FieldRole, self.nChLabel)

        self.label3 = QLabel(SignalConfigWidget)
        self.label3.setObjectName(u"label3")

        self.formLayout1.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label3)

        self.freqLabel = QLabel(SignalConfigWidget)
        self.freqLabel.setObjectName(u"freqLabel")

        self.formLayout1.setWidget(2, QFormLayout.ItemRole.FieldRole, self.freqLabel)


        self.verticalLayout.addLayout(self.formLayout1)

        self.filterGroupBox = QGroupBox(SignalConfigWidget)
        self.filterGroupBox.setObjectName(u"filterGroupBox")
        self.filterGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filterGroupBox.setCheckable(True)
        self.filterGroupBox.setChecked(False)
        self.formLayout3 = QFormLayout(self.filterGroupBox)
        self.formLayout3.setObjectName(u"formLayout3")
        self.formLayout3.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.label4 = QLabel(self.filterGroupBox)
        self.label4.setObjectName(u"label4")
        self.label4.setFrameShape(QFrame.Shape.NoFrame)

        self.formLayout3.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label4)

        self.filtTypeComboBox = QComboBox(self.filterGroupBox)
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.setObjectName(u"filtTypeComboBox")

        self.formLayout3.setWidget(0, QFormLayout.ItemRole.FieldRole, self.filtTypeComboBox)

        self.label5 = QLabel(self.filterGroupBox)
        self.label5.setObjectName(u"label5")

        self.formLayout3.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label5)

        self.freq1TextField = QLineEdit(self.filterGroupBox)
        self.freq1TextField.setObjectName(u"freq1TextField")

        self.formLayout3.setWidget(1, QFormLayout.ItemRole.FieldRole, self.freq1TextField)

        self.label6 = QLabel(self.filterGroupBox)
        self.label6.setObjectName(u"label6")

        self.formLayout3.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label6)

        self.freq2TextField = QLineEdit(self.filterGroupBox)
        self.freq2TextField.setObjectName(u"freq2TextField")
        self.freq2TextField.setEnabled(False)

        self.formLayout3.setWidget(2, QFormLayout.ItemRole.FieldRole, self.freq2TextField)

        self.label7 = QLabel(self.filterGroupBox)
        self.label7.setObjectName(u"label7")

        self.formLayout3.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label7)

        self.filtOrderTextField = QLineEdit(self.filterGroupBox)
        self.filtOrderTextField.setObjectName(u"filtOrderTextField")

        self.formLayout3.setWidget(3, QFormLayout.ItemRole.FieldRole, self.filtOrderTextField)


        self.verticalLayout.addWidget(self.filterGroupBox)

        self.notchFilterGroupBox = QGroupBox(SignalConfigWidget)
        self.notchFilterGroupBox.setObjectName(u"notchFilterGroupBox")
        self.notchFilterGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.notchFilterGroupBox.setCheckable(True)
        self.notchFilterGroupBox.setChecked(False)
        self.formLayout4 = QFormLayout(self.notchFilterGroupBox)
        self.formLayout4.setObjectName(u"formLayout4")
        self.formLayout4.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.label8 = QLabel(self.notchFilterGroupBox)
        self.label8.setObjectName(u"label8")

        self.formLayout4.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label8)

        self.notchFreqComboBox = QComboBox(self.notchFilterGroupBox)
        self.notchFreqComboBox.addItem("")
        self.notchFreqComboBox.addItem("")
        self.notchFreqComboBox.setObjectName(u"notchFreqComboBox")

        self.formLayout4.setWidget(0, QFormLayout.ItemRole.FieldRole, self.notchFreqComboBox)

        self.label9 = QLabel(self.notchFilterGroupBox)
        self.label9.setObjectName(u"label9")

        self.formLayout4.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label9)

        self.qFactorTextField = QLineEdit(self.notchFilterGroupBox)
        self.qFactorTextField.setObjectName(u"qFactorTextField")

        self.formLayout4.setWidget(1, QFormLayout.ItemRole.FieldRole, self.qFactorTextField)


        self.verticalLayout.addWidget(self.notchFilterGroupBox)

        self.plotGroupBox = QGroupBox(SignalConfigWidget)
        self.plotGroupBox.setObjectName(u"plotGroupBox")
        self.plotGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plotGroupBox.setFlat(False)
        self.plotGroupBox.setCheckable(True)
        self.plotGroupBox.setChecked(True)
        self.formLayout = QFormLayout(self.plotGroupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.label10 = QLabel(self.plotGroupBox)
        self.label10.setObjectName(u"label10")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label10)

        self.label11 = QLabel(self.plotGroupBox)
        self.label11.setObjectName(u"label11")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label11)

        self.label12 = QLabel(self.plotGroupBox)
        self.label12.setObjectName(u"label12")
        self.label12.setEnabled(False)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label12)

        self.label13 = QLabel(self.plotGroupBox)
        self.label13.setObjectName(u"label13")
        self.label13.setEnabled(False)

        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.label13)

        self.chSpacingTextField = QLineEdit(self.plotGroupBox)
        self.chSpacingTextField.setObjectName(u"chSpacingTextField")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.chSpacingTextField)

        self.rangeModeComboBox = QComboBox(self.plotGroupBox)
        self.rangeModeComboBox.addItem("")
        self.rangeModeComboBox.addItem("")
        self.rangeModeComboBox.setObjectName(u"rangeModeComboBox")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.rangeModeComboBox)

        self.minRangeTextField = QLineEdit(self.plotGroupBox)
        self.minRangeTextField.setObjectName(u"minRangeTextField")
        self.minRangeTextField.setEnabled(False)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.minRangeTextField)

        self.maxRangeTextField = QLineEdit(self.plotGroupBox)
        self.maxRangeTextField.setObjectName(u"maxRangeTextField")
        self.maxRangeTextField.setEnabled(False)

        self.formLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.maxRangeTextField)


        self.verticalLayout.addWidget(self.plotGroupBox)

        QWidget.setTabOrder(self.filterGroupBox, self.filtTypeComboBox)
        QWidget.setTabOrder(self.filtTypeComboBox, self.freq1TextField)
        QWidget.setTabOrder(self.freq1TextField, self.freq2TextField)
        QWidget.setTabOrder(self.freq2TextField, self.filtOrderTextField)
        QWidget.setTabOrder(self.filtOrderTextField, self.notchFilterGroupBox)
        QWidget.setTabOrder(self.notchFilterGroupBox, self.notchFreqComboBox)
        QWidget.setTabOrder(self.notchFreqComboBox, self.qFactorTextField)
        QWidget.setTabOrder(self.qFactorTextField, self.plotGroupBox)
        QWidget.setTabOrder(self.plotGroupBox, self.chSpacingTextField)
        QWidget.setTabOrder(self.chSpacingTextField, self.rangeModeComboBox)
        QWidget.setTabOrder(self.rangeModeComboBox, self.minRangeTextField)
        QWidget.setTabOrder(self.minRangeTextField, self.maxRangeTextField)

        self.retranslateUi(SignalConfigWidget)

        QMetaObject.connectSlotsByName(SignalConfigWidget)
    # setupUi

    def retranslateUi(self, SignalConfigWidget):
        SignalConfigWidget.setWindowTitle(QCoreApplication.translate("SignalConfigWidget", u"Signal Configuration", None))
        self.label1.setText(QCoreApplication.translate("SignalConfigWidget", u"Name:", None))
        self.sigNameLabel.setText("")
        self.label2.setText(QCoreApplication.translate("SignalConfigWidget", u"Number of channels:", None))
        self.nChLabel.setText("")
        self.label3.setText(QCoreApplication.translate("SignalConfigWidget", u"Sampling rate (in sps):", None))
        self.freqLabel.setText("")
#if QT_CONFIG(tooltip)
        self.filterGroupBox.setToolTip(QCoreApplication.translate("SignalConfigWidget", u"Only for visualization, the raw signal will be saved to file", None))
#endif // QT_CONFIG(tooltip)
        self.filterGroupBox.setTitle(QCoreApplication.translate("SignalConfigWidget", u"Configure filtering", None))
        self.label4.setText(QCoreApplication.translate("SignalConfigWidget", u"Type:", None))
        self.filtTypeComboBox.setItemText(0, QCoreApplication.translate("SignalConfigWidget", u"highpass", None))
        self.filtTypeComboBox.setItemText(1, QCoreApplication.translate("SignalConfigWidget", u"lowpass", None))
        self.filtTypeComboBox.setItemText(2, QCoreApplication.translate("SignalConfigWidget", u"bandpass", None))
        self.filtTypeComboBox.setItemText(3, QCoreApplication.translate("SignalConfigWidget", u"bandstop", None))

        self.label5.setText(QCoreApplication.translate("SignalConfigWidget", u"First critical frequency (in Hz):", None))
#if QT_CONFIG(tooltip)
        self.freq1TextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.freq1TextField.setPlaceholderText("")
        self.label6.setText(QCoreApplication.translate("SignalConfigWidget", u"Second critical frequency (in Hz):", None))
#if QT_CONFIG(tooltip)
        self.freq2TextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.freq2TextField.setPlaceholderText(QCoreApplication.translate("SignalConfigWidget", u"For bandpass and bandstop only", None))
        self.label7.setText(QCoreApplication.translate("SignalConfigWidget", u"Filter order:", None))
#if QT_CONFIG(tooltip)
        self.filtOrderTextField.setToolTip(QCoreApplication.translate("SignalConfigWidget", u"Integer between 1 and 10", None))
#endif // QT_CONFIG(tooltip)
        self.filtOrderTextField.setText(QCoreApplication.translate("SignalConfigWidget", u"4", None))
        self.filtOrderTextField.setPlaceholderText("")
#if QT_CONFIG(tooltip)
        self.notchFilterGroupBox.setToolTip(QCoreApplication.translate("SignalConfigWidget", u"Only for visualization, the raw signal will be saved to file", None))
#endif // QT_CONFIG(tooltip)
        self.notchFilterGroupBox.setTitle(QCoreApplication.translate("SignalConfigWidget", u"Filter powerline noise", None))
        self.label8.setText(QCoreApplication.translate("SignalConfigWidget", u"Frequency (Hz):", None))
        self.notchFreqComboBox.setItemText(0, QCoreApplication.translate("SignalConfigWidget", u"50", None))
        self.notchFreqComboBox.setItemText(1, QCoreApplication.translate("SignalConfigWidget", u"60", None))

        self.label9.setText(QCoreApplication.translate("SignalConfigWidget", u"Quality factor:", None))
#if QT_CONFIG(tooltip)
        self.qFactorTextField.setToolTip(QCoreApplication.translate("SignalConfigWidget", u"Integer between 10 and 50", None))
#endif // QT_CONFIG(tooltip)
        self.qFactorTextField.setText(QCoreApplication.translate("SignalConfigWidget", u"30", None))
#if QT_CONFIG(tooltip)
        self.plotGroupBox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.plotGroupBox.setTitle(QCoreApplication.translate("SignalConfigWidget", u"Show plot", None))
        self.label10.setText(QCoreApplication.translate("SignalConfigWidget", u"Channel spacing (in a.u.):", None))
        self.label11.setText(QCoreApplication.translate("SignalConfigWidget", u"Range mode:", None))
        self.label12.setText(QCoreApplication.translate("SignalConfigWidget", u"Minimum range (in a.u.):", None))
        self.label13.setText(QCoreApplication.translate("SignalConfigWidget", u"Maximum range (in a.u.):", None))
#if QT_CONFIG(tooltip)
        self.chSpacingTextField.setToolTip(QCoreApplication.translate("SignalConfigWidget", u"Spacing between the channels in the signal unit (only for multi-channel signals)", None))
#endif // QT_CONFIG(tooltip)
        self.chSpacingTextField.setText(QCoreApplication.translate("SignalConfigWidget", u"0", None))
        self.chSpacingTextField.setPlaceholderText("")
        self.rangeModeComboBox.setItemText(0, QCoreApplication.translate("SignalConfigWidget", u"Automatic", None))
        self.rangeModeComboBox.setItemText(1, QCoreApplication.translate("SignalConfigWidget", u"Manual", None))

    # retranslateUi

