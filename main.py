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
import json
import logging
import sys

from PySide6.QtWidgets import QApplication

from gui_semg_acquisition import MainWindow, modules


def main():
    logging.basicConfig(level=logging.INFO)

    # Input
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sampFreq",
        required=False,
        default=1000,
        type=int,
        help="Sampling frequency (in sps)",
    )
    parser.add_argument(
        "--renderLength",
        required=False,
        default=5000,
        type=int,
        help="Length of the rendering window in the plot (in ms)",
    )
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
        "--tcpAddress",
        required=False,
        default="127.0.0.1",
        type=str,
        help="Address of the virtual hand server",
    )
    parser.add_argument(
        "--tcpPort1",
        required=False,
        default=3333,
        type=int,
        help="Port for the first virtual hand",
    )
    parser.add_argument(
        "--tcpPort2",
        required=False,
        default=3334,
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
    parser.add_argument(
        "--muDecomp",
        action="store_true",
        help="Whether to add the MU decomposition module",
    )
    args = vars(parser.parse_args())

    argConstraint = sum([bool(args["virtHand"]), bool(args["gestureMapping"])])
    if argConstraint != 0 and argConstraint != 2:
        parser.error("--virtHand and --gestureMapping must be given together")

    # Setup application and main window
    app = QApplication(sys.argv)
    mainWin = MainWindow(
        sampFreq=args["sampFreq"],
        renderLength=args["renderLength"] * args["sampFreq"] // 1000,
    )
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

        if args["virtHand"]:
            with open(args["gestureMapping"]) as f:
                gestureMapping = json.load(f)
                gestureMapping = {i: k for i, k in enumerate(gestureMapping.values())}

            svmInferenceController.tcpServerController = modules.TCPServerController(
                address=args["tcpAddress"],
                port1=args["tcpPort1"],
                port2=args["tcpPort2"],
                gestureMap=gestureMapping,
            )
    if args["muDecomp"]:
        decompositionController = modules.DecompositionController()
        decompositionController.subscribe(mainWin)

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
