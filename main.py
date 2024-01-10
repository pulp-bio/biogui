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

from biosignal_acquisition_gui import MainWindow


def main():
    logging.basicConfig(level=logging.INFO)

    # Input
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--packetSize", required=True, type=int, help="Number of bytes in the packet"
    )
    args = vars(parser.parse_args())
    packetSize = args["packetSize"]

    # Setup application and main window
    app = QApplication(sys.argv)
    mainWin = MainWindow(packetSize)
    mainWin.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
