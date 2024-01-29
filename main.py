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

from biogui import MainWindow, modules


def main():
    logging.basicConfig(level=logging.INFO)

    # Input
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--acq",
        action="store_true",
        help="Whether to add the acquisition module",
    )
    parser.add_argument(
        "--svmTrain",
        action="store_true",
        help="Whether to add the SVM training module",
    )
    parser.add_argument(
        "--svmInference",
        action="store_true",
        help="Whether to add the SVM inference module",
    )
    parser.add_argument(
        "--virtHand",
        action="store_true",
        help="Whether to add the module for communicating with the virtual hand",
    )
    parser.add_argument(
        "--tcpPort1",
        required=False,
        default=3334,
        type=int,
        help="Port for the first virtual hand",
    )
    parser.add_argument(
        "--tcpPort2",
        required=False,
        default=3335,
        type=int,
        help="Port for the second virtual hand",
    )
    parser.add_argument(
        "--gestureMapping",
        required=False,
        default="",
        type=str,
        help="Path to a JSON specifying the mapping between gesture labels and joint angles",
    )
    args = vars(parser.parse_args())

    argConstraint = sum([bool(args["virtHand"]), bool(args["gestureMapping"])])
    if argConstraint != 0 and argConstraint != 2:
        parser.error("--virtHand and --gestureMapping must be given together")

    # Setup application and main window
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()

    # Add widgets
    if args["acq"]:
        modules.AcquisitionController(mainWin)  # add acquisition module
    if args["svmTrain"]:
        svmTrainController = modules.SVMTrainController()
        svmTrainController.subscribe(mainWin)
    if args["svmInference"]:
        modules.SVMInferenceController(mainWin)

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
