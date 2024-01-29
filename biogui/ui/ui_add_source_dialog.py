# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'add_source_dialog.ui'
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
    QAbstractButton,
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Ui_AddSourceDialog(object):
    def setupUi(self, AddSourceDialog):
        if not AddSourceDialog.objectName():
            AddSourceDialog.setObjectName("AddSourceDialog")
        AddSourceDialog.resize(480, 320)
        self.verticalLayout = QVBoxLayout(AddSourceDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label2 = QLabel(AddSourceDialog)
        self.label2.setObjectName("label2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.decodeModulePathLabel = QLabel(AddSourceDialog)
        self.decodeModulePathLabel.setObjectName("decodeModulePathLabel")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.decodeModulePathLabel)

        self.label3 = QLabel(AddSourceDialog)
        self.label3.setObjectName("label3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label3)

        self.packetSizeTextField = QLineEdit(AddSourceDialog)
        self.packetSizeTextField.setObjectName("packetSizeTextField")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.packetSizeTextField)

        self.label4 = QLabel(AddSourceDialog)
        self.label4.setObjectName("label4")
        self.label4.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label4)

        self.sourceComboBox = QComboBox(AddSourceDialog)
        self.sourceComboBox.setObjectName("sourceComboBox")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.sourceComboBox)

        self.browseDecodeModuleButton = QPushButton(AddSourceDialog)
        self.browseDecodeModuleButton.setObjectName("browseDecodeModuleButton")

        self.formLayout.setWidget(
            0, QFormLayout.FieldRole, self.browseDecodeModuleButton
        )

        self.label1 = QLabel(AddSourceDialog)
        self.label1.setObjectName("label1")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.verticalLayout.addLayout(self.formLayout)

        self.sourceConfigContainer = QVBoxLayout()
        self.sourceConfigContainer.setObjectName("sourceConfigContainer")

        self.verticalLayout.addLayout(self.sourceConfigContainer)

        self.buttonBox = QDialogButtonBox(AddSourceDialog)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(AddSourceDialog)
        self.buttonBox.accepted.connect(AddSourceDialog.accept)
        self.buttonBox.rejected.connect(AddSourceDialog.reject)

        QMetaObject.connectSlotsByName(AddSourceDialog)

    # setupUi

    def retranslateUi(self, AddSourceDialog):
        AddSourceDialog.setWindowTitle(
            QCoreApplication.translate("AddSourceDialog", "Add source", None)
        )
        self.label2.setText(
            QCoreApplication.translate("AddSourceDialog", "Path to module:", None)
        )
        self.decodeModulePathLabel.setText("")
        self.label3.setText(
            QCoreApplication.translate("AddSourceDialog", "Packet size:", None)
        )
        # if QT_CONFIG(tooltip)
        self.packetSizeTextField.setToolTip(
            QCoreApplication.translate(
                "AddSourceDialog", "Number of bytes in each packet", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.label4.setText(
            QCoreApplication.translate("AddSourceDialog", "Source:", None)
        )
        # if QT_CONFIG(tooltip)
        self.sourceComboBox.setToolTip(
            QCoreApplication.translate(
                "AddSourceDialog", "List of available serial ports", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(tooltip)
        self.browseDecodeModuleButton.setToolTip(
            QCoreApplication.translate(
                "AddSourceDialog",
                'The module must contain a function called "decodeFn" that converts bytes into a sequence of signals',
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.browseDecodeModuleButton.setText(
            QCoreApplication.translate("AddSourceDialog", "Browse", None)
        )
        self.label1.setText(
            QCoreApplication.translate(
                "AddSourceDialog", "Module with decode function:", None
            )
        )

    # retranslateUi
