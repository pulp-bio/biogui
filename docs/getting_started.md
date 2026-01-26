# Getting Started

Follow these steps to set up the BioGUI project on your local machine.

## Prerequisites

- Python 3.7 or higher.
- `pip` (Python package installer).
- A virtual environment (recommended).

## Installation


### Linux/MacOS

To install BioGUI on Linux or MacOS, follow these steps:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/pulp-bio/biogui.git
    cd biogui
    ```

2.  **Set up a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Windows

To install BioGUI on Windows, follow these steps:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/pulp-bio/biogui.git
    cd biogui
    ```

2.  **Set up a virtual environment**:
    ```powershell
    python3 -m venv venv
    venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

Once the dependencies are installed, you can launch the main GUI by running:

```bash
python main.py
```

This will open the BioGUI main window, where you can select the desired interface and start the acquisition. To get familiar with the interface, refer to the [Graphical User Interface](graphical_user_interface.md) documentation.
