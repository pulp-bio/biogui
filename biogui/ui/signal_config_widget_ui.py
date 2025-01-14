# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'signal_config_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QFrame, QGroupBox, QLabel, QLineEdit,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_SignalConfigWidget(object):
    def setupUi(self, SignalConfigWidget):
        if not SignalConfigWidget.objectName():
            SignalConfigWidget.setObjectName(u"SignalConfigWidget")
        SignalConfigWidget.resize(500, 622)
        self.verticalLayout = QVBoxLayout(SignalConfigWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout1 = QFormLayout()
        self.formLayout1.setObjectName(u"formLayout1")
        self.formLayout1.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.label1 = QLabel(SignalConfigWidget)
        self.label1.setObjectName(u"label1")

        self.formLayout1.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.sigNameLabel = QLabel(SignalConfigWidget)
        self.sigNameLabel.setObjectName(u"sigNameLabel")

        self.formLayout1.setWidget(0, QFormLayout.FieldRole, self.sigNameLabel)

        self.label2 = QLabel(SignalConfigWidget)
        self.label2.setObjectName(u"label2")

        self.formLayout1.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.nChLabel = QLabel(SignalConfigWidget)
        self.nChLabel.setObjectName(u"nChLabel")

        self.formLayout1.setWidget(1, QFormLayout.FieldRole, self.nChLabel)

        self.label3 = QLabel(SignalConfigWidget)
        self.label3.setObjectName(u"label3")

        self.formLayout1.setWidget(2, QFormLayout.LabelRole, self.label3)

        self.freqLabel = QLabel(SignalConfigWidget)
        self.freqLabel.setObjectName(u"freqLabel")

        self.formLayout1.setWidget(2, QFormLayout.FieldRole, self.freqLabel)


        self.verticalLayout.addLayout(self.formLayout1)

        self.plotGroupBox = QGroupBox(SignalConfigWidget)
        self.plotGroupBox.setObjectName(u"plotGroupBox")
        self.plotGroupBox.setAlignment(Qt.AlignCenter)
        self.plotGroupBox.setFlat(True)
        self.plotGroupBox.setCheckable(True)
        self.plotGroupBox.setChecked(True)
        self.verticalLayout_2 = QVBoxLayout(self.plotGroupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.label4 = QLabel(self.plotGroupBox)
        self.label4.setObjectName(u"label4")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label4)

        self.chSpacingTextField = QLineEdit(self.plotGroupBox)
        self.chSpacingTextField.setObjectName(u"chSpacingTextField")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.chSpacingTextField)

        self.showYAxisCheckBox = QCheckBox(self.plotGroupBox)
        self.showYAxisCheckBox.setObjectName(u"showYAxisCheckBox")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.showYAxisCheckBox)

        self.rangeModeComboBox = QComboBox(self.plotGroupBox)
        self.rangeModeComboBox.addItem("")
        self.rangeModeComboBox.addItem("")
        self.rangeModeComboBox.setObjectName(u"rangeModeComboBox")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.rangeModeComboBox)

        self.label5 = QLabel(self.plotGroupBox)
        self.label5.setObjectName(u"label5")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label5)

        self.label6 = QLabel(self.plotGroupBox)
        self.label6.setObjectName(u"label6")
        self.label6.setEnabled(False)

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label6)

        self.minRangeTextField = QLineEdit(self.plotGroupBox)
        self.minRangeTextField.setObjectName(u"minRangeTextField")
        self.minRangeTextField.setEnabled(False)

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.minRangeTextField)

        self.label7 = QLabel(self.plotGroupBox)
        self.label7.setObjectName(u"label7")
        self.label7.setEnabled(False)

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label7)

        self.maxRangeTextField = QLineEdit(self.plotGroupBox)
        self.maxRangeTextField.setObjectName(u"maxRangeTextField")
        self.maxRangeTextField.setEnabled(False)

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.maxRangeTextField)


        self.verticalLayout_2.addLayout(self.formLayout)

        self.filterGroupBox = QGroupBox(self.plotGroupBox)
        self.filterGroupBox.setObjectName(u"filterGroupBox")
        self.filterGroupBox.setAlignment(Qt.AlignCenter)
        self.filterGroupBox.setCheckable(True)
        self.filterGroupBox.setChecked(False)
        self.formLayout_3 = QFormLayout(self.filterGroupBox)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.label8 = QLabel(self.filterGroupBox)
        self.label8.setObjectName(u"label8")
        self.label8.setFrameShape(QFrame.NoFrame)

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label8)

        self.filtTypeComboBox = QComboBox(self.filterGroupBox)
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.setObjectName(u"filtTypeComboBox")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.filtTypeComboBox)

        self.label9 = QLabel(self.filterGroupBox)
        self.label9.setObjectName(u"label9")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label9)

        self.freq1TextField = QLineEdit(self.filterGroupBox)
        self.freq1TextField.setObjectName(u"freq1TextField")

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.freq1TextField)

        self.label10 = QLabel(self.filterGroupBox)
        self.label10.setObjectName(u"label10")

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.label10)

        self.freq2TextField = QLineEdit(self.filterGroupBox)
        self.freq2TextField.setObjectName(u"freq2TextField")
        self.freq2TextField.setEnabled(False)

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.freq2TextField)

        self.label11 = QLabel(self.filterGroupBox)
        self.label11.setObjectName(u"label11")

        self.formLayout_3.setWidget(3, QFormLayout.LabelRole, self.label11)

        self.filtOrderTextField = QLineEdit(self.filterGroupBox)
        self.filtOrderTextField.setObjectName(u"filtOrderTextField")

        self.formLayout_3.setWidget(3, QFormLayout.FieldRole, self.filtOrderTextField)


        self.verticalLayout_2.addWidget(self.filterGroupBox)

        self.notchFilterGroupBox = QGroupBox(self.plotGroupBox)
        self.notchFilterGroupBox.setObjectName(u"notchFilterGroupBox")
        self.notchFilterGroupBox.setCheckable(True)
        self.notchFilterGroupBox.setChecked(False)
        self.formLayout2 = QFormLayout(self.notchFilterGroupBox)
        self.formLayout2.setObjectName(u"formLayout2")
        self.formLayout2.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.label12 = QLabel(self.notchFilterGroupBox)
        self.label12.setObjectName(u"label12")

        self.formLayout2.setWidget(0, QFormLayout.LabelRole, self.label12)

        self.notchFreqComboBox = QComboBox(self.notchFilterGroupBox)
        self.notchFreqComboBox.addItem("")
        self.notchFreqComboBox.addItem("")
        self.notchFreqComboBox.setObjectName(u"notchFreqComboBox")

        self.formLayout2.setWidget(0, QFormLayout.FieldRole, self.notchFreqComboBox)

        self.label13 = QLabel(self.notchFilterGroupBox)
        self.label13.setObjectName(u"label13")

        self.formLayout2.setWidget(1, QFormLayout.LabelRole, self.label13)

        self.qFactorTextField = QLineEdit(self.notchFilterGroupBox)
        self.qFactorTextField.setObjectName(u"qFactorTextField")

        self.formLayout2.setWidget(1, QFormLayout.FieldRole, self.qFactorTextField)


        self.verticalLayout_2.addWidget(self.notchFilterGroupBox)

        self.verticalLayout_2.setStretch(0, 1)

        self.verticalLayout.addWidget(self.plotGroupBox)

        QWidget.setTabOrder(self.notchFreqComboBox, self.qFactorTextField)

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
        self.plotGroupBox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.plotGroupBox.setTitle(QCoreApplication.translate("SignalConfigWidget", u"Show plot", None))
        self.label4.setText(QCoreApplication.translate("SignalConfigWidget", u"Channel spacing (in a.u.):", None))
#if QT_CONFIG(tooltip)
        self.chSpacingTextField.setToolTip(QCoreApplication.translate("SignalConfigWidget", u"Spacing between the channels in the signal unit (only for multi-channel signals)", None))
#endif // QT_CONFIG(tooltip)
        self.chSpacingTextField.setText(QCoreApplication.translate("SignalConfigWidget", u"0", None))
        self.chSpacingTextField.setPlaceholderText("")
        self.showYAxisCheckBox.setText(QCoreApplication.translate("SignalConfigWidget", u"Show Y axis", None))
        self.rangeModeComboBox.setItemText(0, QCoreApplication.translate("SignalConfigWidget", u"Automatic", None))
        self.rangeModeComboBox.setItemText(1, QCoreApplication.translate("SignalConfigWidget", u"Manual", None))

        self.label5.setText(QCoreApplication.translate("SignalConfigWidget", u"Range mode:", None))
        self.label6.setText(QCoreApplication.translate("SignalConfigWidget", u"Minimum range (in a.u.):", None))
        self.label7.setText(QCoreApplication.translate("SignalConfigWidget", u"Maximum range (in a.u.):", None))
#if QT_CONFIG(tooltip)
        self.filterGroupBox.setToolTip(QCoreApplication.translate("SignalConfigWidget", u"Only for visualization, the raw signal will be saved to file", None))
#endif // QT_CONFIG(tooltip)
        self.filterGroupBox.setTitle(QCoreApplication.translate("SignalConfigWidget", u"Configure filtering", None))
        self.label8.setText(QCoreApplication.translate("SignalConfigWidget", u"Type:", None))
        self.filtTypeComboBox.setItemText(0, QCoreApplication.translate("SignalConfigWidget", u"highpass", None))
        self.filtTypeComboBox.setItemText(1, QCoreApplication.translate("SignalConfigWidget", u"lowpass", None))
        self.filtTypeComboBox.setItemText(2, QCoreApplication.translate("SignalConfigWidget", u"bandpass", None))
        self.filtTypeComboBox.setItemText(3, QCoreApplication.translate("SignalConfigWidget", u"bandstop", None))

        self.label9.setText(QCoreApplication.translate("SignalConfigWidget", u"First critical frequency (in Hz):", None))
#if QT_CONFIG(tooltip)
        self.freq1TextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.freq1TextField.setPlaceholderText("")
        self.label10.setText(QCoreApplication.translate("SignalConfigWidget", u"Second critical frequency (in Hz):", None))
#if QT_CONFIG(tooltip)
        self.freq2TextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.freq2TextField.setPlaceholderText(QCoreApplication.translate("SignalConfigWidget", u"For bandpass and bandstop only", None))
        self.label11.setText(QCoreApplication.translate("SignalConfigWidget", u"Filter order:", None))
#if QT_CONFIG(tooltip)
        self.filtOrderTextField.setToolTip(QCoreApplication.translate("SignalConfigWidget", u"Integer between 1 and 10", None))
#endif // QT_CONFIG(tooltip)
        self.filtOrderTextField.setText(QCoreApplication.translate("SignalConfigWidget", u"4", None))
        self.filtOrderTextField.setPlaceholderText("")
#if QT_CONFIG(tooltip)
        self.notchFilterGroupBox.setToolTip(QCoreApplication.translate("SignalConfigWidget", u"Only for visualization, the raw signal will be saved to file", None))
#endif // QT_CONFIG(tooltip)
        self.notchFilterGroupBox.setTitle(QCoreApplication.translate("SignalConfigWidget", u"Filter powerline noise", None))
        self.label12.setText(QCoreApplication.translate("SignalConfigWidget", u"Frequency (Hz):", None))
        self.notchFreqComboBox.setItemText(0, QCoreApplication.translate("SignalConfigWidget", u"50", None))
        self.notchFreqComboBox.setItemText(1, QCoreApplication.translate("SignalConfigWidget", u"60", None))

        self.label13.setText(QCoreApplication.translate("SignalConfigWidget", u"Quality factor:", None))
#if QT_CONFIG(tooltip)
        self.qFactorTextField.setToolTip(QCoreApplication.translate("SignalConfigWidget", u"Integer between 10 and 50", None))
#endif // QT_CONFIG(tooltip)
        self.qFactorTextField.setText(QCoreApplication.translate("SignalConfigWidget", u"30", None))
    # retranslateUi

