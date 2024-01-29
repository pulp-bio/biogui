# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'svm_train_config.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)
from . import resources_rc

class Ui_SVMTrainConfig(object):
    def setupUi(self, SVMTrainConfig):
        if not SVMTrainConfig.objectName():
            SVMTrainConfig.setObjectName(u"SVMTrainConfig")
        SVMTrainConfig.resize(400, 480)
        self.verticalLayout = QVBoxLayout(SVMTrainConfig)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.svmGroupBox = QGroupBox(SVMTrainConfig)
        self.svmGroupBox.setObjectName(u"svmGroupBox")
        self.svmGroupBox.setAlignment(Qt.AlignCenter)
        self.svmGroupBox.setCheckable(False)
        self.svmGroupBox.setChecked(False)
        self.verticalLayout_2 = QVBoxLayout(self.svmGroupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.formLayout1 = QFormLayout()
        self.formLayout1.setObjectName(u"formLayout1")
        self.label1 = QLabel(self.svmGroupBox)
        self.label1.setObjectName(u"label1")

        self.formLayout1.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.featureComboBox = QComboBox(self.svmGroupBox)
        self.featureComboBox.addItem("")
        self.featureComboBox.addItem("")
        self.featureComboBox.setObjectName(u"featureComboBox")

        self.formLayout1.setWidget(0, QFormLayout.FieldRole, self.featureComboBox)

        self.label2 = QLabel(self.svmGroupBox)
        self.label2.setObjectName(u"label2")

        self.formLayout1.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.winSizeTextField = QLineEdit(self.svmGroupBox)
        self.winSizeTextField.setObjectName(u"winSizeTextField")

        self.formLayout1.setWidget(1, QFormLayout.FieldRole, self.winSizeTextField)

        self.fsTextField = QLineEdit(self.svmGroupBox)
        self.fsTextField.setObjectName(u"fsTextField")

        self.formLayout1.setWidget(2, QFormLayout.FieldRole, self.fsTextField)

        self.label4 = QLabel(self.svmGroupBox)
        self.label4.setObjectName(u"label4")

        self.formLayout1.setWidget(3, QFormLayout.LabelRole, self.label4)

        self.kernelComboBox = QComboBox(self.svmGroupBox)
        self.kernelComboBox.addItem("")
        self.kernelComboBox.addItem("")
        self.kernelComboBox.addItem("")
        self.kernelComboBox.addItem("")
        self.kernelComboBox.setObjectName(u"kernelComboBox")

        self.formLayout1.setWidget(3, QFormLayout.FieldRole, self.kernelComboBox)

        self.label5 = QLabel(self.svmGroupBox)
        self.label5.setObjectName(u"label5")

        self.formLayout1.setWidget(4, QFormLayout.LabelRole, self.label5)

        self.cTextField = QLineEdit(self.svmGroupBox)
        self.cTextField.setObjectName(u"cTextField")

        self.formLayout1.setWidget(4, QFormLayout.FieldRole, self.cTextField)

        self.label6 = QLabel(self.svmGroupBox)
        self.label6.setObjectName(u"label6")

        self.formLayout1.setWidget(5, QFormLayout.LabelRole, self.label6)

        self.outModelTextField = QLineEdit(self.svmGroupBox)
        self.outModelTextField.setObjectName(u"outModelTextField")

        self.formLayout1.setWidget(5, QFormLayout.FieldRole, self.outModelTextField)

        self.label7 = QLabel(self.svmGroupBox)
        self.label7.setObjectName(u"label7")

        self.formLayout1.setWidget(6, QFormLayout.LabelRole, self.label7)

        self.browseTrainDataButton = QPushButton(self.svmGroupBox)
        self.browseTrainDataButton.setObjectName(u"browseTrainDataButton")

        self.formLayout1.setWidget(6, QFormLayout.FieldRole, self.browseTrainDataButton)

        self.label8 = QLabel(self.svmGroupBox)
        self.label8.setObjectName(u"label8")

        self.formLayout1.setWidget(7, QFormLayout.LabelRole, self.label8)

        self.trainDataPathLabel = QLabel(self.svmGroupBox)
        self.trainDataPathLabel.setObjectName(u"trainDataPathLabel")

        self.formLayout1.setWidget(7, QFormLayout.FieldRole, self.trainDataPathLabel)

        self.label3 = QLabel(self.svmGroupBox)
        self.label3.setObjectName(u"label3")

        self.formLayout1.setWidget(2, QFormLayout.LabelRole, self.label3)


        self.verticalLayout_2.addLayout(self.formLayout1)

        self.progressLabel = QLabel(self.svmGroupBox)
        self.progressLabel.setObjectName(u"progressLabel")
        self.progressLabel.setMinimumSize(QSize(0, 0))
        self.progressLabel.setMaximumSize(QSize(400, 200))
        self.progressLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.progressLabel)

        self.startTrainButton = QPushButton(self.svmGroupBox)
        self.startTrainButton.setObjectName(u"startTrainButton")

        self.verticalLayout_2.addWidget(self.startTrainButton)

        self.formLayout2 = QFormLayout()
        self.formLayout2.setObjectName(u"formLayout2")
        self.label9 = QLabel(self.svmGroupBox)
        self.label9.setObjectName(u"label9")

        self.formLayout2.setWidget(0, QFormLayout.LabelRole, self.label9)

        self.accLabel = QLabel(self.svmGroupBox)
        self.accLabel.setObjectName(u"accLabel")

        self.formLayout2.setWidget(0, QFormLayout.FieldRole, self.accLabel)


        self.verticalLayout_2.addLayout(self.formLayout2)


        self.verticalLayout.addWidget(self.svmGroupBox)


        self.retranslateUi(SVMTrainConfig)

        QMetaObject.connectSlotsByName(SVMTrainConfig)
    # setupUi

    def retranslateUi(self, SVMTrainConfig):
        SVMTrainConfig.setWindowTitle(QCoreApplication.translate("SVMTrainConfig", u"SVM Widget", None))
        self.svmGroupBox.setTitle(QCoreApplication.translate("SVMTrainConfig", u"SVM training", None))
        self.label1.setText(QCoreApplication.translate("SVMTrainConfig", u"Feature selection:", None))
        self.featureComboBox.setItemText(0, QCoreApplication.translate("SVMTrainConfig", u"Waveform length", None))
        self.featureComboBox.setItemText(1, QCoreApplication.translate("SVMTrainConfig", u"RMS", None))

        self.label2.setText(QCoreApplication.translate("SVMTrainConfig", u"Window size (ms):", None))
#if QT_CONFIG(tooltip)
        self.winSizeTextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.winSizeTextField.setPlaceholderText("")
        self.label4.setText(QCoreApplication.translate("SVMTrainConfig", u"Kernel selection:", None))
        self.kernelComboBox.setItemText(0, QCoreApplication.translate("SVMTrainConfig", u"rbf", None))
        self.kernelComboBox.setItemText(1, QCoreApplication.translate("SVMTrainConfig", u"linear", None))
        self.kernelComboBox.setItemText(2, QCoreApplication.translate("SVMTrainConfig", u"poly", None))
        self.kernelComboBox.setItemText(3, QCoreApplication.translate("SVMTrainConfig", u"sigmoid", None))

        self.label5.setText(QCoreApplication.translate("SVMTrainConfig", u"C selection:", None))
#if QT_CONFIG(tooltip)
        self.cTextField.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.cTextField.setText("")
        self.cTextField.setPlaceholderText("")
        self.label6.setText(QCoreApplication.translate("SVMTrainConfig", u"Output file name:", None))
#if QT_CONFIG(tooltip)
        self.outModelTextField.setToolTip(QCoreApplication.translate("SVMTrainConfig", u"If no name is provided, one based on the timestamp will be used", None))
#endif // QT_CONFIG(tooltip)
        self.label7.setText(QCoreApplication.translate("SVMTrainConfig", u"Training data:", None))
        self.browseTrainDataButton.setText(QCoreApplication.translate("SVMTrainConfig", u"Browse", None))
        self.label8.setText(QCoreApplication.translate("SVMTrainConfig", u"Path to training data:", None))
        self.trainDataPathLabel.setText("")
        self.label3.setText(QCoreApplication.translate("SVMTrainConfig", u"Sampling frequency:", None))
        self.progressLabel.setText("")
        self.startTrainButton.setText(QCoreApplication.translate("SVMTrainConfig", u"Start training", None))
        self.label9.setText(QCoreApplication.translate("SVMTrainConfig", u"Accuracy:", None))
        self.accLabel.setText("")
    # retranslateUi

