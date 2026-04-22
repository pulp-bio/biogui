#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

mkdir -p biogui/ui

find biogui/resources -type f -name "*.ui" | while read -r ui_file; do
    ui_name="$(basename "${ui_file}" .ui)"
    output_file="biogui/ui/ui_${ui_name}.py"
    echo "Compiling ${ui_file} -> ${output_file}"
    uv run pyside6-uic "${ui_file}" -o "${output_file}"
done

if [[ -f biogui/resources/biogui.qrc ]]; then
    echo "Compiling biogui/resources/biogui.qrc -> biogui/ui/biogui_rc.py"
    uv run pyside6-rcc biogui/resources/biogui.qrc -o biogui/ui/biogui_rc.py
fi

python -c "
from pathlib import Path
for path in Path('biogui/ui').glob('ui_*.py'):
    text = path.read_text()
    text = text.replace('import biogui_rc', 'from . import biogui_rc')
    path.write_text(text)
"
