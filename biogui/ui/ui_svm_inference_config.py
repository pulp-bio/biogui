# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'svm_inference_config.ui'
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
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_SVMInferenceConfig(object):
    def setupUi(self, SVMInferenceConfig):
        if not SVMInferenceConfig.objectName():
            SVMInferenceConfig.setObjectName(u"SVMInferenceConfig")
        SVMInferenceConfig.resize(400, 394)
        self.verticalLayout = QVBoxLayout(SVMInferenceConfig)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.svmGroupBox = QGroupBox(SVMInferenceConfig)
        self.svmGroupBox.setObjectName(u"svmGroupBox")
        self.svmGroupBox.setAlignment(Qt.AlignCenter)
        self.svmGroupBox.setCheckable(True)
        self.svmGroupBox.setChecked(False)
        self.verticalLayout_2 = QVBoxLayout(self.svmGroupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.ubHandGroupBox = QGroupBox(self.svmGroupBox)
        self.ubHandGroupBox.setObjectName(u"ubHandGroupBox")
        self.ubHandGroupBox.setEnabled(False)
        self.ubHandGroupBox.setCheckable(True)
        self.formLayout_3 = QFormLayout(self.ubHandGroupBox)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label7 = QLabel(self.ubHandGroupBox)
        self.label7.setObjectName(u"label7")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label7)

        self.browseJSONButton = QPushButton(self.ubHandGroupBox)
        self.browseJSONButton.setObjectName(u"browseJSONButton")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.browseJSONButton)

        self.label8 = QLabel(self.ubHandGroupBox)
        self.label8.setObjectName(u"label8")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label8)

        self.mappingJSONPathLabel = QLabel(self.ubHandGroupBox)
        self.mappingJSONPathLabel.setObjectName(u"mappingJSONPathLabel")

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.mappingJSONPathLabel)


        self.verticalLayout_2.addWidget(self.ubHandGroupBox)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label1 = QLabel(self.svmGroupBox)
        self.label1.setObjectName(u"label1")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.signalComboBox = QComboBox(self.svmGroupBox)
        self.signalComboBox.setObjectName(u"signalComboBox")

        self.horizontalLayout.addWidget(self.signalComboBox)

        self.rescanSignalsButton = QPushButton(self.svmGroupBox)
        self.rescanSignalsButton.setObjectName(u"rescanSignalsButton")
        icon = QIcon()
        iconThemeName = u"view-refresh"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.rescanSignalsButton.setIcon(icon)

        self.horizontalLayout.addWidget(self.rescanSignalsButton)

        self.horizontalLayout.setStretch(0, 4)
        self.horizontalLayout.setStretch(1, 1)

        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout)

        self.label2 = QLabel(self.svmGroupBox)
        self.label2.setObjectName(u"label2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label2)

        self.featureComboBox = QComboBox(self.svmGroupBox)
        self.featureComboBox.addItem("")
        self.featureComboBox.addItem("")
        self.featureComboBox.setObjectName(u"featureComboBox")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.featureComboBox)

        self.label3 = QLabel(self.svmGroupBox)
        self.label3.setObjectName(u"label3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label3)

        self.winSizeTextField = QLineEdit(self.svmGroupBox)
        self.winSizeTextField.setObjectName(u"winSizeTextField")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.winSizeTextField)

        self.label4 = QLabel(self.svmGroupBox)
        self.label4.setObjectName(u"label4")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label4)

        self.browseModelButton = QPushButton(self.svmGroupBox)
        self.browseModelButton.setObjectName(u"browseModelButton")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.browseModelButton)

        self.label5 = QLabel(self.svmGroupBox)
        self.label5.setObjectName(u"label5")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label5)

        self.svmModelPathLabel = QLabel(self.svmGroupBox)
        self.svmModelPathLabel.setObjectName(u"svmModelPathLabel")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.svmModelPathLabel)


        self.verticalLayout_2.addLayout(self.formLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label6 = QLabel(self.svmGroupBox)
        self.label6.setObjectName(u"label6")

        self.horizontalLayout_2.addWidget(self.label6)

        self.svmPredLabel = QLabel(self.svmGroupBox)
        self.svmPredLabel.setObjectName(u"svmPredLabel")

        self.horizontalLayout_2.addWidget(self.svmPredLabel)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.verticalLayout.addWidget(self.svmGroupBox)


        self.retranslateUi(SVMInferenceConfig)

        QMetaObject.connectSlotsByName(SVMInferenceConfig)
    # setupUi

    def retranslateUi(self, SVMInferenceConfig):
        SVMInferenceConfig.setWindowTitle(QCoreApplication.translate("SVMInferenceConfig", u"SVM Inference Widget", None))
        self.svmGroupBox.setTitle(QCoreApplication.translate("SVMInferenceConfig", u"SVM inference", None))
        self.ubHandGroupBox.setTitle(QCoreApplication.translate("SVMInferenceConfig", u"Connect to UBHand", None))
        self.label7.setText(QCoreApplication.translate("SVMInferenceConfig", u"JSON with gesture mapping:", None))
        self.browseJSONButton.setText(QCoreApplication.translate("SVMInferenceConfig", u"Browse", None))
        self.label8.setText(QCoreApplication.translate("SVMInferenceConfig", u"Path to JSON:", None))
        self.mappingJSONPathLabel.setText("")
        self.label1.setText(QCoreApplication.translate("SVMInferenceConfig", u"Signal:", None))
#if QT_CONFIG(tooltip)
        self.rescanSignalsButton.setToolTip(QCoreApplication.translate("SVMInferenceConfig", u"Rescan signals", None))
#endif // QT_CONFIG(tooltip)
        self.rescanSignalsButton.setText("")
        self.label2.setText(QCoreApplication.translate("SVMInferenceConfig", u"Feature selection:", None))
        self.featureComboBox.setItemText(0, QCoreApplication.translate("SVMInferenceConfig", u"Waveform length", None))
        self.featureComboBox.setItemText(1, QCoreApplication.translate("SVMInferenceConfig", u"RMS", None))

        self.label3.setText(QCoreApplication.translate("SVMInferenceConfig", u"Window size (ms):", None))
#if QT_CONFIG(tooltip)
        self.winSizeTextField.setToolTip(QCoreApplication.translate("SVMInferenceConfig", u"If a non-numeric value is set, the default value will be used", None))
#endif // QT_CONFIG(tooltip)
        self.winSizeTextField.setPlaceholderText("")
        self.label4.setText(QCoreApplication.translate("SVMInferenceConfig", u"SVM model:", None))
        self.browseModelButton.setText(QCoreApplication.translate("SVMInferenceConfig", u"Browse", None))
        self.label5.setText(QCoreApplication.translate("SVMInferenceConfig", u"Path to SVM model:", None))
        self.svmModelPathLabel.setText("")
        self.label6.setText(QCoreApplication.translate("SVMInferenceConfig", u"Predicted label:", None))
        self.svmPredLabel.setText("")
    # retranslateUi

