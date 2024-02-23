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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QListView,
    QListWidget, QListWidgetItem, QMainWindow, QMenuBar,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QStatusBar, QVBoxLayout, QWidget)
from . import resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1920, 1080)
        MainWindow.setMinimumSize(QSize(1080, 720))
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        self.horizontalLayout1 = QHBoxLayout(self.centralWidget)
        self.horizontalLayout1.setObjectName(u"horizontalLayout1")
        self.confLayout = QVBoxLayout()
        self.confLayout.setObjectName(u"confLayout")
        self.horizontalLayout2 = QHBoxLayout()
        self.horizontalLayout2.setObjectName(u"horizontalLayout2")
        self.startStreamingButton = QPushButton(self.centralWidget)
        self.startStreamingButton.setObjectName(u"startStreamingButton")
        self.startStreamingButton.setEnabled(True)

        self.horizontalLayout2.addWidget(self.startStreamingButton)

        self.stopStreamingButton = QPushButton(self.centralWidget)
        self.stopStreamingButton.setObjectName(u"stopStreamingButton")
        self.stopStreamingButton.setEnabled(False)

        self.horizontalLayout2.addWidget(self.stopStreamingButton)


        self.confLayout.addLayout(self.horizontalLayout2)

        self.streamConfGroupBox = QGroupBox(self.centralWidget)
        self.streamConfGroupBox.setObjectName(u"streamConfGroupBox")
        self.streamConfGroupBox.setAlignment(Qt.AlignCenter)
        self.verticalLayout1 = QVBoxLayout(self.streamConfGroupBox)
        self.verticalLayout1.setObjectName(u"verticalLayout1")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.loadConfButton = QPushButton(self.streamConfGroupBox)
        self.loadConfButton.setObjectName(u"loadConfButton")

        self.horizontalLayout.addWidget(self.loadConfButton)

        self.saveConfButton = QPushButton(self.streamConfGroupBox)
        self.saveConfButton.setObjectName(u"saveConfButton")
        self.saveConfButton.setEnabled(False)

        self.horizontalLayout.addWidget(self.saveConfButton)


        self.verticalLayout1.addLayout(self.horizontalLayout)

        self.horizontalLayout4 = QHBoxLayout()
        self.horizontalLayout4.setObjectName(u"horizontalLayout4")
        self.addSourceButton = QPushButton(self.streamConfGroupBox)
        self.addSourceButton.setObjectName(u"addSourceButton")

        self.horizontalLayout4.addWidget(self.addSourceButton)

        self.deleteSourceButton = QPushButton(self.streamConfGroupBox)
        self.deleteSourceButton.setObjectName(u"deleteSourceButton")
        self.deleteSourceButton.setEnabled(False)
        icon = QIcon()
        iconThemeName = u"user-trash"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u"../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.deleteSourceButton.setIcon(icon)

        self.horizontalLayout4.addWidget(self.deleteSourceButton)

        self.horizontalLayout4.setStretch(0, 9)
        self.horizontalLayout4.setStretch(1, 1)

        self.verticalLayout1.addLayout(self.horizontalLayout4)

        self.sourceList = QListWidget(self.streamConfGroupBox)
        self.sourceList.setObjectName(u"sourceList")

        self.verticalLayout1.addWidget(self.sourceList)

        self.signalsGroupBox = QGroupBox(self.streamConfGroupBox)
        self.signalsGroupBox.setObjectName(u"signalsGroupBox")
        self.signalsGroupBox.setEnabled(False)
        self.signalsGroupBox.setFlat(True)
        self.verticalLayout2 = QVBoxLayout(self.signalsGroupBox)
        self.verticalLayout2.setObjectName(u"verticalLayout2")
        self.horizontalLayout5 = QHBoxLayout()
        self.horizontalLayout5.setObjectName(u"horizontalLayout5")
        self.addSignalButton = QPushButton(self.signalsGroupBox)
        self.addSignalButton.setObjectName(u"addSignalButton")

        self.horizontalLayout5.addWidget(self.addSignalButton)

        self.deleteSignalButton = QPushButton(self.signalsGroupBox)
        self.deleteSignalButton.setObjectName(u"deleteSignalButton")
        self.deleteSignalButton.setEnabled(False)
        icon1 = QIcon()
        iconThemeName = u"user-trash"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u"../../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.deleteSignalButton.setIcon(icon1)

        self.horizontalLayout5.addWidget(self.deleteSignalButton)

        self.moveUpButton = QPushButton(self.signalsGroupBox)
        self.moveUpButton.setObjectName(u"moveUpButton")
        self.moveUpButton.setEnabled(False)
        icon2 = QIcon()
        iconThemeName = u"arrow-up"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u"../../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.moveUpButton.setIcon(icon2)

        self.horizontalLayout5.addWidget(self.moveUpButton)

        self.moveDownButton = QPushButton(self.signalsGroupBox)
        self.moveDownButton.setObjectName(u"moveDownButton")
        self.moveDownButton.setEnabled(False)
        icon3 = QIcon()
        iconThemeName = u"arrow-down"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u"../../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.moveDownButton.setIcon(icon3)

        self.horizontalLayout5.addWidget(self.moveDownButton)

        self.horizontalLayout5.setStretch(0, 7)
        self.horizontalLayout5.setStretch(1, 1)
        self.horizontalLayout5.setStretch(2, 1)
        self.horizontalLayout5.setStretch(3, 1)

        self.verticalLayout2.addLayout(self.horizontalLayout5)

        self.sigNameList = QListWidget(self.signalsGroupBox)
        self.sigNameList.setObjectName(u"sigNameList")
        self.sigNameList.setAutoFillBackground(False)
        self.sigNameList.setResizeMode(QListView.Adjust)

        self.verticalLayout2.addWidget(self.sigNameList)

        self.verticalLayout2.setStretch(1, 1)

        self.verticalLayout1.addWidget(self.signalsGroupBox)

        self.verticalLayout1.setStretch(2, 1)
        self.verticalLayout1.setStretch(3, 2)

        self.confLayout.addWidget(self.streamConfGroupBox)

        self.scrollArea2 = QScrollArea(self.centralWidget)
        self.scrollArea2.setObjectName(u"scrollArea2")
        self.scrollArea2.setWidgetResizable(True)
        self.moduleContainer = QWidget()
        self.moduleContainer.setObjectName(u"moduleContainer")
        self.moduleContainer.setGeometry(QRect(0, 0, 374, 478))
        self.verticalLayout3 = QVBoxLayout(self.moduleContainer)
        self.verticalLayout3.setObjectName(u"verticalLayout3")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout3.addItem(self.verticalSpacer)

        self.scrollArea2.setWidget(self.moduleContainer)

        self.confLayout.addWidget(self.scrollArea2)

        self.confLayout.setStretch(1, 1)
        self.confLayout.setStretch(2, 1)

        self.horizontalLayout1.addLayout(self.confLayout)

        self.plotsLayout = QVBoxLayout()
        self.plotsLayout.setObjectName(u"plotsLayout")

        self.horizontalLayout1.addLayout(self.plotsLayout)

        self.horizontalLayout1.setStretch(0, 2)
        self.horizontalLayout1.setStretch(1, 8)
        MainWindow.setCentralWidget(self.centralWidget)
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
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"biogui", None))
        self.startStreamingButton.setText(QCoreApplication.translate("MainWindow", u"Start streaming", None))
        self.stopStreamingButton.setText(QCoreApplication.translate("MainWindow", u"Stop streaming", None))
        self.streamConfGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Configuration", None))
        self.loadConfButton.setText(QCoreApplication.translate("MainWindow", u"Load configuration", None))
        self.saveConfButton.setText(QCoreApplication.translate("MainWindow", u"Save configuration", None))
        self.addSourceButton.setText(QCoreApplication.translate("MainWindow", u"Add source", None))
#if QT_CONFIG(tooltip)
        self.deleteSourceButton.setToolTip(QCoreApplication.translate("MainWindow", u"Delete selected source", None))
#endif // QT_CONFIG(tooltip)
        self.deleteSourceButton.setText("")
#if QT_CONFIG(tooltip)
        self.signalsGroupBox.setToolTip(QCoreApplication.translate("MainWindow", u"Configure a source first", None))
#endif // QT_CONFIG(tooltip)
        self.signalsGroupBox.setTitle("")
#if QT_CONFIG(tooltip)
        self.addSignalButton.setToolTip(QCoreApplication.translate("MainWindow", u"The number of signals and channels must respect the communication protocol used in the device firmware and in the streaming controller", None))
#endif // QT_CONFIG(tooltip)
        self.addSignalButton.setText(QCoreApplication.translate("MainWindow", u"Add signal", None))
#if QT_CONFIG(tooltip)
        self.deleteSignalButton.setToolTip(QCoreApplication.translate("MainWindow", u"Delete selected signal", None))
#endif // QT_CONFIG(tooltip)
        self.deleteSignalButton.setText("")
#if QT_CONFIG(tooltip)
        self.moveUpButton.setToolTip(QCoreApplication.translate("MainWindow", u"Move up selected signal", None))
#endif // QT_CONFIG(tooltip)
        self.moveUpButton.setText("")
#if QT_CONFIG(tooltip)
        self.moveDownButton.setToolTip(QCoreApplication.translate("MainWindow", u"Move down selected signal", None))
#endif // QT_CONFIG(tooltip)
        self.moveDownButton.setText("")
#if QT_CONFIG(tooltip)
        self.sigNameList.setToolTip(QCoreApplication.translate("MainWindow", u"The order of the signals must match the one provided by the streaming controller", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

