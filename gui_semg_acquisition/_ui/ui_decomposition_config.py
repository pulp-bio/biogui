# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'decomposition_config.ui'
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
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Ui_DecompositionConfig(object):
    def setupUi(self, DecompositionConfig):
        if not DecompositionConfig.objectName():
            DecompositionConfig.setObjectName("DecompositionConfig")
        DecompositionConfig.resize(400, 394)
        self.verticalLayout = QVBoxLayout(DecompositionConfig)
        self.verticalLayout.setObjectName("verticalLayout")
        self.decompGroupBox = QGroupBox(DecompositionConfig)
        self.decompGroupBox.setObjectName("decompGroupBox")
        self.decompGroupBox.setAlignment(Qt.AlignCenter)
        self.decompGroupBox.setCheckable(True)
        self.decompGroupBox.setChecked(False)
        self.verticalLayout_2 = QVBoxLayout(self.decompGroupBox)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.gammaTextField = QLineEdit(self.decompGroupBox)
        self.gammaTextField.setObjectName("gammaTextField")

        self.gridLayout.addWidget(self.gammaTextField, 1, 1, 1, 1)

        self.label1 = QLabel(self.decompGroupBox)
        self.label1.setObjectName("label1")

        self.gridLayout.addWidget(self.label1, 0, 0, 1, 1)

        self.label2 = QLabel(self.decompGroupBox)
        self.label2.setObjectName("label2")

        self.gridLayout.addWidget(self.label2, 1, 0, 1, 1)

        self.browseDecompModelButton = QPushButton(self.decompGroupBox)
        self.browseDecompModelButton.setObjectName("browseDecompModelButton")

        self.gridLayout.addWidget(self.browseDecompModelButton, 2, 1, 1, 1)

        self.label3 = QLabel(self.decompGroupBox)
        self.label3.setObjectName("label3")

        self.gridLayout.addWidget(self.label3, 2, 0, 1, 1)

        self.lambdaTextField = QLineEdit(self.decompGroupBox)
        self.lambdaTextField.setObjectName("lambdaTextField")

        self.gridLayout.addWidget(self.lambdaTextField, 0, 1, 1, 1)

        self.verticalLayout_2.addLayout(self.gridLayout)

        self.decompModelLabel = QLabel(self.decompGroupBox)
        self.decompModelLabel.setObjectName("decompModelLabel")

        self.verticalLayout_2.addWidget(self.decompModelLabel)

        self.verticalLayout.addWidget(self.decompGroupBox)

        self.retranslateUi(DecompositionConfig)

        QMetaObject.connectSlotsByName(DecompositionConfig)

    # setupUi

    def retranslateUi(self, DecompositionConfig):
        DecompositionConfig.setWindowTitle(
            QCoreApplication.translate(
                "DecompositionConfig", "Decomposition Widget", None
            )
        )
        self.decompGroupBox.setTitle(
            QCoreApplication.translate("DecompositionConfig", "Decomposition", None)
        )
        # if QT_CONFIG(tooltip)
        self.gammaTextField.setToolTip(
            QCoreApplication.translate(
                "DecompositionConfig",
                "If a non-numeric value is set, the default value will be used",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.gammaTextField.setPlaceholderText(
            QCoreApplication.translate("DecompositionConfig", "0.0", None)
        )
        self.label1.setText(
            QCoreApplication.translate(
                "DecompositionConfig", "Initial forgetting factor:", None
            )
        )
        self.label2.setText(
            QCoreApplication.translate("DecompositionConfig", "Decaying factor:", None)
        )
        self.browseDecompModelButton.setText(
            QCoreApplication.translate("DecompositionConfig", "Browse", None)
        )
        self.label3.setText(
            QCoreApplication.translate(
                "DecompositionConfig", "Decomposition model:", None
            )
        )
        self.lambdaTextField.setPlaceholderText(
            QCoreApplication.translate("DecompositionConfig", "0.001", None)
        )
        self.decompModelLabel.setText("")

    # retranslateUi
