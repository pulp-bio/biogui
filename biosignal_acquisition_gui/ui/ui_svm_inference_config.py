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
        self.formLayout = QFormLayout(self.svmGroupBox)
        self.formLayout.setObjectName(u"formLayout")
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

        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout)

        self.label4 = QLabel(self.svmGroupBox)
        self.label4.setObjectName(u"label4")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label4)

        self.label1 = QLabel(self.svmGroupBox)
        self.label1.setObjectName(u"label1")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label1)

        self.label2 = QLabel(self.svmGroupBox)
        self.label2.setObjectName(u"label2")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label2)

        self.featureComboBox = QComboBox(self.svmGroupBox)
        self.featureComboBox.addItem("")
        self.featureComboBox.addItem("")
        self.featureComboBox.setObjectName(u"featureComboBox")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.featureComboBox)

        self.browseModelButton = QPushButton(self.svmGroupBox)
        self.browseModelButton.setObjectName(u"browseModelButton")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.browseModelButton)

        self.label3 = QLabel(self.svmGroupBox)
        self.label3.setObjectName(u"label3")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label3)

        self.winTextField = QLineEdit(self.svmGroupBox)
        self.winTextField.setObjectName(u"winTextField")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.winTextField)

        self.svmModelPathLabel = QLabel(self.svmGroupBox)
        self.svmModelPathLabel.setObjectName(u"svmModelPathLabel")

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.svmModelPathLabel)

        self.label5 = QLabel(self.svmGroupBox)
        self.label5.setObjectName(u"label5")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label5)

        self.svmPredLabel = QLabel(self.svmGroupBox)
        self.svmPredLabel.setObjectName(u"svmPredLabel")

        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.svmPredLabel)

        self.label = QLabel(self.svmGroupBox)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(7, QFormLayout.LabelRole, self.label)


        self.verticalLayout.addWidget(self.svmGroupBox)


        self.retranslateUi(SVMInferenceConfig)

        QMetaObject.connectSlotsByName(SVMInferenceConfig)
    # setupUi

    def retranslateUi(self, SVMInferenceConfig):
        SVMInferenceConfig.setWindowTitle(QCoreApplication.translate("SVMInferenceConfig", u"SVM Inference Widget", None))
        self.svmGroupBox.setTitle(QCoreApplication.translate("SVMInferenceConfig", u"SVM inference", None))
#if QT_CONFIG(tooltip)
        self.rescanSignalsButton.setToolTip(QCoreApplication.translate("SVMInferenceConfig", u"Rescan signals", None))
#endif // QT_CONFIG(tooltip)
        self.rescanSignalsButton.setText("")
        self.label4.setText(QCoreApplication.translate("SVMInferenceConfig", u"SVM model:", None))
        self.label1.setText(QCoreApplication.translate("SVMInferenceConfig", u"Signal:", None))
        self.label2.setText(QCoreApplication.translate("SVMInferenceConfig", u"Feature selection:", None))
        self.featureComboBox.setItemText(0, QCoreApplication.translate("SVMInferenceConfig", u"Waveform length", None))
        self.featureComboBox.setItemText(1, QCoreApplication.translate("SVMInferenceConfig", u"RMS", None))

        self.browseModelButton.setText(QCoreApplication.translate("SVMInferenceConfig", u"Browse", None))
        self.label3.setText(QCoreApplication.translate("SVMInferenceConfig", u"Window size (ms):", None))
#if QT_CONFIG(tooltip)
        self.winTextField.setToolTip(QCoreApplication.translate("SVMInferenceConfig", u"If a non-numeric value is set, the default value will be used", None))
#endif // QT_CONFIG(tooltip)
        self.winTextField.setPlaceholderText(QCoreApplication.translate("SVMInferenceConfig", u"100", None))
        self.svmModelPathLabel.setText("")
        self.label5.setText(QCoreApplication.translate("SVMInferenceConfig", u"Path to SVM model:", None))
        self.svmPredLabel.setText("")
        self.label.setText(QCoreApplication.translate("SVMInferenceConfig", u"Predicted label:", None))
    # retranslateUi

