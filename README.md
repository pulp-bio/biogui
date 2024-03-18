# biogui

## Introduction
Modular PySide6 GUI for acquiring and visualizing bio-signals from different sources.

## Environment setup
The code is compatible with Python 3.7+. To create and activate the Python environment, run the following commands:
```
python -m venv <ENV_NAME>
source <ENV_NAME>/bin/activate
```

Then, **from within the virtual environment**, the required packages can be installed with the following command:
```
pip install -r requirements.txt
```

## Usage

### Interface with board
To enable the communication between the GUI and a board, one must provide a Python file with the following specifications:

- `startSeq`: sequence of commands to start the board, expressed as a list of bytes;
- `stopSeq`: sequence of commands to stop the board, expressed as a list of bytes;
- `SigsPacket`: named tuple containing one field for each signal to read from the board;
- `decodeFn`: function that decodes each packet of byte read from the board into the specified signals.

Some examples of interface files are provided in the [`interfaces`](https://github.com/pulp-bio/biogui/blob/main/interfaces) folder.

Run the script [`main.py`](https://github.com/pulp-bio/biogui/blob/main/main.py).

## Authors
- [Mattia Orlandi](https://www.unibo.it/sitoweb/mattia.orlandi/en)
- [Pierangelo Maria Rapa](https://www.unibo.it/sitoweb/pierangelomaria.rapa/en)

## License
All files are released under the Apache-2.0 license (see [`LICENSE`](https://github.com/pulp-bio/biogui/blob/main/LICENSE)).
