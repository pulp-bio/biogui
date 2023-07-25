# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from pyqtgraph import PlotWidget
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
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from . import resources_rc


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1920, 1080)
        MainWindow.setMinimumSize(QSize(1080, 720))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.confLayout = QVBoxLayout()
        self.confLayout.setObjectName("confLayout")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.startStreamingButton = QPushButton(self.centralwidget)
        self.startStreamingButton.setObjectName("startStreamingButton")

        self.horizontalLayout_5.addWidget(self.startStreamingButton)

        self.stopStreamingButton = QPushButton(self.centralwidget)
        self.stopStreamingButton.setObjectName("stopStreamingButton")

        self.horizontalLayout_5.addWidget(self.stopStreamingButton)

        self.confLayout.addLayout(self.horizontalLayout_5)

        self.verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        self.confLayout.addItem(self.verticalSpacer)

        self.streamConfGroupBox = QGroupBox(self.centralwidget)
        self.streamConfGroupBox.setObjectName("streamConfGroupBox")
        self.streamConfGroupBox.setAlignment(Qt.AlignCenter)
        self.gridLayout = QGridLayout(self.streamConfGroupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.serialPortsComboBox = QComboBox(self.streamConfGroupBox)
        self.serialPortsComboBox.setObjectName("serialPortsComboBox")

        self.gridLayout.addWidget(self.serialPortsComboBox, 0, 1, 1, 1)

        self.rescanSerialPortsButton = QPushButton(self.streamConfGroupBox)
        self.rescanSerialPortsButton.setObjectName("rescanSerialPortsButton")

        self.gridLayout.addWidget(self.rescanSerialPortsButton, 0, 2, 1, 1)

        self.label = QLabel(self.streamConfGroupBox)
        self.label.setObjectName("label")
        self.label.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.label_2 = QLabel(self.streamConfGroupBox)
        self.label_2.setObjectName("label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.channelsComboBox = QComboBox(self.streamConfGroupBox)
        self.channelsComboBox.addItem("")
        self.channelsComboBox.setObjectName("channelsComboBox")

        self.gridLayout.addWidget(self.channelsComboBox, 1, 1, 1, 1)

        self.gridLayout.setColumnStretch(0, 3)
        self.gridLayout.setColumnStretch(1, 3)
        self.gridLayout.setColumnStretch(2, 1)

        self.confLayout.addWidget(self.streamConfGroupBox)

        self.horizontalLayout.addLayout(self.confLayout)

        self.graphWidget = PlotWidget(self.centralwidget)
        self.graphWidget.setObjectName("graphWidget")

        self.horizontalLayout.addWidget(self.graphWidget)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 4)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 1920, 30))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", "sEMG Acquisition GUI", None)
        )
        self.startStreamingButton.setText(
            QCoreApplication.translate("MainWindow", "Start streaming", None)
        )
        self.stopStreamingButton.setText(
            QCoreApplication.translate("MainWindow", "Stop streaming", None)
        )
        self.streamConfGroupBox.setTitle(
            QCoreApplication.translate("MainWindow", "Configuration", None)
        )
        # if QT_CONFIG(tooltip)
        self.serialPortsComboBox.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "List of available serial ports", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(tooltip)
        self.rescanSerialPortsButton.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "Refresh list of available serial ports", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.rescanSerialPortsButton.setText(
            QCoreApplication.translate("MainWindow", "Rescan", None)
        )
        self.label.setText(
            QCoreApplication.translate("MainWindow", "Serial port:", None)
        )
        self.label_2.setText(
            QCoreApplication.translate("MainWindow", "Number of channels:", None)
        )
        self.channelsComboBox.setItemText(
            0, QCoreApplication.translate("MainWindow", "16", None)
        )

    # retranslateUi
