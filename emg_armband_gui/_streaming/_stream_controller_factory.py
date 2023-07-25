"""Class implementing the a dummy streaming controller.


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

from __future__ import annotations

from ._abc_stream_controller import StreamingController
from ._dummy_stream_controller import DummyStreamingController
from ._esb_stream_controller import ESBStreamingController


def streamControllerFactory(
    controllerType: str, serialPort: str, nCh: int
) -> StreamingController:
    """Factory for StreamingController objects.

    Parameters
    ----------
    controllerType : {"ESB", "Dummy"}
        Type of the StreamingController (either "ESB" or "Dummy").
    serialPort : str
        Serial port.
    nCh : int
        Number of channels.

    Returns
    -------
    StreamingController
        Instance of StreamingController.

    Raises
    ------
    InvalidSerialPortError
        Error raised when th serial port is not valid.
    """
    match controllerType:
        case "ESB":
            return ESBStreamingController(serialPort, nCh)
        case "Dummy":
            return DummyStreamingController(nCh)
