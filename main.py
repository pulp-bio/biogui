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
import logging
import sys

from PySide6.QtWidgets import QApplication

from emg_armband_gui import MainWindow, modules


def main():
    logging.basicConfig(level=logging.INFO)

    # Input
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-sc",
        "--streamController",
        required=False,
        default="ESB",
        type=str,
        choices=("ESB", "Dummy"),
        help='Streaming controller (either "ESB" or "Dummy")',
    )
    parser.add_argument(
        "-fs",
        "--sampFreq",
        required=False,
        default=4000,
        type=int,
        help="Sampling frequency (in sps)",
    )
    parser.add_argument(
        "-rl",
        "--renderLength",
        required=False,
        default=1000,
        type=int,
        help="Length of the rendering window in the plot (in ms)",
    )
    parser.add_argument(
        "-ac",
        "--acqConf",
        action="store_true",
        help="Whether to provide configuration for acquisition",
    )
    args = vars(parser.parse_args())

    # Setup application and main window
    app = QApplication(sys.argv)
    mainWin = MainWindow(
        streamControllerType=args["streamController"],
        sampFreq=args["sampFreq"],
        renderLength=args["renderLength"] * args["sampFreq"] // 1000,
    )
    mainWin.show()

    # Add widgets
    if args["acqConf"]:
        acqController = modules.AcquisitionController()
        acqController.subscribe(mainWin)

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
