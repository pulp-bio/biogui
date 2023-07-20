"""This module runs the app.


Copyright 2023 Mattia Orlandi, Pierangelo Maria Rapa

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import argparse
import sys

from PySide6.QtWidgets import QApplication

from emg_armband_gui.main_window import MainWindow


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-fs",
        required=False,
        default=4000,
        type=int,
        help="Sampling frequency (in sps)",
    )
    ap.add_argument(
        "-wl",
        required=False,
        default=1000,
        type=int,
        help="Window length for rendering (in ms)",
    )
    ap.add_argument("--dummy", action="store_true")
    args = vars(ap.parse_args())
    args["wl"] = args["wl"] * args["fs"] // 1000  # convert to samples

    app = QApplication(sys.argv)
    window = MainWindow(**args)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
