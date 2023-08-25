# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'acquisition_config.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
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
    QGridLayout,
    QGroupBox,
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
        AcquisitionConfig.resize(400, 300)
        self.verticalLayout = QVBoxLayout(AcquisitionConfig)
        self.verticalLayout.setObjectName("verticalLayout")
        self.acquisitionGroupBox = QGroupBox(AcquisitionConfig)
        self.acquisitionGroupBox.setObjectName("acquisitionGroupBox")
        self.acquisitionGroupBox.setAlignment(Qt.AlignCenter)
        self.acquisitionGroupBox.setCheckable(True)
        self.acquisitionGroupBox.setChecked(False)
        self.verticalLayout_3 = QVBoxLayout(self.acquisitionGroupBox)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QLabel(self.acquisitionGroupBox)
        self.label.setObjectName("label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.acquisitionTextField = QLineEdit(self.acquisitionGroupBox)
        self.acquisitionTextField.setObjectName("acquisitionTextField")

        self.gridLayout.addWidget(self.acquisitionTextField, 0, 1, 1, 1)

        self.label_2 = QLabel(self.acquisitionGroupBox)
        self.label_2.setObjectName("label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.browseJSONButton = QPushButton(self.acquisitionGroupBox)
        self.browseJSONButton.setObjectName("browseJSONButton")

        self.gridLayout.addWidget(self.browseJSONButton, 1, 1, 1, 1)

        self.gridLayout.setColumnStretch(0, 2)
        self.gridLayout.setColumnStretch(1, 1)

        self.verticalLayout_3.addLayout(self.gridLayout)

        self.JSONLabel = QLabel(self.acquisitionGroupBox)
        self.JSONLabel.setObjectName("JSONLabel")

        self.verticalLayout_3.addWidget(self.JSONLabel)

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
        self.label.setText(
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
        self.label_2.setText(
            QCoreApplication.translate(
                "AcquisitionConfig", "JSON with configuration:", None
            )
        )
        self.browseJSONButton.setText(
            QCoreApplication.translate("AcquisitionConfig", "Browse", None)
        )
        self.JSONLabel.setText("")

    # retranslateUi
