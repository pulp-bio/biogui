# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'serial_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
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
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class Ui_SerialConfigWidget(object):
    def setupUi(self, SerialConfigWidget):
        if not SerialConfigWidget.objectName():
            SerialConfigWidget.setObjectName("SerialConfigWidget")
        SerialConfigWidget.resize(400, 300)
        self.formLayout = QFormLayout(SerialConfigWidget)
        self.formLayout.setObjectName("formLayout")
        self.label1 = QLabel(SerialConfigWidget)
        self.label1.setObjectName("label1")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.serialPortsComboBox = QComboBox(SerialConfigWidget)
        self.serialPortsComboBox.setObjectName("serialPortsComboBox")

        self.horizontalLayout.addWidget(self.serialPortsComboBox)

        self.rescanSerialPortsButton = QPushButton(SerialConfigWidget)
        self.rescanSerialPortsButton.setObjectName("rescanSerialPortsButton")
        icon = QIcon()
        iconThemeName = "view-refresh"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(".", QSize(), QIcon.Normal, QIcon.Off)

        self.rescanSerialPortsButton.setIcon(icon)

        self.horizontalLayout.addWidget(self.rescanSerialPortsButton)

        self.horizontalLayout.setStretch(0, 4)
        self.horizontalLayout.setStretch(1, 1)

        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout)

        self.label2 = QLabel(SerialConfigWidget)
        self.label2.setObjectName("label2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.baudRateTextField = QLineEdit(SerialConfigWidget)
        self.baudRateTextField.setObjectName("baudRateTextField")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.baudRateTextField)

        QWidget.setTabOrder(self.serialPortsComboBox, self.rescanSerialPortsButton)
        QWidget.setTabOrder(self.rescanSerialPortsButton, self.baudRateTextField)

        self.retranslateUi(SerialConfigWidget)

        QMetaObject.connectSlotsByName(SerialConfigWidget)

    # setupUi

    def retranslateUi(self, SerialConfigWidget):
        SerialConfigWidget.setWindowTitle(
            QCoreApplication.translate(
                "SerialConfigWidget", "Serial Configuration Widget", None
            )
        )
        self.label1.setText(
            QCoreApplication.translate("SerialConfigWidget", "Serial port:", None)
        )
        # if QT_CONFIG(tooltip)
        self.rescanSerialPortsButton.setToolTip(
            QCoreApplication.translate(
                "SerialConfigWidget", "Rescan serial ports", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.rescanSerialPortsButton.setText("")
        self.label2.setText(
            QCoreApplication.translate("SerialConfigWidget", "Baud rate:", None)
        )

    # retranslateUi
