# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'signal_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
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
    Qt,
    QTime,
    QUrl,
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
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Ui_SignalConfigWidget(object):
    def setupUi(self, SignalConfigWidget):
        if not SignalConfigWidget.objectName():
            SignalConfigWidget.setObjectName("SignalConfigWidget")
        SignalConfigWidget.resize(400, 500)
        self.verticalLayout = QVBoxLayout(SignalConfigWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout1 = QFormLayout()
        self.formLayout1.setObjectName("formLayout1")
        self.label1 = QLabel(SignalConfigWidget)
        self.label1.setObjectName("label1")

        self.formLayout1.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.sigNameLabel = QLabel(SignalConfigWidget)
        self.sigNameLabel.setObjectName("sigNameLabel")

        self.formLayout1.setWidget(0, QFormLayout.FieldRole, self.sigNameLabel)

        self.label2 = QLabel(SignalConfigWidget)
        self.label2.setObjectName("label2")

        self.formLayout1.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.nChLabel = QLabel(SignalConfigWidget)
        self.nChLabel.setObjectName("nChLabel")

        self.formLayout1.setWidget(1, QFormLayout.FieldRole, self.nChLabel)

        self.label3 = QLabel(SignalConfigWidget)
        self.label3.setObjectName("label3")

        self.formLayout1.setWidget(2, QFormLayout.LabelRole, self.label3)

        self.freqLabel = QLabel(SignalConfigWidget)
        self.freqLabel.setObjectName("freqLabel")

        self.formLayout1.setWidget(2, QFormLayout.FieldRole, self.freqLabel)

        self.verticalLayout.addLayout(self.formLayout1)

        self.filteringGroupBox = QGroupBox(SignalConfigWidget)
        self.filteringGroupBox.setObjectName("filteringGroupBox")
        self.filteringGroupBox.setAlignment(Qt.AlignCenter)
        self.filteringGroupBox.setCheckable(True)
        self.filteringGroupBox.setChecked(False)
        self.formLayout2 = QFormLayout(self.filteringGroupBox)
        self.formLayout2.setObjectName("formLayout2")
        self.label4 = QLabel(self.filteringGroupBox)
        self.label4.setObjectName("label4")
        self.label4.setFrameShape(QFrame.NoFrame)

        self.formLayout2.setWidget(0, QFormLayout.LabelRole, self.label4)

        self.filtTypeComboBox = QComboBox(self.filteringGroupBox)
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.addItem("")
        self.filtTypeComboBox.setObjectName("filtTypeComboBox")

        self.formLayout2.setWidget(0, QFormLayout.FieldRole, self.filtTypeComboBox)

        self.label5 = QLabel(self.filteringGroupBox)
        self.label5.setObjectName("label5")

        self.formLayout2.setWidget(1, QFormLayout.LabelRole, self.label5)

        self.freq1TextField = QLineEdit(self.filteringGroupBox)
        self.freq1TextField.setObjectName("freq1TextField")

        self.formLayout2.setWidget(1, QFormLayout.FieldRole, self.freq1TextField)

        self.label6 = QLabel(self.filteringGroupBox)
        self.label6.setObjectName("label6")

        self.formLayout2.setWidget(2, QFormLayout.LabelRole, self.label6)

        self.freq2TextField = QLineEdit(self.filteringGroupBox)
        self.freq2TextField.setObjectName("freq2TextField")
        self.freq2TextField.setEnabled(False)

        self.formLayout2.setWidget(2, QFormLayout.FieldRole, self.freq2TextField)

        self.label7 = QLabel(self.filteringGroupBox)
        self.label7.setObjectName("label7")

        self.formLayout2.setWidget(3, QFormLayout.LabelRole, self.label7)

        self.filtOrderTextField = QLineEdit(self.filteringGroupBox)
        self.filtOrderTextField.setObjectName("filtOrderTextField")

        self.formLayout2.setWidget(3, QFormLayout.FieldRole, self.filtOrderTextField)

        self.verticalLayout.addWidget(self.filteringGroupBox)

        self.plotGroupBox = QGroupBox(SignalConfigWidget)
        self.plotGroupBox.setObjectName("plotGroupBox")
        self.plotGroupBox.setAlignment(Qt.AlignCenter)
        self.plotGroupBox.setFlat(False)
        self.plotGroupBox.setCheckable(True)
        self.plotGroupBox.setChecked(True)
        self.formLayout4 = QFormLayout(self.plotGroupBox)
        self.formLayout4.setObjectName("formLayout4")
        self.label8 = QLabel(self.plotGroupBox)
        self.label8.setObjectName("label8")

        self.formLayout4.setWidget(0, QFormLayout.LabelRole, self.label8)

        self.chSpacingTextField = QLineEdit(self.plotGroupBox)
        self.chSpacingTextField.setObjectName("chSpacingTextField")

        self.formLayout4.setWidget(0, QFormLayout.FieldRole, self.chSpacingTextField)

        self.showYAxisCheckBox = QCheckBox(self.plotGroupBox)
        self.showYAxisCheckBox.setObjectName("showYAxisCheckBox")

        self.formLayout4.setWidget(1, QFormLayout.FieldRole, self.showYAxisCheckBox)

        self.label9 = QLabel(self.plotGroupBox)
        self.label9.setObjectName("label9")

        self.formLayout4.setWidget(2, QFormLayout.LabelRole, self.label9)

        self.rangeModeComboBox = QComboBox(self.plotGroupBox)
        self.rangeModeComboBox.addItem("")
        self.rangeModeComboBox.addItem("")
        self.rangeModeComboBox.setObjectName("rangeModeComboBox")

        self.formLayout4.setWidget(2, QFormLayout.FieldRole, self.rangeModeComboBox)

        self.label10 = QLabel(self.plotGroupBox)
        self.label10.setObjectName("label10")
        self.label10.setEnabled(False)

        self.formLayout4.setWidget(3, QFormLayout.LabelRole, self.label10)

        self.minRangeTextField = QLineEdit(self.plotGroupBox)
        self.minRangeTextField.setObjectName("minRangeTextField")
        self.minRangeTextField.setEnabled(False)

        self.formLayout4.setWidget(3, QFormLayout.FieldRole, self.minRangeTextField)

        self.label11 = QLabel(self.plotGroupBox)
        self.label11.setObjectName("label11")
        self.label11.setEnabled(False)

        self.formLayout4.setWidget(4, QFormLayout.LabelRole, self.label11)

        self.maxRangeTextField = QLineEdit(self.plotGroupBox)
        self.maxRangeTextField.setObjectName("maxRangeTextField")
        self.maxRangeTextField.setEnabled(False)

        self.formLayout4.setWidget(4, QFormLayout.FieldRole, self.maxRangeTextField)

        self.verticalLayout.addWidget(self.plotGroupBox)

        QWidget.setTabOrder(self.filteringGroupBox, self.filtTypeComboBox)
        QWidget.setTabOrder(self.filtTypeComboBox, self.freq1TextField)
        QWidget.setTabOrder(self.freq1TextField, self.freq2TextField)
        QWidget.setTabOrder(self.freq2TextField, self.filtOrderTextField)
        QWidget.setTabOrder(self.filtOrderTextField, self.plotGroupBox)
        QWidget.setTabOrder(self.plotGroupBox, self.chSpacingTextField)
        QWidget.setTabOrder(self.chSpacingTextField, self.showYAxisCheckBox)
        QWidget.setTabOrder(self.showYAxisCheckBox, self.rangeModeComboBox)
        QWidget.setTabOrder(self.rangeModeComboBox, self.minRangeTextField)
        QWidget.setTabOrder(self.minRangeTextField, self.maxRangeTextField)

        self.retranslateUi(SignalConfigWidget)

        QMetaObject.connectSlotsByName(SignalConfigWidget)

    # setupUi

    def retranslateUi(self, SignalConfigWidget):
        SignalConfigWidget.setWindowTitle(
            QCoreApplication.translate(
                "SignalConfigWidget", "Signal Configuration", None
            )
        )
        self.label1.setText(
            QCoreApplication.translate("SignalConfigWidget", "Name:", None)
        )
        self.sigNameLabel.setText("")
        self.label2.setText(
            QCoreApplication.translate(
                "SignalConfigWidget", "Number of channels:", None
            )
        )
        self.nChLabel.setText("")
        self.label3.setText(
            QCoreApplication.translate(
                "SignalConfigWidget", "Sampling frequency (in sps):", None
            )
        )
        self.freqLabel.setText("")
        # if QT_CONFIG(tooltip)
        self.filteringGroupBox.setToolTip(
            QCoreApplication.translate(
                "SignalConfigWidget",
                "Only for visualization, the raw signal will be saved to file",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.filteringGroupBox.setTitle(
            QCoreApplication.translate(
                "SignalConfigWidget", "Configure filtering", None
            )
        )
        self.label4.setText(
            QCoreApplication.translate("SignalConfigWidget", "Type:", None)
        )
        self.filtTypeComboBox.setItemText(
            0, QCoreApplication.translate("SignalConfigWidget", "highpass", None)
        )
        self.filtTypeComboBox.setItemText(
            1, QCoreApplication.translate("SignalConfigWidget", "lowpass", None)
        )
        self.filtTypeComboBox.setItemText(
            2, QCoreApplication.translate("SignalConfigWidget", "bandpass", None)
        )
        self.filtTypeComboBox.setItemText(
            3, QCoreApplication.translate("SignalConfigWidget", "bandstop", None)
        )

        self.label5.setText(
            QCoreApplication.translate(
                "SignalConfigWidget", "First critical frequency (in sps):", None
            )
        )
        # if QT_CONFIG(tooltip)
        self.freq1TextField.setToolTip("")
        # endif // QT_CONFIG(tooltip)
        self.freq1TextField.setPlaceholderText("")
        self.label6.setText(
            QCoreApplication.translate(
                "SignalConfigWidget", "Second critical frequency (in sps):", None
            )
        )
        # if QT_CONFIG(tooltip)
        self.freq2TextField.setToolTip("")
        # endif // QT_CONFIG(tooltip)
        self.freq2TextField.setPlaceholderText(
            QCoreApplication.translate(
                "SignalConfigWidget", "For bandpass and bandstop only", None
            )
        )
        self.label7.setText(
            QCoreApplication.translate("SignalConfigWidget", "Filter order:", None)
        )
        # if QT_CONFIG(tooltip)
        self.filtOrderTextField.setToolTip("")
        # endif // QT_CONFIG(tooltip)
        self.filtOrderTextField.setPlaceholderText("")
        # if QT_CONFIG(tooltip)
        self.plotGroupBox.setToolTip("")
        # endif // QT_CONFIG(tooltip)
        self.plotGroupBox.setTitle(
            QCoreApplication.translate("SignalConfigWidget", "Configure plot", None)
        )
        self.label8.setText(
            QCoreApplication.translate(
                "SignalConfigWidget", "Channel spacing (in a.u.):", None
            )
        )
        # if QT_CONFIG(tooltip)
        self.chSpacingTextField.setToolTip(
            QCoreApplication.translate(
                "SignalConfigWidget",
                "Spacing between the channels in the signal unit (only for multi-channel signals)",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.chSpacingTextField.setText(
            QCoreApplication.translate("SignalConfigWidget", "0", None)
        )
        self.chSpacingTextField.setPlaceholderText("")
        self.showYAxisCheckBox.setText(
            QCoreApplication.translate("SignalConfigWidget", "Show Y axis", None)
        )
        self.label9.setText(
            QCoreApplication.translate("SignalConfigWidget", "Range mode:", None)
        )
        self.rangeModeComboBox.setItemText(
            0, QCoreApplication.translate("SignalConfigWidget", "Automatic", None)
        )
        self.rangeModeComboBox.setItemText(
            1, QCoreApplication.translate("SignalConfigWidget", "Manual", None)
        )

        self.label10.setText(
            QCoreApplication.translate(
                "SignalConfigWidget", "Minimum range (in a.u.):", None
            )
        )
        self.label11.setText(
            QCoreApplication.translate(
                "SignalConfigWidget", "Maximum range (in a.u.):", None
            )
        )

    # retranslateUi
