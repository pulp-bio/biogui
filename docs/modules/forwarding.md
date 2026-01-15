# Forwarding Module
The Forwarding module allows you to send acquired signals to external servers for real-time processing or recording. When you add the Forwarding module, a configuration widget appears in the scrollable area where you can select signals to forward and configure the socket connection.

The Forwarding module provides three configuration sections:

1. **[Signal Selection](#signal-selection)**: Choose which signals to forward from the available data sources.
2. **[Window Settings](#window-settings)**: Define the length and stride of data windows to send.
3. **[Socket Configuration](#socket-configuration)**: Set up the connection parameters for sending data.


## Signal Selection
A tree view displays all available data sources and their signals:

- Click checkboxes next to signal names to select which signals to forward
- Multiple signals from multiple data sources can be selected simultaneously

## Socket Configuration
You can choose between two connection types:

1. **TCP/UDP Socket**: Connect to a remote server using IP address and port
    - **Socket Address**: IP address or hostname of the remote server
    - **Socket Port**: Port number (1024-49151)

2. **Unix Socket** (Linux/macOS only): Connect using a Unix domain socket file
    - **Socket Path**: Path to the Unix domain socket file

## Window Settings
- **Window Length**: Length of each data window in milliseconds (1-10000)
- **Window Stride**: Step size between consecutive windows in milliseconds (1-10000)