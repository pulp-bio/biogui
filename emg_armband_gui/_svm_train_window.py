import pickle

import numpy as np
from PySide6.QtCore import QSize
from PySide6.QtGui import QMovie
from PySide6.QtWidgets import QLabel, QWidget
from scipy import signal
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

from ._ui.ui_svm_train import Ui_SVMTrain
from ._utils import WaveformLength


class SVMWindow(QWidget, Ui_SVMTrain):
    def __init__(self, trainData: np.ndarray, outFilePath: str):
        super(SVMWindow, self).__init__()

        self.setupUi(self)
        self._trainData = trainData
        self._outFilePath = outFilePath
        self._clf: object
        self.startButton.clicked.connect(self._SVMtrain)
        self._sampleRate = 4e3
        self._WlWindowSize = int(60 * (self._sampleRate / 1000))
        self._downsampleFactorSVM = int(200 * (self._sampleRate / 1000))
        self._label = QLabel(self)
        self._pixmap = QMovie("designer/images/waiting.gif")
        size = QSize(self.width(), self.height())
        self._pixmap.setScaledSize(size)
        self.progressLabel.setMovie(self._pixmap)
        # self.trainAcc.show()
        # self._pixmap.start()

    def _SVMtrain(self):
        self.featureComboBox.setEnabled(False)
        self.kernelComboBox.setEnabled(False)
        self.cTextField.setEnabled(False)
        self.startButton.setEnabled(False)
        self.progressLabel.show()

        self._pixmap.start()

        self._feature = self.featureComboBox.currentText()
        self._kernel = self.kernelComboBox.currentText()
        self._c = 1.0 if self.cTextField.text() == "" else self.cTextField.text()
        dataset = self._trainData[:, :16]
        labels = self._trainData[:, 16]

        #  preprocessing
        # self.progressLabel.setText("Preprocessing started..")
        dataset_size = dataset.shape[0]
        channel_count = dataset.shape[1]
        [b, a] = signal.butter(4, [20, 500], "bandpass", fs=4000)
        pre_proc_signal = np.zeros((dataset_size, channel_count))
        for i in range(channel_count):
            pre_proc_signal[:, i] = signal.filtfilt(b, a, dataset[:, i])
        # self.progressLabel.setText("BP filter finished")

        # feature extraction
        # self.progressLabel.setText('Feature extraction (WL) processing started!')
        # TO DO add a check on the feature
        WL_signal = np.zeros((dataset_size - self._WlWindowSize, channel_count))
        for inx_channel in range(channel_count):
            WL_signal[:, inx_channel] = WaveformLength(
                pre_proc_signal[:, inx_channel], self._WlWindowSize
            )
            # self.progressLabel.setText(f'WL processed on channel {inx_channel}')
        labels = labels[self._WlWindowSize :]

        for label in np.unique(labels):
            if label == 0:
                X_train, X_test, y_train, y_test = train_test_split(
                    WL_signal[labels == label],
                    labels[labels == label],
                    test_size=0.5,
                    random_state=42,
                )
            else:
                X_train1, X_test1, y_train1, y_test1 = train_test_split(
                    WL_signal[labels == label],
                    labels[labels == label],
                    test_size=0.5,
                    random_state=42,
                )
                X_train = np.concatenate((X_train, X_train1))
                X_test = np.concatenate((X_test, X_test1))
                y_train = np.append(y_train, y_train1)
                y_test = np.append(y_test, y_test1)

        self._clf = SVC(kernel=self._kernel, C=self._c)
        self._clf.fit(
            X_train[:: self._downsampleFactorSVM], y_train[:: self._downsampleFactorSVM]
        )
        y_pred = self._clf.predict(X_test)
        self.progressLabel.hide()
        self.trainAcc.setText(f"{accuracy_score(y_test,y_pred)}")

        # save model
        with open(self._outFilePath, "wb") as file:
            pickle.dump(self._clf, file)
