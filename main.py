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
    # Input
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-sc",
        "--streamController",
        required=False,
        default="ESB",
        type=str,
        choices=("ESB", "Dummy"),
        help='Streaming controller (either "ESB" or "Dummy")',
    )
    ap.add_argument(
        "-fs",
        "--sampFreq",
        required=False,
        default=4000,
        type=int,
        help="Sampling frequency (in sps)",
    )
    ap.add_argument(
        "-rl",
        "--renderLength",
        required=False,
        default=1000,
        type=int,
        help="Length of the rendering window in the plot (in ms)",
    )
    args = vars(ap.parse_args())

    streamControllerType = args["streamController"]
    sampFreq = args["sampFreq"]
    renderLength = args["renderLength"] * sampFreq // 1000  # convert to samples

    # Setup application and main window
    app = QApplication(sys.argv)
    main_win = MainWindow(streamControllerType, sampFreq, renderLength)
    main_win.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
