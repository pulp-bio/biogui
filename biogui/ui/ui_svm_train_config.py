# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'svm_train_config.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
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
    QFormLayout,
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
        SVMTrainConfig.resize(400, 480)
        self.verticalLayout = QVBoxLayout(SVMTrainConfig)
        self.verticalLayout.setObjectName("verticalLayout")
        self.svmGroupBox = QGroupBox(SVMTrainConfig)
        self.svmGroupBox.setObjectName("svmGroupBox")
        self.svmGroupBox.setAlignment(Qt.AlignCenter)
        self.svmGroupBox.setCheckable(False)
        self.svmGroupBox.setChecked(False)
        self.verticalLayout_2 = QVBoxLayout(self.svmGroupBox)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.formLayout1 = QFormLayout()
        self.formLayout1.setObjectName("formLayout1")
        self.label1 = QLabel(self.svmGroupBox)
        self.label1.setObjectName("label1")

        self.formLayout1.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.featureComboBox = QComboBox(self.svmGroupBox)
        self.featureComboBox.addItem("")
        self.featureComboBox.addItem("")
        self.featureComboBox.setObjectName("featureComboBox")

        self.formLayout1.setWidget(0, QFormLayout.FieldRole, self.featureComboBox)

        self.label2 = QLabel(self.svmGroupBox)
        self.label2.setObjectName("label2")

        self.formLayout1.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.winSizeTextField = QLineEdit(self.svmGroupBox)
        self.winSizeTextField.setObjectName("winSizeTextField")

        self.formLayout1.setWidget(1, QFormLayout.FieldRole, self.winSizeTextField)

        self.fsTextField = QLineEdit(self.svmGroupBox)
        self.fsTextField.setObjectName("fsTextField")

        self.formLayout1.setWidget(2, QFormLayout.FieldRole, self.fsTextField)

        self.label4 = QLabel(self.svmGroupBox)
        self.label4.setObjectName("label4")

        self.formLayout1.setWidget(3, QFormLayout.LabelRole, self.label4)

        self.kernelComboBox = QComboBox(self.svmGroupBox)
        self.kernelComboBox.addItem("")
        self.kernelComboBox.addItem("")
        self.kernelComboBox.addItem("")
        self.kernelComboBox.addItem("")
        self.kernelComboBox.setObjectName("kernelComboBox")

        self.formLayout1.setWidget(3, QFormLayout.FieldRole, self.kernelComboBox)

        self.label5 = QLabel(self.svmGroupBox)
        self.label5.setObjectName("label5")

        self.formLayout1.setWidget(4, QFormLayout.LabelRole, self.label5)

        self.cTextField = QLineEdit(self.svmGroupBox)
        self.cTextField.setObjectName("cTextField")

        self.formLayout1.setWidget(4, QFormLayout.FieldRole, self.cTextField)

        self.label6 = QLabel(self.svmGroupBox)
        self.label6.setObjectName("label6")

        self.formLayout1.setWidget(5, QFormLayout.LabelRole, self.label6)

        self.outModelTextField = QLineEdit(self.svmGroupBox)
        self.outModelTextField.setObjectName("outModelTextField")

        self.formLayout1.setWidget(5, QFormLayout.FieldRole, self.outModelTextField)

        self.label7 = QLabel(self.svmGroupBox)
        self.label7.setObjectName("label7")

        self.formLayout1.setWidget(6, QFormLayout.LabelRole, self.label7)

        self.browseTrainDataButton = QPushButton(self.svmGroupBox)
        self.browseTrainDataButton.setObjectName("browseTrainDataButton")

        self.formLayout1.setWidget(6, QFormLayout.FieldRole, self.browseTrainDataButton)

        self.label8 = QLabel(self.svmGroupBox)
        self.label8.setObjectName("label8")

        self.formLayout1.setWidget(7, QFormLayout.LabelRole, self.label8)

        self.trainDataPathLabel = QLabel(self.svmGroupBox)
        self.trainDataPathLabel.setObjectName("trainDataPathLabel")

        self.formLayout1.setWidget(7, QFormLayout.FieldRole, self.trainDataPathLabel)

        self.label3 = QLabel(self.svmGroupBox)
        self.label3.setObjectName("label3")

        self.formLayout1.setWidget(2, QFormLayout.LabelRole, self.label3)

        self.verticalLayout_2.addLayout(self.formLayout1)

        self.progressLabel = QLabel(self.svmGroupBox)
        self.progressLabel.setObjectName("progressLabel")
        self.progressLabel.setMinimumSize(QSize(0, 0))
        self.progressLabel.setMaximumSize(QSize(400, 200))
        self.progressLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.progressLabel)

        self.startTrainButton = QPushButton(self.svmGroupBox)
        self.startTrainButton.setObjectName("startTrainButton")

        self.verticalLayout_2.addWidget(self.startTrainButton)

        self.formLayout2 = QFormLayout()
        self.formLayout2.setObjectName("formLayout2")
        self.label9 = QLabel(self.svmGroupBox)
        self.label9.setObjectName("label9")

        self.formLayout2.setWidget(0, QFormLayout.LabelRole, self.label9)

        self.accLabel = QLabel(self.svmGroupBox)
        self.accLabel.setObjectName("accLabel")

        self.formLayout2.setWidget(0, QFormLayout.FieldRole, self.accLabel)

        self.verticalLayout_2.addLayout(self.formLayout2)

        self.verticalLayout.addWidget(self.svmGroupBox)

        self.retranslateUi(SVMTrainConfig)

        QMetaObject.connectSlotsByName(SVMTrainConfig)

    # setupUi

    def retranslateUi(self, SVMTrainConfig):
        SVMTrainConfig.setWindowTitle(
            QCoreApplication.translate("SVMTrainConfig", "SVM Widget", None)
        )
        self.svmGroupBox.setTitle(
            QCoreApplication.translate("SVMTrainConfig", "SVM training", None)
        )
        self.label1.setText(
            QCoreApplication.translate("SVMTrainConfig", "Feature selection:", None)
        )
        self.featureComboBox.setItemText(
            0, QCoreApplication.translate("SVMTrainConfig", "Waveform length", None)
        )
        self.featureComboBox.setItemText(
            1, QCoreApplication.translate("SVMTrainConfig", "RMS", None)
        )

        self.label2.setText(
            QCoreApplication.translate("SVMTrainConfig", "Window size (ms):", None)
        )
        # if QT_CONFIG(tooltip)
        self.winSizeTextField.setToolTip("")
        # endif // QT_CONFIG(tooltip)
        self.winSizeTextField.setPlaceholderText("")
        self.label4.setText(
            QCoreApplication.translate("SVMTrainConfig", "Kernel selection:", None)
        )
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
            QCoreApplication.translate("SVMTrainConfig", "C selection:", None)
        )
        # if QT_CONFIG(tooltip)
        self.cTextField.setToolTip("")
        # endif // QT_CONFIG(tooltip)
        self.cTextField.setText("")
        self.cTextField.setPlaceholderText("")
        self.label6.setText(
            QCoreApplication.translate("SVMTrainConfig", "Output file name:", None)
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
        self.label7.setText(
            QCoreApplication.translate("SVMTrainConfig", "Training data:", None)
        )
        self.browseTrainDataButton.setText(
            QCoreApplication.translate("SVMTrainConfig", "Browse", None)
        )
        self.label8.setText(
            QCoreApplication.translate("SVMTrainConfig", "Path to training data:", None)
        )
        self.trainDataPathLabel.setText("")
        self.label3.setText(
            QCoreApplication.translate("SVMTrainConfig", "Sampling frequency:", None)
        )
        self.progressLabel.setText("")
        self.startTrainButton.setText(
            QCoreApplication.translate("SVMTrainConfig", "Start training", None)
        )
        self.label9.setText(
            QCoreApplication.translate("SVMTrainConfig", "Accuracy:", None)
        )
        self.accLabel.setText("")

    # retranslateUi
