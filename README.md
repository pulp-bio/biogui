# BioGUI

Modular PySide6 GUI for acquiring and visualizing bio-signals from different sources.

## BioGUI Requirements

- `uv`: The project uses uv as its package manager. uv will automatically download and manage the required Python version for you (the project is pinned to Python 3.11). To install uv: `pip install uv` or see [installation instructions](https://docs.astral.sh/uv/getting-started/installation/).

## BioGUI Setup

To install dependencies, run:

```bash
uv sync
```

### Development

To install the pre-commit hooks (ruff, black, prettier, license headers), run:

```bash
uv run pre-commit install
```

### Run

Run the script [`main.py`](https://github.com/pulp-bio/biogui/blob/main/main.py), which launches the main window.

You can run the application in two ways:

**Option 1:** Run with uv:

```bash
uv run main.py
```

**Option 2:** Activate the virtual environment and run directly:

```bash
source .venv/bin/activate
python main.py
```

#### Interface with board

To enable communication between the GUI and a board, one must provide a Python file with the following specifications:

- `packetSize`: integer representing the number of bytes to be read;
- `startSeq`: sequence of commands to start the board, expressed as a list of bytes;
- `stopSeq`: sequence of commands to stop the board, expressed as a list of bytes;
- `sigInfo`: dictionary containing, for each signal, a sub-dictionary with:
  - `fs`: sampling rate (float)
  - `nCh`: number of channels (int)
  - `signal_type`: dictionary with signal type information (required), must contain at least:
    - `type`: signal type, either `"ultrasound"` or `"time-series"` (string)
- `decodeFn`: function that decodes each packet of bytes read from the board into the specified signals.

Some examples of interface files are provided in the [`interfaces`](https://github.com/pulp-bio/biogui/blob/main/interfaces) folder.

### Utilities

In the [`utils`](https://github.com/pulp-bio/biogui/blob/main/utils) folder, there are some utility scripts: the most useful one is [`plot_signal.py`](https://github.com/pulp-bio/biogui/blob/main/utils/plot_signal.py), which shows how to open the `.bio` binary file containing the acquired signals.

## Applications

This repository contains additional components in the [`applications/`](applications) folder:

- [`bio-bridge`](applications/bio-bridge/README.md) — BioBridge: real-time ML inference middleware
- [`motion-lab`](applications/motion-lab/README.md) — MotionLab: Unity environment for hand control and task evaluation

To run the full gesture-control pipeline, additional setup is required for BioBridge and MotionLab.
See [`bio-bridge/README.md`](bio-bridge/README.md) and [`motion-lab/README.md`](motion-lab/README.md).

**Preparation** (order does not matter):

- Open BioGUI and configure the interface and forwarding settings.
- Open MotionLab in Unity and load a scene (do not press Play yet).

**Start** (in this order):

1. Run BioBridge — waits for an incoming BioGUI connection.
2. Start acquisition in BioGUI with forwarding enabled — data is displayed and forwarded to BioBridge.
3. Press Play in Unity — receives hand pose data from BioBridge and starts rendering.

## Authors

This work was realized mainly at the [Energy-Efficient Embedded Systems Laboratory (EEES Lab)](https://dei.unibo.it/it/ricerca/laboratori-di-ricerca/eees)
of University of Bologna (Italy), and at the [Digital Circuits and Systems (IIS)](https://iis.ee.ethz.ch/research/research-groups/Digital%20Circuits%20and%20Systems.html) of ETH Zurich by:

- [Mattia Orlandi](https://www.unibo.it/sitoweb/mattia.orlandi/en) (University of Bologna)
- [Pierangelo Maria Rapa](https://www.unibo.it/sitoweb/pierangelomaria.rapa/en) (University of Bologna)
- Enzo Baraldi (ETH Zurich)

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
