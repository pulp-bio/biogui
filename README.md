# BioGUI

Modular PySide6 GUI for acquiring and visualizing bio-signals from different sources.

## Usage

### Environment setup

The code is compatible with Python 3.10+. First, make sure you have uv installed (see [installation guide](https://docs.astral.sh/uv/getting-started/installation/)). The simplest way is probably `pip install uv` in your current Python installation.

To install dependencies and create a virtual environment with Python 3.10, run:

```
uv sync
```

### Execution

Run the script [`main.py`](https://github.com/pulp-bio/biogui/blob/main/main.py), which launches the main window.

You can run the application in two ways:

**Option 1:** Run with uv:

```
uv run main.py
```

**Option 2:** Activate the virtual environment and run directly:

```
source .venv/bin/activate
python main.py
```

### Interface with board

To enable the communication between the GUI and a board, one must provide a Python file with the following specifications:

- `packetSize`: integer representing the number of bytes to be read;
- `startSeq`: sequence of commands to start the board, expressed as a list of bytes;
- `stopSeq`: sequence of commands to stop the board, expressed as a list of bytes;
- `sigInfo`: dictionary containing, for each signal, a sub-dictionary with:
  - `fs`: sampling rate (float)
  - `nCh`: number of channels (int)
  - `signal_type`: dictionary with signal type information (required), must contain at least:
    - `type`: signal type, either `"ultrasound"` or `"time-series"` (string)
- `decodeFn`: function that decodes each packet of byte read from the board into the specified signals.

Some examples of interface files are provided in the [`interfaces`](https://github.com/pulp-bio/biogui/blob/main/interfaces) folder.

### Utilities

In the [`utils`](https://github.com/pulp-bio/biogui/blob/main/utils) folder there are some utility scripts: the most useful one is [`plot_signal.py`](https://github.com/pulp-bio/biogui/blob/main/utils/plot_signal.py), which shows how to open the `.bio` binary file containing the acquired signals.

## Authors

This work was realized mainly at the [Energy-Efficient Embedded Systems Laboratory (EEES Lab)](https://dei.unibo.it/it/ricerca/laboratori-di-ricerca/eees)
of University of Bologna (Italy) by:

- [Mattia Orlandi](https://www.unibo.it/sitoweb/mattia.orlandi/en)
- [Pierangelo Maria Rapa](https://www.unibo.it/sitoweb/pierangelomaria.rapa/en)

## Citation

If you would like to reference the project, please cite the following paper:

```
@ARTICLE{10552147,
  author={Orlandi, Mattia and Rapa, Pierangelo Maria and Zanghieri, Marcello and Frey, Sebastian and Kartsch, Victor and Benini, Luca and Benatti, Simone},
  journal={IEEE Transactions on Biomedical Circuits and Systems},
  title={Real-Time Motor Unit Tracking From sEMG Signals With Adaptive ICA on a Parallel Ultra-Low Power Processor},
  year={2024},
  volume={18},
  number={4},
  pages={771-782},
  keywords={Electrodes;Real-time systems;Muscles;Motors;Electromyography;Circuits and systems;Graphical user interfaces;Blind source separation;human-machine interfaces;independent component analysis;low-power;machine learning;on-device learning;online learning;PULP;surface EMG},
  doi={10.1109/TBCAS.2024.3410840}}
```

## License

All files are released under the Apache-2.0 license (see [`LICENSE`](https://github.com/pulp-bio/biogui/blob/main/LICENSE)).
