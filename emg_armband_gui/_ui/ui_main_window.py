# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from pyqtgraph import PlotWidget
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
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from . import rc_resources


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1920, 1080)
        MainWindow.setMinimumSize(QSize(1080, 720))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.serialPortsGroupBox = QGroupBox(self.centralwidget)
        self.serialPortsGroupBox.setObjectName("serialPortsGroupBox")
        self.serialPortsGroupBox.setAlignment(Qt.AlignCenter)
        self.horizontalLayout_2 = QHBoxLayout(self.serialPortsGroupBox)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.serialPortsComboBox = QComboBox(self.serialPortsGroupBox)
        self.serialPortsComboBox.setObjectName("serialPortsComboBox")

        self.horizontalLayout_2.addWidget(self.serialPortsComboBox)

        self.rescanSerialPortsButton = QPushButton(self.serialPortsGroupBox)
        self.rescanSerialPortsButton.setObjectName("rescanSerialPortsButton")

        self.horizontalLayout_2.addWidget(self.rescanSerialPortsButton)

        self.horizontalLayout_2.setStretch(0, 3)
        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout.addWidget(self.serialPortsGroupBox)

        self.channelsGroupBox = QGroupBox(self.centralwidget)
        self.channelsGroupBox.setObjectName("channelsGroupBox")
        self.channelsGroupBox.setAlignment(Qt.AlignCenter)
        self.verticalLayout_2 = QVBoxLayout(self.channelsGroupBox)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.ch16RadioButton = QRadioButton(self.channelsGroupBox)
        self.ch16RadioButton.setObjectName("ch16RadioButton")
        self.ch16RadioButton.setChecked(True)

        self.verticalLayout_2.addWidget(self.ch16RadioButton)

        self.ch32RadioButton = QRadioButton(self.channelsGroupBox)
        self.ch32RadioButton.setObjectName("ch32RadioButton")
        self.ch32RadioButton.setCheckable(True)

        self.verticalLayout_2.addWidget(self.ch32RadioButton)

        self.ch64RadioButton = QRadioButton(self.channelsGroupBox)
        self.ch64RadioButton.setObjectName("ch64RadioButton")
        self.ch64RadioButton.setCheckable(True)

        self.verticalLayout_2.addWidget(self.ch64RadioButton)

        self.verticalLayout.addWidget(self.channelsGroupBox)

        self.experimentGroupBox = QGroupBox(self.centralwidget)
        self.experimentGroupBox.setObjectName("experimentGroupBox")
        self.experimentGroupBox.setAlignment(Qt.AlignCenter)
        self.experimentGroupBox.setCheckable(True)
        self.experimentGroupBox.setChecked(False)
        self.verticalLayout_3 = QVBoxLayout(self.experimentGroupBox)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QLabel(self.experimentGroupBox)
        self.label.setObjectName("label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.experimentTextField = QLineEdit(self.experimentGroupBox)
        self.experimentTextField.setObjectName("experimentTextField")

        self.gridLayout.addWidget(self.experimentTextField, 0, 1, 1, 1)

        self.label_2 = QLabel(self.experimentGroupBox)
        self.label_2.setObjectName("label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.browseJSONButton = QPushButton(self.experimentGroupBox)
        self.browseJSONButton.setObjectName("browseJSONButton")

        self.gridLayout.addWidget(self.browseJSONButton, 1, 1, 1, 1)

        self.gridLayout.setColumnStretch(0, 2)
        self.gridLayout.setColumnStretch(1, 1)

        self.verticalLayout_3.addLayout(self.gridLayout)

        self.JSONLabel = QLabel(self.experimentGroupBox)
        self.JSONLabel.setObjectName("JSONLabel")

        self.verticalLayout_3.addWidget(self.JSONLabel)

        self.verticalLayout.addWidget(self.experimentGroupBox)

        self.trainingGroupBox = QGroupBox(self.centralwidget)
        self.trainingGroupBox.setObjectName("trainingGroupBox")
        self.trainingGroupBox.setAlignment(Qt.AlignCenter)
        self.trainingGroupBox.setCheckable(False)
        self.trainingGroupBox.setChecked(False)
        self.verticalLayout_4 = QVBoxLayout(self.trainingGroupBox)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.svmRadioButton = QRadioButton(self.trainingGroupBox)
        self.svmRadioButton.setObjectName("svmRadioButton")
        self.svmRadioButton.setChecked(True)

        self.verticalLayout_4.addWidget(self.svmRadioButton)

        self.bssRadioButton = QRadioButton(self.trainingGroupBox)
        self.bssRadioButton.setObjectName("bssRadioButton")
        self.bssRadioButton.setCheckable(False)

        self.verticalLayout_4.addWidget(self.bssRadioButton)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.trainingTextField = QLineEdit(self.trainingGroupBox)
        self.trainingTextField.setObjectName("trainingTextField")

        self.gridLayout_2.addWidget(self.trainingTextField, 0, 1, 1, 1)

        self.label_3 = QLabel(self.trainingGroupBox)
        self.label_3.setObjectName("label_3")

        self.gridLayout_2.addWidget(self.label_3, 0, 0, 1, 1)

        self.label_4 = QLabel(self.trainingGroupBox)
        self.label_4.setObjectName("label_4")

        self.gridLayout_2.addWidget(self.label_4, 1, 0, 1, 1)

        self.browseTrainButton = QPushButton(self.trainingGroupBox)
        self.browseTrainButton.setObjectName("browseTrainButton")

        self.gridLayout_2.addWidget(self.browseTrainButton, 1, 1, 1, 1)

        self.gridLayout_2.setColumnStretch(0, 2)
        self.gridLayout_2.setColumnStretch(1, 1)

        self.verticalLayout_4.addLayout(self.gridLayout_2)

        self.trainLabel = QLabel(self.trainingGroupBox)
        self.trainLabel.setObjectName("trainLabel")

        self.verticalLayout_4.addWidget(self.trainLabel)

        self.startTrainButton = QPushButton(self.trainingGroupBox)
        self.startTrainButton.setObjectName("startTrainButton")

        self.verticalLayout_4.addWidget(self.startTrainButton)

        self.verticalLayout.addWidget(self.trainingGroupBox)

        self.verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.startAcquisitionButton = QPushButton(self.centralwidget)
        self.startAcquisitionButton.setObjectName("startAcquisitionButton")

        self.horizontalLayout_5.addWidget(self.startAcquisitionButton)

        self.stopAcquisitionButton = QPushButton(self.centralwidget)
        self.stopAcquisitionButton.setObjectName("stopAcquisitionButton")

        self.horizontalLayout_5.addWidget(self.stopAcquisitionButton)

        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.graphWidget = PlotWidget(self.centralwidget)
        self.graphWidget.setObjectName("graphWidget")

        self.horizontalLayout.addWidget(self.graphWidget)

        self.horizontalLayout.setStretch(1, 3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 1920, 30))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", "sEMG Acquisition GUI", None)
        )
        self.serialPortsGroupBox.setTitle(
            QCoreApplication.translate("MainWindow", "Serial port", None)
        )
        # if QT_CONFIG(tooltip)
        self.serialPortsComboBox.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "List of available serial ports", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(tooltip)
        self.rescanSerialPortsButton.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "Refresh list of available serial ports", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.rescanSerialPortsButton.setText(
            QCoreApplication.translate("MainWindow", "Rescan", None)
        )
        self.channelsGroupBox.setTitle(
            QCoreApplication.translate("MainWindow", "Channels", None)
        )
        self.ch16RadioButton.setText(
            QCoreApplication.translate("MainWindow", "16", None)
        )
        self.ch32RadioButton.setText(
            QCoreApplication.translate("MainWindow", "32", None)
        )
        self.ch64RadioButton.setText(
            QCoreApplication.translate("MainWindow", "64", None)
        )
        self.experimentGroupBox.setTitle(
            QCoreApplication.translate("MainWindow", "Configure experiment", None)
        )
        self.label.setText(
            QCoreApplication.translate("MainWindow", "Output file name:", None)
        )
        # if QT_CONFIG(tooltip)
        self.experimentTextField.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "If no name is provided, one based on the timestamp will be used",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.label_2.setText(
            QCoreApplication.translate("MainWindow", "JSON with configuration:", None)
        )
        self.browseJSONButton.setText(
            QCoreApplication.translate("MainWindow", "Browse", None)
        )
        self.JSONLabel.setText("")
        self.trainingGroupBox.setTitle(
            QCoreApplication.translate("MainWindow", "Configure model training", None)
        )
        self.svmRadioButton.setText(
            QCoreApplication.translate("MainWindow", "SVM", None)
        )
        self.bssRadioButton.setText(
            QCoreApplication.translate("MainWindow", "BSS", None)
        )
        # if QT_CONFIG(tooltip)
        self.trainingTextField.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                "If no name is provided, one based on the timestamp will be used",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.label_3.setText(
            QCoreApplication.translate("MainWindow", "Output file name:", None)
        )
        self.label_4.setText(
            QCoreApplication.translate("MainWindow", "Training data:", None)
        )
        self.browseTrainButton.setText(
            QCoreApplication.translate("MainWindow", "Browse", None)
        )
        self.trainLabel.setText("")
        self.startTrainButton.setText(
            QCoreApplication.translate("MainWindow", "Start training", None)
        )
        self.startAcquisitionButton.setText(
            QCoreApplication.translate("MainWindow", "Start acquisition", None)
        )
        self.stopAcquisitionButton.setText(
            QCoreApplication.translate("MainWindow", "Stop acquisition", None)
        )

    # retranslateUi
