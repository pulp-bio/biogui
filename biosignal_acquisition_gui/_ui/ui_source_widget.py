# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'source_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
    QListView, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_SourceWidget(object):
    def setupUi(self, SourceWidget):
        if not SourceWidget.objectName():
            SourceWidget.setObjectName(u"SourceWidget")
        SourceWidget.resize(400, 300)
        self.verticalLayout = QVBoxLayout(SourceWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout4 = QHBoxLayout()
        self.horizontalLayout4.setObjectName(u"horizontalLayout4")
        self.label1 = QLabel(SourceWidget)
        self.label1.setObjectName(u"label1")
        self.label1.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.horizontalLayout4.addWidget(self.label1)

        self.sourceComboBox = QComboBox(SourceWidget)
        self.sourceComboBox.addItem("")
        self.sourceComboBox.addItem("")
        self.sourceComboBox.addItem("")
        self.sourceComboBox.setObjectName(u"sourceComboBox")

        self.horizontalLayout4.addWidget(self.sourceComboBox)

        self.horizontalLayout4.setStretch(0, 3)
        self.horizontalLayout4.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout4)

        self.sourceConfContainer = QVBoxLayout()
        self.sourceConfContainer.setObjectName(u"sourceConfContainer")

        self.verticalLayout.addLayout(self.sourceConfContainer)

        self.horizontalLayout5 = QHBoxLayout()
        self.horizontalLayout5.setObjectName(u"horizontalLayout5")
        self.addSignalButton = QPushButton(SourceWidget)
        self.addSignalButton.setObjectName(u"addSignalButton")

        self.horizontalLayout5.addWidget(self.addSignalButton)

        self.deleteSignalButton = QPushButton(SourceWidget)
        self.deleteSignalButton.setObjectName(u"deleteSignalButton")
        self.deleteSignalButton.setEnabled(False)
        icon = QIcon()
        iconThemeName = u"user-trash"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u"../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.deleteSignalButton.setIcon(icon)

        self.horizontalLayout5.addWidget(self.deleteSignalButton)

        self.moveUpButton = QPushButton(SourceWidget)
        self.moveUpButton.setObjectName(u"moveUpButton")
        self.moveUpButton.setEnabled(False)
        icon1 = QIcon()
        iconThemeName = u"arrow-up"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u"../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.moveUpButton.setIcon(icon1)

        self.horizontalLayout5.addWidget(self.moveUpButton)

        self.moveDownButton = QPushButton(SourceWidget)
        self.moveDownButton.setObjectName(u"moveDownButton")
        self.moveDownButton.setEnabled(False)
        icon2 = QIcon()
        iconThemeName = u"arrow-down"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u"../../../.designer/backup", QSize(), QIcon.Normal, QIcon.Off)

        self.moveDownButton.setIcon(icon2)

        self.horizontalLayout5.addWidget(self.moveDownButton)

        self.horizontalLayout5.setStretch(0, 7)
        self.horizontalLayout5.setStretch(1, 1)
        self.horizontalLayout5.setStretch(2, 1)
        self.horizontalLayout5.setStretch(3, 1)

        self.verticalLayout.addLayout(self.horizontalLayout5)

        self.signalList = QListWidget(SourceWidget)
        self.signalList.setObjectName(u"signalList")
        self.signalList.setAutoFillBackground(False)
        self.signalList.setResizeMode(QListView.Adjust)

        self.verticalLayout.addWidget(self.signalList)


        self.retranslateUi(SourceWidget)

        QMetaObject.connectSlotsByName(SourceWidget)
    # setupUi

    def retranslateUi(self, SourceWidget):
        SourceWidget.setWindowTitle(QCoreApplication.translate("SourceWidget", u"Source widget", None))
        self.label1.setText(QCoreApplication.translate("SourceWidget", u"Source:", None))
        self.sourceComboBox.setItemText(0, QCoreApplication.translate("SourceWidget", u"Serial port", None))
        self.sourceComboBox.setItemText(1, QCoreApplication.translate("SourceWidget", u"Socket", None))
        self.sourceComboBox.setItemText(2, QCoreApplication.translate("SourceWidget", u"Dummy", None))

#if QT_CONFIG(tooltip)
        self.sourceComboBox.setToolTip(QCoreApplication.translate("SourceWidget", u"List of available serial ports", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.addSignalButton.setToolTip(QCoreApplication.translate("SourceWidget", u"The number of signals and channels must respect the communication protocol used in the device firmware and in the streaming controller", None))
#endif // QT_CONFIG(tooltip)
        self.addSignalButton.setText(QCoreApplication.translate("SourceWidget", u"Add signal", None))
#if QT_CONFIG(tooltip)
        self.deleteSignalButton.setToolTip(QCoreApplication.translate("SourceWidget", u"Delete selected signal", None))
#endif // QT_CONFIG(tooltip)
        self.deleteSignalButton.setText("")
#if QT_CONFIG(tooltip)
        self.moveUpButton.setToolTip(QCoreApplication.translate("SourceWidget", u"Move up selected signal", None))
#endif // QT_CONFIG(tooltip)
        self.moveUpButton.setText("")
#if QT_CONFIG(tooltip)
        self.moveDownButton.setToolTip(QCoreApplication.translate("SourceWidget", u"Move down selected signal", None))
#endif // QT_CONFIG(tooltip)
        self.moveDownButton.setText("")
#if QT_CONFIG(tooltip)
        self.signalList.setToolTip(QCoreApplication.translate("SourceWidget", u"The order of the signals must match the one provided by the streaming controller", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

