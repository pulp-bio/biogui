# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'add_source_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QLabel, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_AddSourceDialog(object):
    def setupUi(self, AddSourceDialog):
        if not AddSourceDialog.objectName():
            AddSourceDialog.setObjectName(u"AddSourceDialog")
        AddSourceDialog.resize(400, 200)
        self.verticalLayout = QVBoxLayout(AddSourceDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label1 = QLabel(AddSourceDialog)
        self.label1.setObjectName(u"label1")
        self.label1.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.sourceComboBox = QComboBox(AddSourceDialog)
        self.sourceComboBox.addItem("")
        self.sourceComboBox.addItem("")
        self.sourceComboBox.addItem("")
        self.sourceComboBox.setObjectName(u"sourceComboBox")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.sourceComboBox)


        self.verticalLayout.addLayout(self.formLayout)

        self.sourceConfContainer = QVBoxLayout()
        self.sourceConfContainer.setObjectName(u"sourceConfContainer")

        self.verticalLayout.addLayout(self.sourceConfContainer)

        self.buttonBox = QDialogButtonBox(AddSourceDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(AddSourceDialog)
        self.buttonBox.accepted.connect(AddSourceDialog.accept)
        self.buttonBox.rejected.connect(AddSourceDialog.reject)

        QMetaObject.connectSlotsByName(AddSourceDialog)
    # setupUi

    def retranslateUi(self, AddSourceDialog):
        AddSourceDialog.setWindowTitle(QCoreApplication.translate("AddSourceDialog", u"Add source", None))
        self.label1.setText(QCoreApplication.translate("AddSourceDialog", u"Source:", None))
        self.sourceComboBox.setItemText(0, QCoreApplication.translate("AddSourceDialog", u"Serial port", None))
        self.sourceComboBox.setItemText(1, QCoreApplication.translate("AddSourceDialog", u"Socket", None))
        self.sourceComboBox.setItemText(2, QCoreApplication.translate("AddSourceDialog", u"Dummy", None))

#if QT_CONFIG(tooltip)
        self.sourceComboBox.setToolTip(QCoreApplication.translate("AddSourceDialog", u"List of available serial ports", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

