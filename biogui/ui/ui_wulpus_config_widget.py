# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'wulpus_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    QTime,
    QUrl,
    Qt,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class Ui_WulpusConfigWidget(object):
    def setupUi(self, WulpusConfigWidget):
        if not WulpusConfigWidget.objectName():
            WulpusConfigWidget.setObjectName("WulpusConfigWidget")
        WulpusConfigWidget.resize(601, 700)
        self.mainVerticalLayout = QVBoxLayout(WulpusConfigWidget)
        self.mainVerticalLayout.setObjectName("mainVerticalLayout")
        self.groupBox = QGroupBox(WulpusConfigWidget)
        self.groupBox.setObjectName("groupBox")
        self.groupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.presetGroupBox = QGroupBox(self.groupBox)
        self.presetGroupBox.setObjectName("presetGroupBox")
        self.presetGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.presetHorizontalLayout = QHBoxLayout(self.presetGroupBox)
        self.presetHorizontalLayout.setObjectName("presetHorizontalLayout")
        self.presetLabel = QLabel(self.presetGroupBox)
        self.presetLabel.setObjectName("presetLabel")

        self.presetHorizontalLayout.addWidget(self.presetLabel)

        self.presetComboBox = QComboBox(self.presetGroupBox)
        self.presetComboBox.addItem("")
        self.presetComboBox.addItem("")
        self.presetComboBox.addItem("")
        self.presetComboBox.setObjectName("presetComboBox")

        self.presetHorizontalLayout.addWidget(self.presetComboBox)

        self.saveConfigButton = QPushButton(self.presetGroupBox)
        self.saveConfigButton.setObjectName("saveConfigButton")

        self.presetHorizontalLayout.addWidget(self.saveConfigButton)

        self.verticalLayout.addWidget(self.presetGroupBox)

        self.configTabWidget = QTabWidget(self.groupBox)
        self.configTabWidget.setObjectName("configTabWidget")
        self.basicTab = QWidget()
        self.basicTab.setObjectName("basicTab")
        self.basicFormLayout = QFormLayout(self.basicTab)
        self.basicFormLayout.setObjectName("basicFormLayout")
        self.dcdcTurnonLabel = QLabel(self.basicTab)
        self.dcdcTurnonLabel.setObjectName("dcdcTurnonLabel")

        self.basicFormLayout.setWidget(
            0, QFormLayout.ItemRole.LabelRole, self.dcdcTurnonLabel
        )

        self.dcdcTurnonLineEdit = QLineEdit(self.basicTab)
        self.dcdcTurnonLineEdit.setObjectName("dcdcTurnonLineEdit")

        self.basicFormLayout.setWidget(
            0, QFormLayout.ItemRole.FieldRole, self.dcdcTurnonLineEdit
        )

        self.measPeriodLabel = QLabel(self.basicTab)
        self.measPeriodLabel.setObjectName("measPeriodLabel")

        self.basicFormLayout.setWidget(
            1, QFormLayout.ItemRole.LabelRole, self.measPeriodLabel
        )

        self.measPeriodLineEdit = QLineEdit(self.basicTab)
        self.measPeriodLineEdit.setObjectName("measPeriodLineEdit")

        self.basicFormLayout.setWidget(
            1, QFormLayout.ItemRole.FieldRole, self.measPeriodLineEdit
        )

        self.transFreqLabel = QLabel(self.basicTab)
        self.transFreqLabel.setObjectName("transFreqLabel")

        self.basicFormLayout.setWidget(
            2, QFormLayout.ItemRole.LabelRole, self.transFreqLabel
        )

        self.imuActiveCheckBox = QCheckBox(self.basicTab)
        self.imuActiveCheckBox.setObjectName("imuActiveCheckBox")

        self.basicFormLayout.setWidget(
            2, QFormLayout.ItemRole.FieldRole, self.imuActiveCheckBox
        )

        self.pulseFreqLabel = QLabel(self.basicTab)
        self.pulseFreqLabel.setObjectName("pulseFreqLabel")

        self.basicFormLayout.setWidget(
            3, QFormLayout.ItemRole.LabelRole, self.pulseFreqLabel
        )

        self.pulseFreqLineEdit = QLineEdit(self.basicTab)
        self.pulseFreqLineEdit.setObjectName("pulseFreqLineEdit")

        self.basicFormLayout.setWidget(
            3, QFormLayout.ItemRole.FieldRole, self.pulseFreqLineEdit
        )

        self.numPulsesLabel = QLabel(self.basicTab)
        self.numPulsesLabel.setObjectName("numPulsesLabel")

        self.basicFormLayout.setWidget(
            4, QFormLayout.ItemRole.LabelRole, self.numPulsesLabel
        )

        self.numPulsesLineEdit = QLineEdit(self.basicTab)
        self.numPulsesLineEdit.setObjectName("numPulsesLineEdit")

        self.basicFormLayout.setWidget(
            4, QFormLayout.ItemRole.FieldRole, self.numPulsesLineEdit
        )

        self.samplingFreqLabel = QLabel(self.basicTab)
        self.samplingFreqLabel.setObjectName("samplingFreqLabel")

        self.basicFormLayout.setWidget(
            5, QFormLayout.ItemRole.LabelRole, self.samplingFreqLabel
        )

        self.samplingFreqComboBox = QComboBox(self.basicTab)
        self.samplingFreqComboBox.setObjectName("samplingFreqComboBox")

        self.basicFormLayout.setWidget(
            5, QFormLayout.ItemRole.FieldRole, self.samplingFreqComboBox
        )

        self.numSamplesLabel = QLabel(self.basicTab)
        self.numSamplesLabel.setObjectName("numSamplesLabel")

        self.basicFormLayout.setWidget(
            6, QFormLayout.ItemRole.LabelRole, self.numSamplesLabel
        )

        self.numSamplesLineEdit = QLineEdit(self.basicTab)
        self.numSamplesLineEdit.setObjectName("numSamplesLineEdit")

        self.basicFormLayout.setWidget(
            6, QFormLayout.ItemRole.FieldRole, self.numSamplesLineEdit
        )

        self.rxGainLabel = QLabel(self.basicTab)
        self.rxGainLabel.setObjectName("rxGainLabel")

        self.basicFormLayout.setWidget(
            7, QFormLayout.ItemRole.LabelRole, self.rxGainLabel
        )

        self.rxGainComboBox = QComboBox(self.basicTab)
        self.rxGainComboBox.setObjectName("rxGainComboBox")

        self.basicFormLayout.setWidget(
            7, QFormLayout.ItemRole.FieldRole, self.rxGainComboBox
        )

        self.configTabWidget.addTab(self.basicTab, "")
        self.advancedTab = QWidget()
        self.advancedTab.setObjectName("advancedTab")
        self.advancedFormLayout = QFormLayout(self.advancedTab)
        self.advancedFormLayout.setObjectName("advancedFormLayout")
        self.startHvmuxrxLabel = QLabel(self.advancedTab)
        self.startHvmuxrxLabel.setObjectName("startHvmuxrxLabel")

        self.advancedFormLayout.setWidget(
            0, QFormLayout.ItemRole.LabelRole, self.startHvmuxrxLabel
        )

        self.startHvmuxrxLineEdit = QLineEdit(self.advancedTab)
        self.startHvmuxrxLineEdit.setObjectName("startHvmuxrxLineEdit")

        self.advancedFormLayout.setWidget(
            0, QFormLayout.ItemRole.FieldRole, self.startHvmuxrxLineEdit
        )

        self.startPpgLabel = QLabel(self.advancedTab)
        self.startPpgLabel.setObjectName("startPpgLabel")

        self.advancedFormLayout.setWidget(
            1, QFormLayout.ItemRole.LabelRole, self.startPpgLabel
        )

        self.startPpgLineEdit = QLineEdit(self.advancedTab)
        self.startPpgLineEdit.setObjectName("startPpgLineEdit")

        self.advancedFormLayout.setWidget(
            1, QFormLayout.ItemRole.FieldRole, self.startPpgLineEdit
        )

        self.turnonAdcLabel = QLabel(self.advancedTab)
        self.turnonAdcLabel.setObjectName("turnonAdcLabel")

        self.advancedFormLayout.setWidget(
            2, QFormLayout.ItemRole.LabelRole, self.turnonAdcLabel
        )

        self.turnonAdcLineEdit = QLineEdit(self.advancedTab)
        self.turnonAdcLineEdit.setObjectName("turnonAdcLineEdit")

        self.advancedFormLayout.setWidget(
            2, QFormLayout.ItemRole.FieldRole, self.turnonAdcLineEdit
        )

        self.startPgainbiasLabel = QLabel(self.advancedTab)
        self.startPgainbiasLabel.setObjectName("startPgainbiasLabel")

        self.advancedFormLayout.setWidget(
            3, QFormLayout.ItemRole.LabelRole, self.startPgainbiasLabel
        )

        self.startPgainbiasLineEdit = QLineEdit(self.advancedTab)
        self.startPgainbiasLineEdit.setObjectName("startPgainbiasLineEdit")

        self.advancedFormLayout.setWidget(
            3, QFormLayout.ItemRole.FieldRole, self.startPgainbiasLineEdit
        )

        self.startAdcsampleLabel = QLabel(self.advancedTab)
        self.startAdcsampleLabel.setObjectName("startAdcsampleLabel")

        self.advancedFormLayout.setWidget(
            4, QFormLayout.ItemRole.LabelRole, self.startAdcsampleLabel
        )

        self.startAdcsampleLineEdit = QLineEdit(self.advancedTab)
        self.startAdcsampleLineEdit.setObjectName("startAdcsampleLineEdit")

        self.advancedFormLayout.setWidget(
            4, QFormLayout.ItemRole.FieldRole, self.startAdcsampleLineEdit
        )

        self.restartCaptLabel = QLabel(self.advancedTab)
        self.restartCaptLabel.setObjectName("restartCaptLabel")

        self.advancedFormLayout.setWidget(
            5, QFormLayout.ItemRole.LabelRole, self.restartCaptLabel
        )

        self.restartCaptLineEdit = QLineEdit(self.advancedTab)
        self.restartCaptLineEdit.setObjectName("restartCaptLineEdit")

        self.advancedFormLayout.setWidget(
            5, QFormLayout.ItemRole.FieldRole, self.restartCaptLineEdit
        )

        self.captTimeoutLabel = QLabel(self.advancedTab)
        self.captTimeoutLabel.setObjectName("captTimeoutLabel")

        self.advancedFormLayout.setWidget(
            6, QFormLayout.ItemRole.LabelRole, self.captTimeoutLabel
        )

        self.captTimeoutLineEdit = QLineEdit(self.advancedTab)
        self.captTimeoutLineEdit.setObjectName("captTimeoutLineEdit")

        self.advancedFormLayout.setWidget(
            6, QFormLayout.ItemRole.FieldRole, self.captTimeoutLineEdit
        )

        self.configTabWidget.addTab(self.advancedTab, "")
        self.txRxTab = QWidget()
        self.txRxTab.setObjectName("txRxTab")
        self.txRxVerticalLayout = QVBoxLayout(self.txRxTab)
        self.txRxVerticalLayout.setObjectName("txRxVerticalLayout")
        self.txRxInfoLabel = QLabel(self.txRxTab)
        self.txRxInfoLabel.setObjectName("txRxInfoLabel")
        self.txRxInfoLabel.setWordWrap(True)

        self.txRxVerticalLayout.addWidget(self.txRxInfoLabel)

        self.txRxButtonLayout = QHBoxLayout()
        self.txRxButtonLayout.setObjectName("txRxButtonLayout")
        self.addTxRxConfigButton = QPushButton(self.txRxTab)
        self.addTxRxConfigButton.setObjectName("addTxRxConfigButton")

        self.txRxButtonLayout.addWidget(self.addTxRxConfigButton)

        self.removeTxRxConfigButton = QPushButton(self.txRxTab)
        self.removeTxRxConfigButton.setObjectName("removeTxRxConfigButton")

        self.txRxButtonLayout.addWidget(self.removeTxRxConfigButton)

        self.clearTxRxConfigButton = QPushButton(self.txRxTab)
        self.clearTxRxConfigButton.setObjectName("clearTxRxConfigButton")

        self.txRxButtonLayout.addWidget(self.clearTxRxConfigButton)

        self.txRxVerticalLayout.addLayout(self.txRxButtonLayout)

        self.txRxTableWidget = QTableWidget(self.txRxTab)
        if self.txRxTableWidget.columnCount() < 4:
            self.txRxTableWidget.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.txRxTableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.txRxTableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.txRxTableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.txRxTableWidget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.txRxTableWidget.setObjectName("txRxTableWidget")
        self.txRxTableWidget.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.txRxVerticalLayout.addWidget(self.txRxTableWidget)

        self.configTabWidget.addTab(self.txRxTab, "")

        self.verticalLayout.addWidget(self.configTabWidget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.statusLabel = QLabel(self.groupBox)
        self.statusLabel.setObjectName("statusLabel")

        self.horizontalLayout.addWidget(self.statusLabel)

        self.applyConfigButton = QPushButton(self.groupBox)
        self.applyConfigButton.setObjectName("applyConfigButton")

        self.horizontalLayout.addWidget(self.applyConfigButton)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.mainVerticalLayout.addWidget(self.groupBox)

        self.retranslateUi(WulpusConfigWidget)

        self.configTabWidget.setCurrentIndex(1)

        QMetaObject.connectSlotsByName(WulpusConfigWidget)

    # setupUi

    def retranslateUi(self, WulpusConfigWidget):
        WulpusConfigWidget.setWindowTitle(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Wulpus Configuration", None
            )
        )
        self.groupBox.setTitle(
            QCoreApplication.translate(
                "WulpusConfigWidget", "WULPUS Configuration", None
            )
        )
        self.presetGroupBox.setTitle(
            QCoreApplication.translate("WulpusConfigWidget", "Presets", None)
        )
        self.presetLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Configuration Preset:", None
            )
        )
        self.presetComboBox.setItemText(
            0, QCoreApplication.translate("WulpusConfigWidget", "Biceps Exercise", None)
        )
        self.presetComboBox.setItemText(
            1, QCoreApplication.translate("WulpusConfigWidget", "Waterbath", None)
        )
        self.presetComboBox.setItemText(
            2, QCoreApplication.translate("WulpusConfigWidget", "Custom", None)
        )

        # if QT_CONFIG(tooltip)
        self.presetComboBox.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget",
                "Select a predefined configuration or create a custom one",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(tooltip)
        self.saveConfigButton.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Save current configuration to a JSON file", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.saveConfigButton.setText(
            QCoreApplication.translate("WulpusConfigWidget", "Save to JSON", None)
        )
        # if QT_CONFIG(tooltip)
        self.dcdcTurnonLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget",
                "Time for DC-DC converter to turn on (0-65535 \u00b5s)",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.dcdcTurnonLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "DC-DC Turn On Time (\u00b5s):", None
            )
        )
        self.dcdcTurnonLineEdit.setText(
            QCoreApplication.translate("WulpusConfigWidget", "19530", None)
        )
        # if QT_CONFIG(tooltip)
        self.measPeriodLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget",
                "Time between acquisitions (655-65535 \u00b5s)",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.measPeriodLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Measurement Period (\u00b5s):", None
            )
        )
        self.measPeriodLineEdit.setText(
            QCoreApplication.translate("WulpusConfigWidget", "25000", None)
        )
        # if QT_CONFIG(tooltip)
        self.transFreqLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget",
                "Enable or disable accelerometer acquisition mode",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.transFreqLabel.setText(
            QCoreApplication.translate("WulpusConfigWidget", "IMU active:", None)
        )
        self.imuActiveCheckBox.setText("")
        # if QT_CONFIG(tooltip)
        self.pulseFreqLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Frequency of pulses (0-5000000 Hz)", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.pulseFreqLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Pulse Frequency (Hz):", None
            )
        )
        self.pulseFreqLineEdit.setText(
            QCoreApplication.translate("WulpusConfigWidget", "2250000", None)
        )
        # if QT_CONFIG(tooltip)
        self.numPulsesLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Number of pulses per acquisition (0-30)", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.numPulsesLabel.setText(
            QCoreApplication.translate("WulpusConfigWidget", "Number of Pulses:", None)
        )
        self.numPulsesLineEdit.setText(
            QCoreApplication.translate("WulpusConfigWidget", "2", None)
        )
        # if QT_CONFIG(tooltip)
        self.samplingFreqLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "ADC sampling frequency", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.samplingFreqLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Sampling Frequency (Hz):", None
            )
        )
        # if QT_CONFIG(tooltip)
        self.samplingFreqComboBox.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Available sampling frequencies", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(tooltip)
        self.numSamplesLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Number of samples per acquisition (0-800)", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.numSamplesLabel.setText(
            QCoreApplication.translate("WulpusConfigWidget", "Number of Samples:", None)
        )
        self.numSamplesLineEdit.setText(
            QCoreApplication.translate("WulpusConfigWidget", "400", None)
        )
        # if QT_CONFIG(tooltip)
        self.rxGainLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Receiver gain in decibels", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.rxGainLabel.setText(
            QCoreApplication.translate("WulpusConfigWidget", "RX Gain (dB):", None)
        )
        # if QT_CONFIG(tooltip)
        self.rxGainComboBox.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Available RX gain values", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.configTabWidget.setTabText(
            self.configTabWidget.indexOf(self.basicTab),
            QCoreApplication.translate("WulpusConfigWidget", "Basic Settings", None),
        )
        # if QT_CONFIG(tooltip)
        self.startHvmuxrxLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget",
                "Start time for HV multiplexer RX (0-65535 \u00b5s)",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.startHvmuxrxLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "HV-MUX RX Start Time (\u00b5s):", None
            )
        )
        self.startHvmuxrxLineEdit.setText(
            QCoreApplication.translate("WulpusConfigWidget", "498", None)
        )
        # if QT_CONFIG(tooltip)
        self.startPpgLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget",
                "Programmable pulse generator start time (0-65535 \u00b5s)",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.startPpgLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "PPG Start Time (\u00b5s):", None
            )
        )
        self.startPpgLineEdit.setText(
            QCoreApplication.translate("WulpusConfigWidget", "500", None)
        )
        # if QT_CONFIG(tooltip)
        self.turnonAdcLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "ADC turn on time (0-65535 \u00b5s)", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.turnonAdcLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "ADC Turn On Time (\u00b5s):", None
            )
        )
        self.turnonAdcLineEdit.setText(
            QCoreApplication.translate("WulpusConfigWidget", "5", None)
        )
        # if QT_CONFIG(tooltip)
        self.startPgainbiasLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget",
                "Programmable gain amplifier input bias start time (0-65535 \u00b5s)",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.startPgainbiasLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "PGA In Bias Start Time (\u00b5s):", None
            )
        )
        self.startPgainbiasLineEdit.setText(
            QCoreApplication.translate("WulpusConfigWidget", "5", None)
        )
        # if QT_CONFIG(tooltip)
        self.startAdcsampleLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "ADC sampling start time (0-65535 \u00b5s)", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.startAdcsampleLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "ADC Sampling Start Time (\u00b5s):", None
            )
        )
        self.startAdcsampleLineEdit.setText(
            QCoreApplication.translate("WulpusConfigWidget", "509", None)
        )
        # if QT_CONFIG(tooltip)
        self.restartCaptLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Time to restart capture (0-65535 \u00b5s)", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.restartCaptLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Capture Restart Time (\u00b5s):", None
            )
        )
        self.restartCaptLineEdit.setText(
            QCoreApplication.translate("WulpusConfigWidget", "3000", None)
        )
        # if QT_CONFIG(tooltip)
        self.captTimeoutLabel.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Timeout for capture (0-65535 \u00b5s)", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.captTimeoutLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Capture Timeout (\u00b5s):", None
            )
        )
        self.captTimeoutLineEdit.setText(
            QCoreApplication.translate("WulpusConfigWidget", "3000", None)
        )
        self.configTabWidget.setTabText(
            self.configTabWidget.indexOf(self.advancedTab),
            QCoreApplication.translate("WulpusConfigWidget", "Advanced Timing", None),
        )
        self.txRxInfoLabel.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget",
                "Configure transmitter and receiver channels. Each configuration specifies which channels are active.",
                None,
            )
        )
        self.addTxRxConfigButton.setText(
            QCoreApplication.translate("WulpusConfigWidget", "Add Config", None)
        )
        self.removeTxRxConfigButton.setText(
            QCoreApplication.translate("WulpusConfigWidget", "Remove Selected", None)
        )
        self.clearTxRxConfigButton.setText(
            QCoreApplication.translate("WulpusConfigWidget", "Clear All", None)
        )
        ___qtablewidgetitem = self.txRxTableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(
            QCoreApplication.translate("WulpusConfigWidget", "#", None)
        )
        ___qtablewidgetitem1 = self.txRxTableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(
            QCoreApplication.translate("WulpusConfigWidget", "TX Channels", None)
        )
        ___qtablewidgetitem2 = self.txRxTableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(
            QCoreApplication.translate("WulpusConfigWidget", "RX Channels", None)
        )
        ___qtablewidgetitem3 = self.txRxTableWidget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(
            QCoreApplication.translate(
                "WulpusConfigWidget", "Optimized Switching", None
            )
        )
        # if QT_CONFIG(tooltip)
        self.txRxTableWidget.setToolTip(
            QCoreApplication.translate(
                "WulpusConfigWidget", "List of TX/RX channel configurations", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.configTabWidget.setTabText(
            self.configTabWidget.indexOf(self.txRxTab),
            QCoreApplication.translate(
                "WulpusConfigWidget", "TX/RX Configuration", None
            ),
        )
        self.statusLabel.setText(
            QCoreApplication.translate("WulpusConfigWidget", "Status: Ready", None)
        )
        self.applyConfigButton.setText(
            QCoreApplication.translate("WulpusConfigWidget", "Apply", None)
        )

    # retranslateUi
