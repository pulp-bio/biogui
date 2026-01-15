# Project Structure

The repository is organized as follows:

- `acquisitions/`: Contains example triggers and teleprompters JSON files for data acquisition setups.
- `biogui/`: Core library containing the application logic.
    - `controllers/`: Logic for handling data flow and user interactions.
    - `data_sources/`: Modules for interacting with different hardware (Serial, etc.).
    - `modules/`: Folder containing widgets. When a new widget is created, it should be placed here.
    - `resources/`: Folder containing all the `.ui` files and other resource files.
    - `ui/`: Folder containing python UI definition files (converted from `.ui` Qt Designer files).
    - `views/`: PySide6 implementations of the UI windows and widgets.
- `docs/`: Markdown files for this documentation.
- `interfaces/`: Definition of board-specific communication protocols (the "interfaces" for BioGUI).
- `utils/`: Collection of standalone utility scripts.
- `main.py`: The entry point script that initializes and launches the GUI.
- `mkdocs.yaml`: Configuration for the documentation site.
- `requirements.txt`: List of Python dependencies.
- `LICENSE`: Apache-2.0 license information.
