# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'forwarding_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QGroupBox,
    QHeaderView, QLabel, QLineEdit, QSizePolicy,
    QTreeView, QVBoxLayout, QWidget)

class Ui_ForwardingConfigWidget(object):
    def setupUi(self, ForwardingConfigWidget):
        if not ForwardingConfigWidget.objectName():
            ForwardingConfigWidget.setObjectName(u"ForwardingConfigWidget")
        ForwardingConfigWidget.resize(400, 453)
        self.verticalLayout1 = QVBoxLayout(ForwardingConfigWidget)
        self.verticalLayout1.setObjectName(u"verticalLayout1")
        self.forwardGroupBox = QGroupBox(ForwardingConfigWidget)
        self.forwardGroupBox.setObjectName(u"forwardGroupBox")
        self.forwardGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verticalLayout2 = QVBoxLayout(self.forwardGroupBox)
        self.verticalLayout2.setObjectName(u"verticalLayout2")
        self.dataSourceTree = QTreeView(self.forwardGroupBox)
        self.dataSourceTree.setObjectName(u"dataSourceTree")

        self.verticalLayout2.addWidget(self.dataSourceTree)

        self.windowGroupBox = QGroupBox(self.forwardGroupBox)
        self.windowGroupBox.setObjectName(u"windowGroupBox")
        self.windowGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout1 = QFormLayout(self.windowGroupBox)
        self.formLayout1.setObjectName(u"formLayout1")
        self.label1 = QLabel(self.windowGroupBox)
        self.label1.setObjectName(u"label1")

        self.formLayout1.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label1)

        self.winLenTextField = QLineEdit(self.windowGroupBox)
        self.winLenTextField.setObjectName(u"winLenTextField")

        self.formLayout1.setWidget(0, QFormLayout.ItemRole.FieldRole, self.winLenTextField)

        self.label2 = QLabel(self.windowGroupBox)
        self.label2.setObjectName(u"label2")

        self.formLayout1.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label2)

        self.winStrideTextField = QLineEdit(self.windowGroupBox)
        self.winStrideTextField.setObjectName(u"winStrideTextField")

        self.formLayout1.setWidget(1, QFormLayout.ItemRole.FieldRole, self.winStrideTextField)


        self.verticalLayout2.addWidget(self.windowGroupBox)

        self.socketGroupBox = QGroupBox(self.forwardGroupBox)
        self.socketGroupBox.setObjectName(u"socketGroupBox")
        self.socketGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout2 = QFormLayout(self.socketGroupBox)
        self.formLayout2.setObjectName(u"formLayout2")
        self.label3 = QLabel(self.socketGroupBox)
        self.label3.setObjectName(u"label3")

        self.formLayout2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label3)

        self.socketTypeComboBox = QComboBox(self.socketGroupBox)
        self.socketTypeComboBox.addItem("")
        self.socketTypeComboBox.addItem("")
        self.socketTypeComboBox.setObjectName(u"socketTypeComboBox")

        self.formLayout2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.socketTypeComboBox)

        self.label4 = QLabel(self.socketGroupBox)
        self.label4.setObjectName(u"label4")

        self.formLayout2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label4)

        self.socketAddressTextField = QLineEdit(self.socketGroupBox)
        self.socketAddressTextField.setObjectName(u"socketAddressTextField")

        self.formLayout2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.socketAddressTextField)

        self.label5 = QLabel(self.socketGroupBox)
        self.label5.setObjectName(u"label5")
        self.label5.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label5)

        self.socketPortTextField = QLineEdit(self.socketGroupBox)
        self.socketPortTextField.setObjectName(u"socketPortTextField")

        self.formLayout2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.socketPortTextField)

        self.label6 = QLabel(self.socketGroupBox)
        self.label6.setObjectName(u"label6")
        self.label6.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout2.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label6)

        self.socketPathTextField = QLineEdit(self.socketGroupBox)
        self.socketPathTextField.setObjectName(u"socketPathTextField")

        self.formLayout2.setWidget(3, QFormLayout.ItemRole.FieldRole, self.socketPathTextField)


        self.verticalLayout2.addWidget(self.socketGroupBox)


        self.verticalLayout1.addWidget(self.forwardGroupBox)


        self.retranslateUi(ForwardingConfigWidget)

        QMetaObject.connectSlotsByName(ForwardingConfigWidget)
    # setupUi

    def retranslateUi(self, ForwardingConfigWidget):
        ForwardingConfigWidget.setWindowTitle(QCoreApplication.translate("ForwardingConfigWidget", u"Forwarding Configuration Widget", None))
        self.forwardGroupBox.setTitle(QCoreApplication.translate("ForwardingConfigWidget", u"Forwarding configuration", None))
        self.windowGroupBox.setTitle(QCoreApplication.translate("ForwardingConfigWidget", u"Window settings", None))
        self.label1.setText(QCoreApplication.translate("ForwardingConfigWidget", u"Window length (in ms):", None))
        self.label2.setText(QCoreApplication.translate("ForwardingConfigWidget", u"Window stride (in ms):", None))
        self.socketGroupBox.setTitle(QCoreApplication.translate("ForwardingConfigWidget", u"Socket settings", None))
        self.label3.setText(QCoreApplication.translate("ForwardingConfigWidget", u"Socket type:", None))
        self.socketTypeComboBox.setItemText(0, QCoreApplication.translate("ForwardingConfigWidget", u"TCP", None))
        self.socketTypeComboBox.setItemText(1, QCoreApplication.translate("ForwardingConfigWidget", u"Unix", None))

        self.label4.setText(QCoreApplication.translate("ForwardingConfigWidget", u"Socket address:", None))
        self.socketAddressTextField.setText(QCoreApplication.translate("ForwardingConfigWidget", u"127.0.0.1", None))
#if QT_CONFIG(tooltip)
        self.label5.setToolTip(QCoreApplication.translate("ForwardingConfigWidget", u"For the process to which the results will be sent", None))
#endif // QT_CONFIG(tooltip)
        self.label5.setText(QCoreApplication.translate("ForwardingConfigWidget", u"Socket port:", None))
        self.label6.setText(QCoreApplication.translate("ForwardingConfigWidget", u"Socket path:", None))
    # retranslateUi

