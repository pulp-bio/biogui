# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'svm_inference_config.ui'
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


class Ui_SVMInferenceConfig(object):
    def setupUi(self, SVMInferenceConfig):
        if not SVMInferenceConfig.objectName():
            SVMInferenceConfig.setObjectName("SVMInferenceConfig")
        SVMInferenceConfig.resize(400, 394)
        self.verticalLayout = QVBoxLayout(SVMInferenceConfig)
        self.verticalLayout.setObjectName("verticalLayout")
        self.svmGroupBox = QGroupBox(SVMInferenceConfig)
        self.svmGroupBox.setObjectName("svmGroupBox")
        self.svmGroupBox.setAlignment(Qt.AlignCenter)
        self.svmGroupBox.setCheckable(False)
        self.svmGroupBox.setChecked(False)
        self.verticalLayout_2 = QVBoxLayout(self.svmGroupBox)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.winTextField = QLineEdit(self.svmGroupBox)
        self.winTextField.setObjectName("winTextField")

        self.gridLayout.addWidget(self.winTextField, 1, 1, 1, 1)

        self.label1 = QLabel(self.svmGroupBox)
        self.label1.setObjectName("label1")

        self.gridLayout.addWidget(self.label1, 0, 0, 1, 1)

        self.featureComboBox = QComboBox(self.svmGroupBox)
        self.featureComboBox.addItem("")
        self.featureComboBox.addItem("")
        self.featureComboBox.setObjectName("featureComboBox")

        self.gridLayout.addWidget(self.featureComboBox, 0, 1, 1, 1)

        self.label2 = QLabel(self.svmGroupBox)
        self.label2.setObjectName("label2")

        self.gridLayout.addWidget(self.label2, 1, 0, 1, 1)

        self.browseModelButton = QPushButton(self.svmGroupBox)
        self.browseModelButton.setObjectName("browseModelButton")

        self.gridLayout.addWidget(self.browseModelButton, 2, 1, 1, 1)

        self.label6 = QLabel(self.svmGroupBox)
        self.label6.setObjectName("label6")

        self.gridLayout.addWidget(self.label6, 2, 0, 1, 1)

        self.verticalLayout_2.addLayout(self.gridLayout)

        self.svmLabel = QLabel(self.svmGroupBox)
        self.svmLabel.setObjectName("svmLabel")

        self.verticalLayout_2.addWidget(self.svmLabel)

        self.verticalLayout.addWidget(self.svmGroupBox)

        self.retranslateUi(SVMInferenceConfig)

        QMetaObject.connectSlotsByName(SVMInferenceConfig)

    # setupUi

    def retranslateUi(self, SVMInferenceConfig):
        SVMInferenceConfig.setWindowTitle(
            QCoreApplication.translate(
                "SVMInferenceConfig", "SVM Inference Widget", None
            )
        )
        self.svmGroupBox.setTitle(
            QCoreApplication.translate("SVMInferenceConfig", "SVM Inference", None)
        )
        # if QT_CONFIG(tooltip)
        self.winTextField.setToolTip(
            QCoreApplication.translate(
                "SVMInferenceConfig",
                "If a non-numeric value is set, the default value will be used",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.winTextField.setPlaceholderText(
            QCoreApplication.translate("SVMInferenceConfig", "100", None)
        )
        self.label1.setText(
            QCoreApplication.translate("SVMInferenceConfig", "Feature selection:", None)
        )
        self.featureComboBox.setItemText(
            0, QCoreApplication.translate("SVMInferenceConfig", "Waveform length", None)
        )
        self.featureComboBox.setItemText(
            1, QCoreApplication.translate("SVMInferenceConfig", "RMS", None)
        )

        self.label2.setText(
            QCoreApplication.translate("SVMInferenceConfig", "Window size (ms):", None)
        )
        self.browseModelButton.setText(
            QCoreApplication.translate("SVMInferenceConfig", "Browse", None)
        )
        self.label6.setText(
            QCoreApplication.translate("SVMInferenceConfig", "SVM model:", None)
        )
        self.svmLabel.setText("")

    # retranslateUi
