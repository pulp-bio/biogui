# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox, QHBoxLayout,
    QLabel, QListView, QListWidget, QListWidgetItem,
    QMainWindow, QMenuBar, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QStatusBar, QVBoxLayout,
    QWidget)
from . import resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1920, 1080)
        MainWindow.setMinimumSize(QSize(1080, 720))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout1 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout1.setObjectName(u"horizontalLayout1")
        self.confLayout = QVBoxLayout()
        self.confLayout.setObjectName(u"confLayout")
        self.horizontalLayout2 = QHBoxLayout()
        self.horizontalLayout2.setObjectName(u"horizontalLayout2")
        self.startStreamingButton = QPushButton(self.centralwidget)
        self.startStreamingButton.setObjectName(u"startStreamingButton")
        self.startStreamingButton.setEnabled(True)

        self.horizontalLayout2.addWidget(self.startStreamingButton)

        self.stopStreamingButton = QPushButton(self.centralwidget)
        self.stopStreamingButton.setObjectName(u"stopStreamingButton")
        self.stopStreamingButton.setEnabled(False)

        self.horizontalLayout2.addWidget(self.stopStreamingButton)


        self.confLayout.addLayout(self.horizontalLayout2)

        self.streamConfGroupBox = QGroupBox(self.centralwidget)
        self.streamConfGroupBox.setObjectName(u"streamConfGroupBox")
        self.streamConfGroupBox.setAlignment(Qt.AlignCenter)
        self.verticalLayout1 = QVBoxLayout(self.streamConfGroupBox)
        self.verticalLayout1.setObjectName(u"verticalLayout1")
        self.horizontalLayout3 = QHBoxLayout()
        self.horizontalLayout3.setObjectName(u"horizontalLayout3")
        self.label1 = QLabel(self.streamConfGroupBox)
        self.label1.setObjectName(u"label1")
        self.label1.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.horizontalLayout3.addWidget(self.label1)

        self.sourceComboBox = QComboBox(self.streamConfGroupBox)
        self.sourceComboBox.addItem("")
        self.sourceComboBox.addItem("")
        self.sourceComboBox.addItem("")
        self.sourceComboBox.setObjectName(u"sourceComboBox")

        self.horizontalLayout3.addWidget(self.sourceComboBox)

        self.horizontalLayout3.setStretch(0, 3)
        self.horizontalLayout3.setStretch(1, 1)

        self.verticalLayout1.addLayout(self.horizontalLayout3)

        self.sourceConfContainer = QVBoxLayout()
        self.sourceConfContainer.setObjectName(u"sourceConfContainer")

        self.verticalLayout1.addLayout(self.sourceConfContainer)

        self.horizontalLayout4 = QHBoxLayout()
        self.horizontalLayout4.setObjectName(u"horizontalLayout4")
        self.addSignalButton = QPushButton(self.streamConfGroupBox)
        self.addSignalButton.setObjectName(u"addSignalButton")

        self.horizontalLayout4.addWidget(self.addSignalButton)

        self.deleteSignalButton = QPushButton(self.streamConfGroupBox)
        self.deleteSignalButton.setObjectName(u"deleteSignalButton")
        self.deleteSignalButton.setEnabled(False)
        icon = QIcon()
        iconThemeName = u"user-trash"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u"../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.deleteSignalButton.setIcon(icon)

        self.horizontalLayout4.addWidget(self.deleteSignalButton)

        self.moveUpButton = QPushButton(self.streamConfGroupBox)
        self.moveUpButton.setObjectName(u"moveUpButton")
        self.moveUpButton.setEnabled(False)
        icon1 = QIcon()
        iconThemeName = u"arrow-up"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u"../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.moveUpButton.setIcon(icon1)

        self.horizontalLayout4.addWidget(self.moveUpButton)

        self.moveDownButton = QPushButton(self.streamConfGroupBox)
        self.moveDownButton.setObjectName(u"moveDownButton")
        self.moveDownButton.setEnabled(False)
        icon2 = QIcon()
        iconThemeName = u"arrow-down"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u"../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.moveDownButton.setIcon(icon2)

        self.horizontalLayout4.addWidget(self.moveDownButton)

        self.horizontalLayout4.setStretch(0, 7)
        self.horizontalLayout4.setStretch(1, 1)
        self.horizontalLayout4.setStretch(2, 1)
        self.horizontalLayout4.setStretch(3, 1)

        self.verticalLayout1.addLayout(self.horizontalLayout4)

        self.signalList = QListWidget(self.streamConfGroupBox)
        self.signalList.setObjectName(u"signalList")
        self.signalList.setAutoFillBackground(False)
        self.signalList.setResizeMode(QListView.Adjust)

        self.verticalLayout1.addWidget(self.signalList)


        self.confLayout.addWidget(self.streamConfGroupBox)

        self.scrollArea1 = QScrollArea(self.centralwidget)
        self.scrollArea1.setObjectName(u"scrollArea1")
        self.scrollArea1.setWidgetResizable(True)
        self.moduleContainer = QWidget()
        self.moduleContainer.setObjectName(u"moduleContainer")
        self.moduleContainer.setGeometry(QRect(0, 0, 374, 742))
        self.verticalLayout3 = QVBoxLayout(self.moduleContainer)
        self.verticalLayout3.setObjectName(u"verticalLayout3")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout3.addItem(self.verticalSpacer)

        self.scrollArea1.setWidget(self.moduleContainer)

        self.confLayout.addWidget(self.scrollArea1)

        self.confLayout.setStretch(1, 2)
        self.confLayout.setStretch(2, 8)

        self.horizontalLayout1.addLayout(self.confLayout)

        self.plotsLayout = QVBoxLayout()
        self.plotsLayout.setObjectName(u"plotsLayout")

        self.horizontalLayout1.addLayout(self.plotsLayout)

        self.horizontalLayout1.setStretch(0, 2)
        self.horizontalLayout1.setStretch(1, 8)
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
        self.label1.setText(QCoreApplication.translate("MainWindow", u"Source:", None))
        self.sourceComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"Serial port", None))
        self.sourceComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"Socket", None))
        self.sourceComboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"Dummy", None))

#if QT_CONFIG(tooltip)
        self.sourceComboBox.setToolTip(QCoreApplication.translate("MainWindow", u"List of available serial ports", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.addSignalButton.setToolTip(QCoreApplication.translate("MainWindow", u"The number of signals and channels must respect the communication protocol used in the device firmware and in the streaming controller", None))
#endif // QT_CONFIG(tooltip)
        self.addSignalButton.setText(QCoreApplication.translate("MainWindow", u"Add signal", None))
        self.deleteSignalButton.setText("")
        self.moveUpButton.setText("")
        self.moveDownButton.setText("")
#if QT_CONFIG(tooltip)
        self.signalList.setToolTip(QCoreApplication.translate("MainWindow", u"The order of the signals must match the one provided by the streaming controller", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

