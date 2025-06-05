# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'microphone_data_source_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
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
from PySide6.QtWidgets import (QApplication, QComboBox, QLineEdit, QSizePolicy,
    QTextEdit, QWidget)

class Ui_MicrophoneDataSourceConfigWidget(object):
    def setupUi(self, MicrophoneDataSourceConfigWidget):
        if not MicrophoneDataSourceConfigWidget.objectName():
            MicrophoneDataSourceConfigWidget.setObjectName(u"MicrophoneDataSourceConfigWidget")
        MicrophoneDataSourceConfigWidget.resize(400, 300)
        self.audioDeviceComboBox = QComboBox(MicrophoneDataSourceConfigWidget)
        self.audioDeviceComboBox.setObjectName(u"audioDeviceComboBox")
        self.audioDeviceComboBox.setGeometry(QRect(40, 0, 82, 28))
        self.sampleRateTextField = QLineEdit(MicrophoneDataSourceConfigWidget)
        self.sampleRateTextField.setObjectName(u"sampleRateTextField")
        self.sampleRateTextField.setGeometry(QRect(30, 50, 113, 28))
        self.textEdit = QTextEdit(MicrophoneDataSourceConfigWidget)
        self.textEdit.setObjectName(u"textEdit")
        self.textEdit.setGeometry(QRect(180, 40, 151, 41))
        self.textEdit_2 = QTextEdit(MicrophoneDataSourceConfigWidget)
        self.textEdit_2.setObjectName(u"textEdit_2")
        self.textEdit_2.setGeometry(QRect(180, 90, 151, 41))
        self.packetSizeTextField = QLineEdit(MicrophoneDataSourceConfigWidget)
        self.packetSizeTextField.setObjectName(u"packetSizeTextField")
        self.packetSizeTextField.setGeometry(QRect(30, 100, 113, 28))

        self.retranslateUi(MicrophoneDataSourceConfigWidget)

        QMetaObject.connectSlotsByName(MicrophoneDataSourceConfigWidget)
    # setupUi

    def retranslateUi(self, MicrophoneDataSourceConfigWidget):
        MicrophoneDataSourceConfigWidget.setWindowTitle(QCoreApplication.translate("MicrophoneDataSourceConfigWidget", u"Form", None))
        self.sampleRateTextField.setText("")
        self.textEdit.setHtml(QCoreApplication.translate("MicrophoneDataSourceConfigWidget", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Input frequency</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.textEdit_2.setHtml(QCoreApplication.translate("MicrophoneDataSourceConfigWidget", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Input packet size</p></body></html>", None))
        self.packetSizeTextField.setText("")
    # retranslateUi

