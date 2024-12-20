# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QMainWindow,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QTreeView, QVBoxLayout, QWidget)
from . import biogui_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1920, 1080)
        MainWindow.setMinimumSize(QSize(1080, 720))
        self.actionConfigureAcq = QAction(MainWindow)
        self.actionConfigureAcq.setObjectName(u"actionConfigureAcq")
        self.actionConfigureAcq.setCheckable(True)
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
        self.startStreamingButton.setEnabled(False)

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

        self.editButton = QPushButton(self.streamConfGroupBox)
        self.editButton.setObjectName(u"editButton")
        self.editButton.setEnabled(False)
        icon = QIcon(QIcon.fromTheme(u"edit-entry"))
        self.editButton.setIcon(icon)

        self.horizontalLayout3.addWidget(self.editButton)

        self.deleteDataSourceButton = QPushButton(self.streamConfGroupBox)
        self.deleteDataSourceButton.setObjectName(u"deleteDataSourceButton")
        self.deleteDataSourceButton.setEnabled(False)
        icon1 = QIcon()
        iconThemeName = u"user-trash"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u"../../../.designer/backup", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.deleteDataSourceButton.setIcon(icon1)

        self.horizontalLayout3.addWidget(self.deleteDataSourceButton)

        self.horizontalLayout3.setStretch(0, 1)

        self.verticalLayout1.addLayout(self.horizontalLayout3)

        self.dataSourceTree = QTreeView(self.streamConfGroupBox)
        self.dataSourceTree.setObjectName(u"dataSourceTree")
        self.dataSourceTree.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.verticalLayout1.addWidget(self.dataSourceTree)

        self.horizontalLayout4 = QHBoxLayout()
        self.horizontalLayout4.setObjectName(u"horizontalLayout4")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout4.addItem(self.horizontalSpacer)

        self.label = QLabel(self.streamConfGroupBox)
        self.label.setObjectName(u"label")

        self.horizontalLayout4.addWidget(self.label)

        self.renderLenComboBox = QComboBox(self.streamConfGroupBox)
        self.renderLenComboBox.addItem("")
        self.renderLenComboBox.addItem("")
        self.renderLenComboBox.addItem("")
        self.renderLenComboBox.addItem("")
        self.renderLenComboBox.addItem("")
        self.renderLenComboBox.addItem("")
        self.renderLenComboBox.addItem("")
        self.renderLenComboBox.setObjectName(u"renderLenComboBox")

        self.horizontalLayout4.addWidget(self.renderLenComboBox)


        self.verticalLayout1.addLayout(self.horizontalLayout4)


        self.confLayout.addWidget(self.streamConfGroupBox)

        self.scrollArea = QScrollArea(self.centralWidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.moduleContainer = QWidget()
        self.moduleContainer.setObjectName(u"moduleContainer")
        self.moduleContainer.setGeometry(QRect(0, 0, 374, 675))
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
        QWidget.setTabOrder(self.startStreamingButton, self.stopStreamingButton)
        QWidget.setTabOrder(self.stopStreamingButton, self.addDataSourceButton)
        QWidget.setTabOrder(self.addDataSourceButton, self.deleteDataSourceButton)
        QWidget.setTabOrder(self.deleteDataSourceButton, self.scrollArea)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"BioGUI", None))
        self.actionConfigureAcq.setText(QCoreApplication.translate("MainWindow", u"Configure acquisition", None))
        self.startStreamingButton.setText(QCoreApplication.translate("MainWindow", u"Start streaming", None))
        self.stopStreamingButton.setText(QCoreApplication.translate("MainWindow", u"Stop streaming", None))
        self.streamConfGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Configuration", None))
        self.addDataSourceButton.setText(QCoreApplication.translate("MainWindow", u"Add data source", None))
#if QT_CONFIG(tooltip)
        self.editButton.setToolTip(QCoreApplication.translate("MainWindow", u"Edit the selected signal", None))
#endif // QT_CONFIG(tooltip)
        self.editButton.setText("")
#if QT_CONFIG(tooltip)
        self.deleteDataSourceButton.setToolTip(QCoreApplication.translate("MainWindow", u"Delete selected source", None))
#endif // QT_CONFIG(tooltip)
        self.deleteDataSourceButton.setText("")
        self.label.setText(QCoreApplication.translate("MainWindow", u"Render length:", None))
        self.renderLenComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"100 ms", None))
        self.renderLenComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"200 ms", None))
        self.renderLenComboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"500 ms", None))
        self.renderLenComboBox.setItemText(3, QCoreApplication.translate("MainWindow", u"1 s", None))
        self.renderLenComboBox.setItemText(4, QCoreApplication.translate("MainWindow", u"2 s", None))
        self.renderLenComboBox.setItemText(5, QCoreApplication.translate("MainWindow", u"5 s", None))
        self.renderLenComboBox.setItemText(6, QCoreApplication.translate("MainWindow", u"10 s", None))

    # retranslateUi

