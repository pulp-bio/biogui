# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'wulpus_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFormLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_WulpusConfigWidget(object):
    def setupUi(self, WulpusConfigWidget):
        if not WulpusConfigWidget.objectName():
            WulpusConfigWidget.setObjectName(u"WulpusConfigWidget")
        WulpusConfigWidget.resize(601, 700)
        self.mainVerticalLayout = QVBoxLayout(WulpusConfigWidget)
        self.mainVerticalLayout.setObjectName(u"mainVerticalLayout")
        self.groupBox = QGroupBox(WulpusConfigWidget)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.presetGroupBox = QGroupBox(self.groupBox)
        self.presetGroupBox.setObjectName(u"presetGroupBox")
        self.presetGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.presetHorizontalLayout = QHBoxLayout(self.presetGroupBox)
        self.presetHorizontalLayout.setObjectName(u"presetHorizontalLayout")
        self.presetLabel = QLabel(self.presetGroupBox)
        self.presetLabel.setObjectName(u"presetLabel")

        self.presetHorizontalLayout.addWidget(self.presetLabel)

        self.presetComboBox = QComboBox(self.presetGroupBox)
        self.presetComboBox.addItem("")
        self.presetComboBox.addItem("")
        self.presetComboBox.addItem("")
        self.presetComboBox.setObjectName(u"presetComboBox")

        self.presetHorizontalLayout.addWidget(self.presetComboBox)

        self.saveConfigButton = QPushButton(self.presetGroupBox)
        self.saveConfigButton.setObjectName(u"saveConfigButton")

        self.presetHorizontalLayout.addWidget(self.saveConfigButton)


        self.verticalLayout.addWidget(self.presetGroupBox)

        self.configTabWidget = QTabWidget(self.groupBox)
        self.configTabWidget.setObjectName(u"configTabWidget")
        self.basicTab = QWidget()
        self.basicTab.setObjectName(u"basicTab")
        self.basicFormLayout = QFormLayout(self.basicTab)
        self.basicFormLayout.setObjectName(u"basicFormLayout")
        self.dcdcTurnonLabel = QLabel(self.basicTab)
        self.dcdcTurnonLabel.setObjectName(u"dcdcTurnonLabel")

        self.basicFormLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.dcdcTurnonLabel)

        self.dcdcTurnonLineEdit = QLineEdit(self.basicTab)
        self.dcdcTurnonLineEdit.setObjectName(u"dcdcTurnonLineEdit")

        self.basicFormLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.dcdcTurnonLineEdit)

        self.measPeriodLabel = QLabel(self.basicTab)
        self.measPeriodLabel.setObjectName(u"measPeriodLabel")

        self.basicFormLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.measPeriodLabel)

        self.measPeriodLineEdit = QLineEdit(self.basicTab)
        self.measPeriodLineEdit.setObjectName(u"measPeriodLineEdit")

        self.basicFormLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.measPeriodLineEdit)

        self.transFreqLabel = QLabel(self.basicTab)
        self.transFreqLabel.setObjectName(u"transFreqLabel")

        self.basicFormLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.transFreqLabel)

        self.transFreqLineEdit = QLineEdit(self.basicTab)
        self.transFreqLineEdit.setObjectName(u"transFreqLineEdit")

        self.basicFormLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.transFreqLineEdit)

        self.pulseFreqLabel = QLabel(self.basicTab)
        self.pulseFreqLabel.setObjectName(u"pulseFreqLabel")

        self.basicFormLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.pulseFreqLabel)

        self.pulseFreqLineEdit = QLineEdit(self.basicTab)
        self.pulseFreqLineEdit.setObjectName(u"pulseFreqLineEdit")

        self.basicFormLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.pulseFreqLineEdit)

        self.numPulsesLabel = QLabel(self.basicTab)
        self.numPulsesLabel.setObjectName(u"numPulsesLabel")

        self.basicFormLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.numPulsesLabel)

        self.numPulsesLineEdit = QLineEdit(self.basicTab)
        self.numPulsesLineEdit.setObjectName(u"numPulsesLineEdit")

        self.basicFormLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.numPulsesLineEdit)

        self.samplingFreqLabel = QLabel(self.basicTab)
        self.samplingFreqLabel.setObjectName(u"samplingFreqLabel")

        self.basicFormLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.samplingFreqLabel)

        self.samplingFreqComboBox = QComboBox(self.basicTab)
        self.samplingFreqComboBox.setObjectName(u"samplingFreqComboBox")

        self.basicFormLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.samplingFreqComboBox)

        self.numSamplesLabel = QLabel(self.basicTab)
        self.numSamplesLabel.setObjectName(u"numSamplesLabel")

        self.basicFormLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.numSamplesLabel)

        self.numSamplesLineEdit = QLineEdit(self.basicTab)
        self.numSamplesLineEdit.setObjectName(u"numSamplesLineEdit")

        self.basicFormLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.numSamplesLineEdit)

        self.rxGainLabel = QLabel(self.basicTab)
        self.rxGainLabel.setObjectName(u"rxGainLabel")

        self.basicFormLayout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.rxGainLabel)

        self.rxGainComboBox = QComboBox(self.basicTab)
        self.rxGainComboBox.setObjectName(u"rxGainComboBox")

        self.basicFormLayout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.rxGainComboBox)

        self.configTabWidget.addTab(self.basicTab, "")
        self.advancedTab = QWidget()
        self.advancedTab.setObjectName(u"advancedTab")
        self.advancedFormLayout = QFormLayout(self.advancedTab)
        self.advancedFormLayout.setObjectName(u"advancedFormLayout")
        self.startHvmuxrxLabel = QLabel(self.advancedTab)
        self.startHvmuxrxLabel.setObjectName(u"startHvmuxrxLabel")

        self.advancedFormLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.startHvmuxrxLabel)

        self.startHvmuxrxLineEdit = QLineEdit(self.advancedTab)
        self.startHvmuxrxLineEdit.setObjectName(u"startHvmuxrxLineEdit")

        self.advancedFormLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.startHvmuxrxLineEdit)

        self.startPpgLabel = QLabel(self.advancedTab)
        self.startPpgLabel.setObjectName(u"startPpgLabel")

        self.advancedFormLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.startPpgLabel)

        self.startPpgLineEdit = QLineEdit(self.advancedTab)
        self.startPpgLineEdit.setObjectName(u"startPpgLineEdit")

        self.advancedFormLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.startPpgLineEdit)

        self.turnonAdcLabel = QLabel(self.advancedTab)
        self.turnonAdcLabel.setObjectName(u"turnonAdcLabel")

        self.advancedFormLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.turnonAdcLabel)

        self.turnonAdcLineEdit = QLineEdit(self.advancedTab)
        self.turnonAdcLineEdit.setObjectName(u"turnonAdcLineEdit")

        self.advancedFormLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.turnonAdcLineEdit)

        self.startPgainbiasLabel = QLabel(self.advancedTab)
        self.startPgainbiasLabel.setObjectName(u"startPgainbiasLabel")

        self.advancedFormLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.startPgainbiasLabel)

        self.startPgainbiasLineEdit = QLineEdit(self.advancedTab)
        self.startPgainbiasLineEdit.setObjectName(u"startPgainbiasLineEdit")

        self.advancedFormLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.startPgainbiasLineEdit)

        self.startAdcsampleLabel = QLabel(self.advancedTab)
        self.startAdcsampleLabel.setObjectName(u"startAdcsampleLabel")

        self.advancedFormLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.startAdcsampleLabel)

        self.startAdcsampleLineEdit = QLineEdit(self.advancedTab)
        self.startAdcsampleLineEdit.setObjectName(u"startAdcsampleLineEdit")

        self.advancedFormLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.startAdcsampleLineEdit)

        self.restartCaptLabel = QLabel(self.advancedTab)
        self.restartCaptLabel.setObjectName(u"restartCaptLabel")

        self.advancedFormLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.restartCaptLabel)

        self.restartCaptLineEdit = QLineEdit(self.advancedTab)
        self.restartCaptLineEdit.setObjectName(u"restartCaptLineEdit")

        self.advancedFormLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.restartCaptLineEdit)

        self.captTimeoutLabel = QLabel(self.advancedTab)
        self.captTimeoutLabel.setObjectName(u"captTimeoutLabel")

        self.advancedFormLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.captTimeoutLabel)

        self.captTimeoutLineEdit = QLineEdit(self.advancedTab)
        self.captTimeoutLineEdit.setObjectName(u"captTimeoutLineEdit")

        self.advancedFormLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.captTimeoutLineEdit)

        self.configTabWidget.addTab(self.advancedTab, "")
        self.txRxTab = QWidget()
        self.txRxTab.setObjectName(u"txRxTab")
        self.txRxVerticalLayout = QVBoxLayout(self.txRxTab)
        self.txRxVerticalLayout.setObjectName(u"txRxVerticalLayout")
        self.txRxInfoLabel = QLabel(self.txRxTab)
        self.txRxInfoLabel.setObjectName(u"txRxInfoLabel")
        self.txRxInfoLabel.setWordWrap(True)

        self.txRxVerticalLayout.addWidget(self.txRxInfoLabel)

        self.txRxButtonLayout = QHBoxLayout()
        self.txRxButtonLayout.setObjectName(u"txRxButtonLayout")
        self.addTxRxConfigButton = QPushButton(self.txRxTab)
        self.addTxRxConfigButton.setObjectName(u"addTxRxConfigButton")

        self.txRxButtonLayout.addWidget(self.addTxRxConfigButton)

        self.removeTxRxConfigButton = QPushButton(self.txRxTab)
        self.removeTxRxConfigButton.setObjectName(u"removeTxRxConfigButton")

        self.txRxButtonLayout.addWidget(self.removeTxRxConfigButton)

        self.clearTxRxConfigButton = QPushButton(self.txRxTab)
        self.clearTxRxConfigButton.setObjectName(u"clearTxRxConfigButton")

        self.txRxButtonLayout.addWidget(self.clearTxRxConfigButton)


        self.txRxVerticalLayout.addLayout(self.txRxButtonLayout)

        self.txRxTableWidget = QTableWidget(self.txRxTab)
        if (self.txRxTableWidget.columnCount() < 4):
            self.txRxTableWidget.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.txRxTableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.txRxTableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.txRxTableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.txRxTableWidget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.txRxTableWidget.setObjectName(u"txRxTableWidget")
        self.txRxTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.txRxTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.txRxVerticalLayout.addWidget(self.txRxTableWidget)

        self.configTabWidget.addTab(self.txRxTab, "")

        self.verticalLayout.addWidget(self.configTabWidget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.statusLabel = QLabel(self.groupBox)
        self.statusLabel.setObjectName(u"statusLabel")

        self.horizontalLayout.addWidget(self.statusLabel)

        self.applyConfigButton = QPushButton(self.groupBox)
        self.applyConfigButton.setObjectName(u"applyConfigButton")

        self.horizontalLayout.addWidget(self.applyConfigButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.mainVerticalLayout.addWidget(self.groupBox)


        self.retranslateUi(WulpusConfigWidget)

        self.configTabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(WulpusConfigWidget)
    # setupUi

    def retranslateUi(self, WulpusConfigWidget):
        WulpusConfigWidget.setWindowTitle(QCoreApplication.translate("WulpusConfigWidget", u"Wulpus Configuration", None))
        self.groupBox.setTitle(QCoreApplication.translate("WulpusConfigWidget", u"WULPUS Configuration", None))
        self.presetGroupBox.setTitle(QCoreApplication.translate("WulpusConfigWidget", u"Presets", None))
        self.presetLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"Configuration Preset:", None))
        self.presetComboBox.setItemText(0, QCoreApplication.translate("WulpusConfigWidget", u"Biceps Exercise", None))
        self.presetComboBox.setItemText(1, QCoreApplication.translate("WulpusConfigWidget", u"Waterbath", None))
        self.presetComboBox.setItemText(2, QCoreApplication.translate("WulpusConfigWidget", u"Custom", None))

#if QT_CONFIG(tooltip)
        self.presetComboBox.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Select a predefined configuration or create a custom one", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.saveConfigButton.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Save current configuration to a JSON file", None))
#endif // QT_CONFIG(tooltip)
        self.saveConfigButton.setText(QCoreApplication.translate("WulpusConfigWidget", u"Save to JSON", None))
#if QT_CONFIG(tooltip)
        self.dcdcTurnonLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Time for DC-DC converter to turn on (0-65535 \u00b5s)", None))
#endif // QT_CONFIG(tooltip)
        self.dcdcTurnonLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"DC-DC Turn On Time (\u00b5s):", None))
        self.dcdcTurnonLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"19530", None))
#if QT_CONFIG(tooltip)
        self.measPeriodLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Time between acquisitions (655-65535 \u00b5s)", None))
#endif // QT_CONFIG(tooltip)
        self.measPeriodLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"Measurement Period (\u00b5s):", None))
        self.measPeriodLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"25000", None))
#if QT_CONFIG(tooltip)
        self.transFreqLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Frequency of the transmitter (0-5000000 Hz)", None))
#endif // QT_CONFIG(tooltip)
        self.transFreqLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"Transmitter Frequency (Hz):", None))
        self.transFreqLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"2250000", None))
#if QT_CONFIG(tooltip)
        self.pulseFreqLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Frequency of pulses (0-5000000 Hz)", None))
#endif // QT_CONFIG(tooltip)
        self.pulseFreqLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"Pulse Frequency (Hz):", None))
        self.pulseFreqLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"2250000", None))
#if QT_CONFIG(tooltip)
        self.numPulsesLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Number of pulses per acquisition (0-30)", None))
#endif // QT_CONFIG(tooltip)
        self.numPulsesLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"Number of Pulses:", None))
        self.numPulsesLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"2", None))
#if QT_CONFIG(tooltip)
        self.samplingFreqLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"ADC sampling frequency", None))
#endif // QT_CONFIG(tooltip)
        self.samplingFreqLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"Sampling Frequency (Hz):", None))
#if QT_CONFIG(tooltip)
        self.samplingFreqComboBox.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Available sampling frequencies", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.numSamplesLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Number of samples per acquisition (0-800)", None))
#endif // QT_CONFIG(tooltip)
        self.numSamplesLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"Number of Samples:", None))
        self.numSamplesLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"400", None))
#if QT_CONFIG(tooltip)
        self.rxGainLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Receiver gain in decibels", None))
#endif // QT_CONFIG(tooltip)
        self.rxGainLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"RX Gain (dB):", None))
#if QT_CONFIG(tooltip)
        self.rxGainComboBox.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Available RX gain values", None))
#endif // QT_CONFIG(tooltip)
        self.configTabWidget.setTabText(self.configTabWidget.indexOf(self.basicTab), QCoreApplication.translate("WulpusConfigWidget", u"Basic Settings", None))
#if QT_CONFIG(tooltip)
        self.startHvmuxrxLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Start time for HV multiplexer RX (0-65535 \u00b5s)", None))
#endif // QT_CONFIG(tooltip)
        self.startHvmuxrxLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"HV-MUX RX Start Time (\u00b5s):", None))
        self.startHvmuxrxLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"498", None))
#if QT_CONFIG(tooltip)
        self.startPpgLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Programmable pulse generator start time (0-65535 \u00b5s)", None))
#endif // QT_CONFIG(tooltip)
        self.startPpgLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"PPG Start Time (\u00b5s):", None))
        self.startPpgLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"500", None))
#if QT_CONFIG(tooltip)
        self.turnonAdcLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"ADC turn on time (0-65535 \u00b5s)", None))
#endif // QT_CONFIG(tooltip)
        self.turnonAdcLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"ADC Turn On Time (\u00b5s):", None))
        self.turnonAdcLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"5", None))
#if QT_CONFIG(tooltip)
        self.startPgainbiasLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Programmable gain amplifier input bias start time (0-65535 \u00b5s)", None))
#endif // QT_CONFIG(tooltip)
        self.startPgainbiasLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"PGA In Bias Start Time (\u00b5s):", None))
        self.startPgainbiasLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"5", None))
#if QT_CONFIG(tooltip)
        self.startAdcsampleLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"ADC sampling start time (0-65535 \u00b5s)", None))
#endif // QT_CONFIG(tooltip)
        self.startAdcsampleLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"ADC Sampling Start Time (\u00b5s):", None))
        self.startAdcsampleLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"509", None))
#if QT_CONFIG(tooltip)
        self.restartCaptLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Time to restart capture (0-65535 \u00b5s)", None))
#endif // QT_CONFIG(tooltip)
        self.restartCaptLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"Capture Restart Time (\u00b5s):", None))
        self.restartCaptLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"3000", None))
#if QT_CONFIG(tooltip)
        self.captTimeoutLabel.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"Timeout for capture (0-65535 \u00b5s)", None))
#endif // QT_CONFIG(tooltip)
        self.captTimeoutLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"Capture Timeout (\u00b5s):", None))
        self.captTimeoutLineEdit.setText(QCoreApplication.translate("WulpusConfigWidget", u"3000", None))
        self.configTabWidget.setTabText(self.configTabWidget.indexOf(self.advancedTab), QCoreApplication.translate("WulpusConfigWidget", u"Advanced Timing", None))
        self.txRxInfoLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"Configure transmitter and receiver channels. Each configuration specifies which channels are active.", None))
        self.addTxRxConfigButton.setText(QCoreApplication.translate("WulpusConfigWidget", u"Add Config", None))
        self.removeTxRxConfigButton.setText(QCoreApplication.translate("WulpusConfigWidget", u"Remove Selected", None))
        self.clearTxRxConfigButton.setText(QCoreApplication.translate("WulpusConfigWidget", u"Clear All", None))
        ___qtablewidgetitem = self.txRxTableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("WulpusConfigWidget", u"#", None));
        ___qtablewidgetitem1 = self.txRxTableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("WulpusConfigWidget", u"TX Channels", None));
        ___qtablewidgetitem2 = self.txRxTableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("WulpusConfigWidget", u"RX Channels", None));
        ___qtablewidgetitem3 = self.txRxTableWidget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("WulpusConfigWidget", u"Optimized Switching", None));
#if QT_CONFIG(tooltip)
        self.txRxTableWidget.setToolTip(QCoreApplication.translate("WulpusConfigWidget", u"List of TX/RX channel configurations", None))
#endif // QT_CONFIG(tooltip)
        self.configTabWidget.setTabText(self.configTabWidget.indexOf(self.txRxTab), QCoreApplication.translate("WulpusConfigWidget", u"TX/RX Configuration", None))
        self.statusLabel.setText(QCoreApplication.translate("WulpusConfigWidget", u"Status: Ready", None))
        self.applyConfigButton.setText(QCoreApplication.translate("WulpusConfigWidget", u"Apply", None))
    # retranslateUi

