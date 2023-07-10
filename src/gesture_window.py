from __future__ import annotations

import os

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QWidget

import resources


class GeturesWindow(QWidget):
    """Widget showing the gestures to perform.

    Parameters
    ----------
    gestures : dict of {str : str
        Dictionary containing pairs of gesture labels and paths to images.
    n_reps : int
        Number of repetitions for each gesture.
    duration_ms : int
        Duration of gestures and rest (in ms).
    image_folder : str
        Path to the image folder containing the images.

    Attributes
    ----------
    _gesture_dict : dict of {str : str}
        Dictionary containing pairs of gesture labels and paths to images.
    _gestures_id : dict of {str : int}
        Dictionary containing pairs of gesture labels and integer indexes.
    _gestures_labels : list of str
        List of gesture labels accounting for the number of repetitions.
    _label : QLabel
        Label containing the image widget.
    _pixmap : QPixmap
        Image widget.
    _timer : QTimer
        Timer.
    _toggle_timer : bool
        Pause/start the timer.
    _trial_idx : int
        Trial index.
    """

    trigger_sig = pyqtSignal(int)
    stop_sig = pyqtSignal()

    def __init__(
        self,
        gestures: list[str],
        n_reps: str,
        duration_ms: int,
        image_folder: str,
    ) -> None:
        super().__init__()

        self._gesture_dict = gestures
        self._gestures_id = {k: i + 1 for i, k in enumerate(gestures.keys())}
        self._gestures_labels = []
        for k in gestures.keys():
            self._gestures_labels.extend([k] * n_reps)
        self._image_folder = image_folder

        self.setWindowTitle("Gesture Viewer")
        self.resize(480, 480)

        self._label = QLabel(self)
        self._pixmap = QPixmap(":/images/start.png")
        self._pixmap = self._pixmap.scaled(self.width(), self.height())
        self._label.setPixmap(self._pixmap)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.render_image)
        self._toggle_timer = True
        self._rep_idx = 0
        self._timer.start(duration_ms)

    def render_image(self):
        """Render the image for the current gesture."""
        if self._rep_idx == len(self._gestures_labels):
            self.close()
        elif self._toggle_timer:
            image_path = os.path.join(
                self._image_folder,
                self._gesture_dict[self._gestures_labels[self._rep_idx]],
            )
            self._pixmap = QPixmap(image_path)
            self._pixmap = self._pixmap.scaled(self.width(), self.height())
            self._label.setPixmap(self._pixmap)

            self._toggle_timer = False
            self.trigger_sig.emit(
                self._gestures_id[self._gestures_labels[self._rep_idx]]
            )
            self._rep_idx += 1
        else:
            self._pixmap = QPixmap(":/images/stop.png")
            self._pixmap = self._pixmap.scaled(self.width(), self.height())
            self._label.setPixmap(self._pixmap)

            self._toggle_timer = True
            self.trigger_sig.emit(0)

    def closeEvent(self, event):
        self._timer.stop()
        self.stop_sig.emit()
        event.accept()
