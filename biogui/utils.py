"""
Utility functions.


Copyright 2024 Mattia Orlandi, Pierangelo Maria Rapa

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

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication


def detectTheme():
    """Determine whether the system theme is light or dark."""
    # Get palette of QApplication
    palette = QApplication.palette()

    # Compare the color of the background and text to infer theme
    textColor = palette.color(QPalette.Text)  # type: ignore
    backgroundColor = palette.color(QPalette.Window)  # type: ignore

    # Simple heuristic to determine if the theme is light or dark
    isDark = backgroundColor.lightness() < textColor.lightness()
    return "dark" if isDark else "light"
