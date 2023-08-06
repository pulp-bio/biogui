# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'svm_train_config.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
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
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import resources_rc


class Ui_SVMTrainConfig(object):
    def setupUi(self, SVMTrainConfig):
        if not SVMTrainConfig.objectName():
            SVMTrainConfig.setObjectName("SVMTrainConfig")
        SVMTrainConfig.resize(500, 600)
        self.verticalLayout = QVBoxLayout(SVMTrainConfig)
        self.verticalLayout.setObjectName("verticalLayout")
        self.svmGroupBox = QGroupBox(SVMTrainConfig)
        self.svmGroupBox.setObjectName("svmGroupBox")
        self.svmGroupBox.setAlignment(Qt.AlignCenter)
        self.svmGroupBox.setCheckable(False)
        self.svmGroupBox.setChecked(False)
        self.verticalLayout_4 = QVBoxLayout(self.svmGroupBox)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label1 = QLabel(self.svmGroupBox)
        self.label1.setObjectName("label1")

        self.gridLayout_2.addWidget(self.label1, 0, 0, 1, 1)

        self.label6 = QLabel(self.svmGroupBox)
        self.label6.setObjectName("label6")

        self.gridLayout_2.addWidget(self.label6, 5, 0, 1, 1)

        self.outModelTextField = QLineEdit(self.svmGroupBox)
        self.outModelTextField.setObjectName("outModelTextField")

        self.gridLayout_2.addWidget(self.outModelTextField, 4, 1, 1, 1)

        self.kernelComboBox = QComboBox(self.svmGroupBox)
        self.kernelComboBox.addItem("")
        self.kernelComboBox.addItem("")
        self.kernelComboBox.addItem("")
        self.kernelComboBox.addItem("")
        self.kernelComboBox.setObjectName("kernelComboBox")

        self.gridLayout_2.addWidget(self.kernelComboBox, 2, 1, 1, 1)

        self.label5 = QLabel(self.svmGroupBox)
        self.label5.setObjectName("label5")

        self.gridLayout_2.addWidget(self.label5, 4, 0, 1, 1)

        self.label3 = QLabel(self.svmGroupBox)
        self.label3.setObjectName("label3")

        self.gridLayout_2.addWidget(self.label3, 2, 0, 1, 1)

        self.featureComboBox = QComboBox(self.svmGroupBox)
        self.featureComboBox.addItem("")
        self.featureComboBox.addItem("")
        self.featureComboBox.setObjectName("featureComboBox")

        self.gridLayout_2.addWidget(self.featureComboBox, 0, 1, 1, 1)

        self.cTextField = QLineEdit(self.svmGroupBox)
        self.cTextField.setObjectName("cTextField")

        self.gridLayout_2.addWidget(self.cTextField, 3, 1, 1, 1)

        self.browseTrainDataButton = QPushButton(self.svmGroupBox)
        self.browseTrainDataButton.setObjectName("browseTrainDataButton")

        self.gridLayout_2.addWidget(self.browseTrainDataButton, 5, 1, 1, 1)

        self.label4 = QLabel(self.svmGroupBox)
        self.label4.setObjectName("label4")

        self.gridLayout_2.addWidget(self.label4, 3, 0, 1, 1)

        self.label2 = QLabel(self.svmGroupBox)
        self.label2.setObjectName("label2")

        self.gridLayout_2.addWidget(self.label2, 1, 0, 1, 1)

        self.winTextField = QLineEdit(self.svmGroupBox)
        self.winTextField.setObjectName("winTextField")

        self.gridLayout_2.addWidget(self.winTextField, 1, 1, 1, 1)

        self.gridLayout_2.setColumnStretch(0, 2)
        self.gridLayout_2.setColumnStretch(1, 1)

        self.verticalLayout_4.addLayout(self.gridLayout_2)

        self.trainDataLabel = QLabel(self.svmGroupBox)
        self.trainDataLabel.setObjectName("trainDataLabel")

        self.verticalLayout_4.addWidget(self.trainDataLabel)

        self.progressLabel = QLabel(self.svmGroupBox)
        self.progressLabel.setObjectName("progressLabel")
        self.progressLabel.setMinimumSize(QSize(400, 200))
        self.progressLabel.setMaximumSize(QSize(400, 200))
        self.progressLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.progressLabel)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.accLabel = QLabel(self.svmGroupBox)
        self.accLabel.setObjectName("accLabel")

        self.gridLayout.addWidget(self.accLabel, 0, 1, 1, 1)

        self.label7 = QLabel(self.svmGroupBox)
        self.label7.setObjectName("label7")

        self.gridLayout.addWidget(self.label7, 0, 0, 1, 1)

        self.verticalLayout_4.addLayout(self.gridLayout)

        self.startTrainButton = QPushButton(self.svmGroupBox)
        self.startTrainButton.setObjectName("startTrainButton")

        self.verticalLayout_4.addWidget(self.startTrainButton)

        self.verticalLayout_4.setStretch(0, 4)
        self.verticalLayout_4.setStretch(2, 4)

        self.verticalLayout.addWidget(self.svmGroupBox)

        self.retranslateUi(SVMTrainConfig)

        QMetaObject.connectSlotsByName(SVMTrainConfig)

    # setupUi

    def retranslateUi(self, SVMTrainConfig):
        SVMTrainConfig.setWindowTitle(
            QCoreApplication.translate("SVMTrainConfig", "SVM Widget", None)
        )
        self.svmGroupBox.setTitle(
            QCoreApplication.translate("SVMTrainConfig", "SVM", None)
        )
        self.label1.setText(
            QCoreApplication.translate("SVMTrainConfig", "Feature selection:", None)
        )
        self.label6.setText(
            QCoreApplication.translate("SVMTrainConfig", "Training data:", None)
        )
        # if QT_CONFIG(tooltip)
        self.outModelTextField.setToolTip(
            QCoreApplication.translate(
                "SVMTrainConfig",
                "If no name is provided, one based on the timestamp will be used",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.kernelComboBox.setItemText(
            0, QCoreApplication.translate("SVMTrainConfig", "rbf", None)
        )
        self.kernelComboBox.setItemText(
            1, QCoreApplication.translate("SVMTrainConfig", "linear", None)
        )
        self.kernelComboBox.setItemText(
            2, QCoreApplication.translate("SVMTrainConfig", "poly", None)
        )
        self.kernelComboBox.setItemText(
            3, QCoreApplication.translate("SVMTrainConfig", "sigmoid", None)
        )

        self.label5.setText(
            QCoreApplication.translate("SVMTrainConfig", "Output file name:", None)
        )
        self.label3.setText(
            QCoreApplication.translate("SVMTrainConfig", "Kernel selection:", None)
        )
        self.featureComboBox.setItemText(
            0, QCoreApplication.translate("SVMTrainConfig", "Waveform length", None)
        )
        self.featureComboBox.setItemText(
            1, QCoreApplication.translate("SVMTrainConfig", "RMS", None)
        )

        # if QT_CONFIG(tooltip)
        self.cTextField.setToolTip(
            QCoreApplication.translate(
                "SVMTrainConfig",
                "If a non-numeric value is set, the default value will be used",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.cTextField.setText("")
        self.cTextField.setPlaceholderText(
            QCoreApplication.translate("SVMTrainConfig", "1.0", None)
        )
        self.browseTrainDataButton.setText(
            QCoreApplication.translate("SVMTrainConfig", "Browse", None)
        )
        self.label4.setText(
            QCoreApplication.translate("SVMTrainConfig", "C selection:", None)
        )
        self.label2.setText(
            QCoreApplication.translate("SVMTrainConfig", "Window size (ms):", None)
        )
        # if QT_CONFIG(tooltip)
        self.winTextField.setToolTip(
            QCoreApplication.translate(
                "SVMTrainConfig",
                "If a non-numeric value is set, the default value will be used",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.winTextField.setPlaceholderText(
            QCoreApplication.translate("SVMTrainConfig", "100", None)
        )
        self.trainDataLabel.setText("")
        self.progressLabel.setText("")
        self.accLabel.setText("")
        self.label7.setText(
            QCoreApplication.translate("SVMTrainConfig", "Accuracy:", None)
        )
        self.startTrainButton.setText(
            QCoreApplication.translate("SVMTrainConfig", "Start training", None)
        )

    # retranslateUi
