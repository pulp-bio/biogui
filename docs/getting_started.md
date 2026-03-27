# Getting Started

Follow these steps to set up the BioGUI project on your local machine.

## Requirements

- `uv`: The project uses uv as its package manager. uv will automatically download and manage the required Python version for you (the project is pinned to Python 3.11). To install uv: `pip install uv` or see [installation instructions](https://docs.astral.sh/uv/getting-started/installation/).

## Installation

To install the BioGUI, follow these steps:

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/pulp-bio/biogui.git
    cd biogui
    ```

2.  **Set up the virtual environment with all its dependencies**:

    ```bash
    uv sync
    ```

### Development

To install the pre-commit hooks, run:

```bash
uv run pre-commit install
```

## Running the Application

Once the dependencies are installed, you can launch the main GUI in two ways:

**Option 1**: Run with uv:

```bash
uv run main.py
```

**Option 2**: Activate the virtual environment and run directly:

```bash
source .venv/bin/activate
python main.py
```

This will open the BioGUI main window, where you can select the desired interface and start the acquisition. To get familiar with the interface, refer to the [Graphical User Interface](graphical_user_interface.md) documentation.
