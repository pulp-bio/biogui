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

from biosignal_acquisition_gui import MainWindow, modules


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
    args = vars(parser.parse_args())

    # Setup application and main window
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()

    # Add widgets
    if args["acq"]:
        acqController = modules.AcquisitionController()
        acqController.subscribe(mainWin)
    if args["svmTrain"]:
        svmTrainController = modules.SVMTrainController(args["sampFreq"])
        svmTrainController.subscribe(mainWin)
    if args["svmInference"]:
        svmInferenceController = modules.SVMInferenceController()
        svmInferenceController.subscribe(mainWin)

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
