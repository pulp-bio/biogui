"""
BioGUI entry point.


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

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        sys.exit("Usage: python main.py [ENABLE_LOGS]")

    # Enable logging
    if len(sys.argv) == 2 and sys.argv[1]:

        import logging

        logging.basicConfig(level=logging.INFO)

    from biogui import BioGUI

    app = BioGUI()
    sys.exit(app.exec())
