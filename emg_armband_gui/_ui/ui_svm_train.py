# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'svm_train.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

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
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class Ui_SVMTrain(object):
    def setupUi(self, SVMTrain):
        if not SVMTrain.objectName():
            SVMTrain.setObjectName("SVMTrain")
        SVMTrain.resize(531, 488)
        self.verticalLayout = QVBoxLayout(SVMTrain)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.featureComboBox = QComboBox(SVMTrain)
        self.featureComboBox.addItem("")
        self.featureComboBox.setObjectName("featureComboBox")

        self.gridLayout.addWidget(self.featureComboBox, 0, 1, 1, 1)

        self.label = QLabel(SVMTrain)
        self.label.setObjectName("label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.label_2 = QLabel(SVMTrain)
        self.label_2.setObjectName("label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.kernelComboBox = QComboBox(SVMTrain)
        self.kernelComboBox.addItem("")
        self.kernelComboBox.addItem("")
        self.kernelComboBox.addItem("")
        self.kernelComboBox.addItem("")
        self.kernelComboBox.setObjectName("kernelComboBox")

        self.gridLayout.addWidget(self.kernelComboBox, 1, 1, 1, 1)

        self.label_3 = QLabel(SVMTrain)
        self.label_3.setObjectName("label_3")

        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)

        self.cTextField = QLineEdit(SVMTrain)
        self.cTextField.setObjectName("cTextField")

        self.gridLayout.addWidget(self.cTextField, 2, 1, 1, 1)

        self.verticalLayout.addLayout(self.gridLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.startButton = QPushButton(SVMTrain)
        self.startButton.setObjectName("startButton")

        self.horizontalLayout.addWidget(self.startButton)

        self.horizontalSpacer_2 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.progressLabel = QLabel(SVMTrain)
        self.progressLabel.setObjectName("progressLabel")

        self.verticalLayout.addWidget(self.progressLabel)

        self.label_4 = QLabel(SVMTrain)
        self.label_4.setObjectName("label_4")

        self.verticalLayout.addWidget(self.label_4)

        self.trainAcc = QLabel(SVMTrain)
        self.trainAcc.setObjectName("trainAcc")

        self.verticalLayout.addWidget(self.trainAcc)

        self.testButton = QPushButton(SVMTrain)
        self.testButton.setObjectName("testButton")
        self.testButton.setEnabled(True)

        self.verticalLayout.addWidget(self.testButton)

        self.verticalLayout.setStretch(0, 3)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(SVMTrain)

        QMetaObject.connectSlotsByName(SVMTrain)

    # setupUi

    def retranslateUi(self, SVMTrain):
        SVMTrain.setWindowTitle(
            QCoreApplication.translate("SVMTrain", "SVM training", None)
        )
        self.featureComboBox.setItemText(
            0, QCoreApplication.translate("SVMTrain", "Waveform length", None)
        )

        self.label.setText(
            QCoreApplication.translate("SVMTrain", "Feature selection:", None)
        )
        self.label_2.setText(
            QCoreApplication.translate("SVMTrain", "Kernel selection:", None)
        )
        self.kernelComboBox.setItemText(
            0, QCoreApplication.translate("SVMTrain", "rbf", None)
        )
        self.kernelComboBox.setItemText(
            1, QCoreApplication.translate("SVMTrain", "linear", None)
        )
        self.kernelComboBox.setItemText(
            2, QCoreApplication.translate("SVMTrain", "poly", None)
        )
        self.kernelComboBox.setItemText(
            3, QCoreApplication.translate("SVMTrain", "sigmoid", None)
        )

        self.label_3.setText(
            QCoreApplication.translate("SVMTrain", "C selection:", None)
        )
        self.startButton.setText(QCoreApplication.translate("SVMTrain", "Start", None))
        self.progressLabel.setText("")
        self.label_4.setText(
            QCoreApplication.translate("SVMTrain", "Train accuracy:", None)
        )
        self.trainAcc.setText("")
        self.testButton.setText(
            QCoreApplication.translate("SVMTrain", "Test it!", None)
        )

    # retranslateUi