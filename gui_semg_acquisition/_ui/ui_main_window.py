# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QMainWindow, QMenuBar,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QStatusBar, QVBoxLayout, QWidget)

from pyqtgraph import PlotWidget
from . import resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1920, 1080)
        MainWindow.setMinimumSize(QSize(1080, 720))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.confLayout = QVBoxLayout()
        self.confLayout.setObjectName(u"confLayout")
        self.horizontalLayout1 = QHBoxLayout()
        self.horizontalLayout1.setObjectName(u"horizontalLayout1")
        self.startStreamingButton = QPushButton(self.centralwidget)
        self.startStreamingButton.setObjectName(u"startStreamingButton")

        self.horizontalLayout1.addWidget(self.startStreamingButton)

        self.stopStreamingButton = QPushButton(self.centralwidget)
        self.stopStreamingButton.setObjectName(u"stopStreamingButton")

        self.horizontalLayout1.addWidget(self.stopStreamingButton)


        self.confLayout.addLayout(self.horizontalLayout1)

        self.streamConfGroupBox = QGroupBox(self.centralwidget)
        self.streamConfGroupBox.setObjectName(u"streamConfGroupBox")
        self.streamConfGroupBox.setAlignment(Qt.AlignCenter)
        self.gridLayout = QGridLayout(self.streamConfGroupBox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.channelsComboBox = QComboBox(self.streamConfGroupBox)
        self.channelsComboBox.addItem("")
        self.channelsComboBox.addItem("")
        self.channelsComboBox.setObjectName(u"channelsComboBox")

        self.gridLayout.addWidget(self.channelsComboBox, 1, 1, 1, 1)

        self.label2 = QLabel(self.streamConfGroupBox)
        self.label2.setObjectName(u"label2")

        self.gridLayout.addWidget(self.label2, 1, 0, 1, 1)

        self.serialPortsComboBox = QComboBox(self.streamConfGroupBox)
        self.serialPortsComboBox.setObjectName(u"serialPortsComboBox")

        self.gridLayout.addWidget(self.serialPortsComboBox, 0, 1, 1, 1)

        self.rescanSerialPortsButton = QPushButton(self.streamConfGroupBox)
        self.rescanSerialPortsButton.setObjectName(u"rescanSerialPortsButton")

        self.gridLayout.addWidget(self.rescanSerialPortsButton, 0, 2, 1, 1)

        self.label1 = QLabel(self.streamConfGroupBox)
        self.label1.setObjectName(u"label1")
        self.label1.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label1, 0, 0, 1, 1)

        self.gridLayout.setColumnStretch(0, 3)

        self.confLayout.addWidget(self.streamConfGroupBox)

        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.moduleContainer = QWidget()
        self.moduleContainer.setObjectName(u"moduleContainer")
        self.moduleContainer.setGeometry(QRect(0, 0, 470, 847))
        self.verticalLayout_2 = QVBoxLayout(self.moduleContainer)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.moduleContainer)

        self.confLayout.addWidget(self.scrollArea)


        self.horizontalLayout.addLayout(self.confLayout)

        self.graphWidget = PlotWidget(self.centralwidget)
        self.graphWidget.setObjectName(u"graphWidget")

        self.horizontalLayout.addWidget(self.graphWidget)

        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 6)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1920, 30))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"sEMG Acquisition GUI", None))
        self.startStreamingButton.setText(QCoreApplication.translate("MainWindow", u"Start streaming", None))
        self.stopStreamingButton.setText(QCoreApplication.translate("MainWindow", u"Stop streaming", None))
        self.streamConfGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Configuration", None))
        self.channelsComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"16", None))
        self.channelsComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"32", None))

        self.label2.setText(QCoreApplication.translate("MainWindow", u"Number of channels:", None))
#if QT_CONFIG(tooltip)
        self.serialPortsComboBox.setToolTip(QCoreApplication.translate("MainWindow", u"List of available serial ports", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.rescanSerialPortsButton.setToolTip(QCoreApplication.translate("MainWindow", u"Refresh list of available serial ports", None))
#endif // QT_CONFIG(tooltip)
        self.rescanSerialPortsButton.setText(QCoreApplication.translate("MainWindow", u"Rescan", None))
        self.label1.setText(QCoreApplication.translate("MainWindow", u"Serial port:", None))
    # retranslateUi

