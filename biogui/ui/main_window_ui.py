# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QGroupBox, QHBoxLayout,
    QHeaderView, QMainWindow, QMenu, QMenuBar,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QStatusBar, QTreeView, QVBoxLayout, QWidget)
from . import biogui_rc

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
        self.horizontalLayout3 = QHBoxLayout()
        self.horizontalLayout3.setObjectName(u"horizontalLayout3")
        self.addDataSourceButton = QPushButton(self.streamConfGroupBox)
        self.addDataSourceButton.setObjectName(u"addDataSourceButton")

        self.horizontalLayout3.addWidget(self.addDataSourceButton)

        self.deleteDataSourceButton = QPushButton(self.streamConfGroupBox)
        self.deleteDataSourceButton.setObjectName(u"deleteDataSourceButton")
        self.deleteDataSourceButton.setEnabled(False)
        icon = QIcon()
        iconThemeName = u"user-trash"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u"../../../.designer/backup", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.deleteDataSourceButton.setIcon(icon)

        self.horizontalLayout3.addWidget(self.deleteDataSourceButton)

        self.horizontalLayout3.setStretch(0, 9)
        self.horizontalLayout3.setStretch(1, 1)

        self.verticalLayout1.addLayout(self.horizontalLayout3)

        self.dataSourceTree = QTreeView(self.streamConfGroupBox)
        self.dataSourceTree.setObjectName(u"dataSourceTree")
        self.dataSourceTree.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.verticalLayout1.addWidget(self.dataSourceTree)

        self.horizontalLayout4 = QHBoxLayout()
        self.horizontalLayout4.setObjectName(u"horizontalLayout4")
        self.editSignalButton = QPushButton(self.streamConfGroupBox)
        self.editSignalButton.setObjectName(u"editSignalButton")
        self.editSignalButton.setEnabled(False)
        icon1 = QIcon()
        iconThemeName = u"edit-entry"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.editSignalButton.setIcon(icon1)

        self.horizontalLayout4.addWidget(self.editSignalButton)

        self.moveLeftButton = QPushButton(self.streamConfGroupBox)
        self.moveLeftButton.setObjectName(u"moveLeftButton")
        self.moveLeftButton.setEnabled(False)
        icon2 = QIcon()
        iconThemeName = u"arrow-left"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.moveLeftButton.setIcon(icon2)

        self.horizontalLayout4.addWidget(self.moveLeftButton)

        self.moveUpButton = QPushButton(self.streamConfGroupBox)
        self.moveUpButton.setObjectName(u"moveUpButton")
        self.moveUpButton.setEnabled(False)
        icon3 = QIcon()
        iconThemeName = u"arrow-up"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.moveUpButton.setIcon(icon3)

        self.horizontalLayout4.addWidget(self.moveUpButton)

        self.moveDownButton = QPushButton(self.streamConfGroupBox)
        self.moveDownButton.setObjectName(u"moveDownButton")
        self.moveDownButton.setEnabled(False)
        icon4 = QIcon()
        iconThemeName = u"arrow-down"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.moveDownButton.setIcon(icon4)

        self.horizontalLayout4.addWidget(self.moveDownButton)

        self.moveRightButton = QPushButton(self.streamConfGroupBox)
        self.moveRightButton.setObjectName(u"moveRightButton")
        self.moveRightButton.setEnabled(False)
        icon5 = QIcon()
        iconThemeName = u"arrow-right"
        if QIcon.hasThemeIcon(iconThemeName):
            icon5 = QIcon.fromTheme(iconThemeName)
        else:
            icon5.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.moveRightButton.setIcon(icon5)

        self.horizontalLayout4.addWidget(self.moveRightButton)


        self.verticalLayout1.addLayout(self.horizontalLayout4)


        self.confLayout.addWidget(self.streamConfGroupBox)

        self.scrollArea = QScrollArea(self.centralWidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.moduleContainer = QWidget()
        self.moduleContainer.setObjectName(u"moduleContainer")
        self.moduleContainer.setGeometry(QRect(0, 0, 374, 639))
        self.verticalLayout3 = QVBoxLayout(self.moduleContainer)
        self.verticalLayout3.setObjectName(u"verticalLayout3")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout3.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.moduleContainer)

        self.confLayout.addWidget(self.scrollArea)

        self.confLayout.setStretch(1, 1)
        self.confLayout.setStretch(2, 2)

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
        self.menuModules = QMenu(self.menubar)
        self.menuModules.setObjectName(u"menuModules")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        QWidget.setTabOrder(self.startStreamingButton, self.stopStreamingButton)
        QWidget.setTabOrder(self.stopStreamingButton, self.addDataSourceButton)
        QWidget.setTabOrder(self.addDataSourceButton, self.deleteDataSourceButton)
        QWidget.setTabOrder(self.deleteDataSourceButton, self.editSignalButton)
        QWidget.setTabOrder(self.editSignalButton, self.scrollArea)

        self.menubar.addAction(self.menuModules.menuAction())

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"BioGUI", None))
        self.startStreamingButton.setText(QCoreApplication.translate("MainWindow", u"Start streaming", None))
        self.stopStreamingButton.setText(QCoreApplication.translate("MainWindow", u"Stop streaming", None))
        self.streamConfGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Configuration", None))
        self.addDataSourceButton.setText(QCoreApplication.translate("MainWindow", u"Add data source", None))
#if QT_CONFIG(tooltip)
        self.deleteDataSourceButton.setToolTip(QCoreApplication.translate("MainWindow", u"Delete selected source", None))
#endif // QT_CONFIG(tooltip)
        self.deleteDataSourceButton.setText("")
#if QT_CONFIG(tooltip)
        self.editSignalButton.setToolTip(QCoreApplication.translate("MainWindow", u"Edit the selected signal", None))
#endif // QT_CONFIG(tooltip)
        self.editSignalButton.setText("")
#if QT_CONFIG(tooltip)
        self.moveLeftButton.setToolTip(QCoreApplication.translate("MainWindow", u"Move the selected signal left", None))
#endif // QT_CONFIG(tooltip)
        self.moveLeftButton.setText("")
#if QT_CONFIG(tooltip)
        self.moveUpButton.setToolTip(QCoreApplication.translate("MainWindow", u"Move the selected signal up", None))
#endif // QT_CONFIG(tooltip)
        self.moveUpButton.setText("")
#if QT_CONFIG(tooltip)
        self.moveDownButton.setToolTip(QCoreApplication.translate("MainWindow", u"Move the selected signal down", None))
#endif // QT_CONFIG(tooltip)
        self.moveDownButton.setText("")
#if QT_CONFIG(tooltip)
        self.moveRightButton.setToolTip(QCoreApplication.translate("MainWindow", u"Move the selected signal right", None))
#endif // QT_CONFIG(tooltip)
        self.moveRightButton.setText("")
        self.menuModules.setTitle(QCoreApplication.translate("MainWindow", u"Modules", None))
    # retranslateUi

