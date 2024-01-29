# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'acquisition_config.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
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
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Ui_AcquisitionConfig(object):
    def setupUi(self, AcquisitionConfig):
        if not AcquisitionConfig.objectName():
            AcquisitionConfig.setObjectName("AcquisitionConfig")
        AcquisitionConfig.resize(400, 202)
        self.verticalLayout = QVBoxLayout(AcquisitionConfig)
        self.verticalLayout.setObjectName("verticalLayout")
        self.acquisitionGroupBox = QGroupBox(AcquisitionConfig)
        self.acquisitionGroupBox.setObjectName("acquisitionGroupBox")
        self.acquisitionGroupBox.setAlignment(Qt.AlignCenter)
        self.acquisitionGroupBox.setCheckable(True)
        self.acquisitionGroupBox.setChecked(False)
        self.formLayout = QFormLayout(self.acquisitionGroupBox)
        self.formLayout.setObjectName("formLayout")
        self.label1 = QLabel(self.acquisitionGroupBox)
        self.label1.setObjectName("label1")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.label2 = QLabel(self.acquisitionGroupBox)
        self.label2.setObjectName("label2")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label2)

        self.acquisitionTextField = QLineEdit(self.acquisitionGroupBox)
        self.acquisitionTextField.setObjectName("acquisitionTextField")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.acquisitionTextField)

        self.label3 = QLabel(self.acquisitionGroupBox)
        self.label3.setObjectName("label3")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label3)

        self.browseJSONButton = QPushButton(self.acquisitionGroupBox)
        self.browseJSONButton.setObjectName("browseJSONButton")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.browseJSONButton)

        self.label4 = QLabel(self.acquisitionGroupBox)
        self.label4.setObjectName("label4")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label4)

        self.configJSONPathLabel = QLabel(self.acquisitionGroupBox)
        self.configJSONPathLabel.setObjectName("configJSONPathLabel")

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.configJSONPathLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.signalComboBox = QComboBox(self.acquisitionGroupBox)
        self.signalComboBox.setObjectName("signalComboBox")

        self.horizontalLayout.addWidget(self.signalComboBox)

        self.rescanSignalsButton = QPushButton(self.acquisitionGroupBox)
        self.rescanSignalsButton.setObjectName("rescanSignalsButton")
        icon = QIcon(QIcon.fromTheme("view-refresh"))
        self.rescanSignalsButton.setIcon(icon)

        self.horizontalLayout.addWidget(self.rescanSignalsButton)

        self.horizontalLayout.setStretch(0, 4)
        self.horizontalLayout.setStretch(1, 1)

        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout)

        self.verticalLayout.addWidget(self.acquisitionGroupBox)

        self.retranslateUi(AcquisitionConfig)

        QMetaObject.connectSlotsByName(AcquisitionConfig)

    # setupUi

    def retranslateUi(self, AcquisitionConfig):
        AcquisitionConfig.setWindowTitle(
            QCoreApplication.translate("AcquisitionConfig", "Acquisition Widget", None)
        )
        self.acquisitionGroupBox.setTitle(
            QCoreApplication.translate(
                "AcquisitionConfig", "Configure acquisition", None
            )
        )
        self.label1.setText(
            QCoreApplication.translate("AcquisitionConfig", "Signal:", None)
        )
        self.label2.setText(
            QCoreApplication.translate("AcquisitionConfig", "Output file name:", None)
        )
        # if QT_CONFIG(tooltip)
        self.acquisitionTextField.setToolTip(
            QCoreApplication.translate(
                "AcquisitionConfig",
                "If no name is provided, one based on the timestamp will be used",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.label3.setText(
            QCoreApplication.translate(
                "AcquisitionConfig", "JSON with configuration:", None
            )
        )
        self.browseJSONButton.setText(
            QCoreApplication.translate("AcquisitionConfig", "Browse", None)
        )
        self.label4.setText(
            QCoreApplication.translate("AcquisitionConfig", "Path to JSON:", None)
        )
        self.configJSONPathLabel.setText("")
        # if QT_CONFIG(tooltip)
        self.rescanSignalsButton.setToolTip(
            QCoreApplication.translate("AcquisitionConfig", "Rescan signals", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.rescanSignalsButton.setText("")

    # retranslateUi
