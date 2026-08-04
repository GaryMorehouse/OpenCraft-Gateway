#!/usr/bin/env python3
"""SmartCraft CAN log analysis tool. See tools/README.md for usage.

    python tools/smartcraft_decoder.py decode capture.log --json out.json --csv out.csv
    python tools/smartcraft_decoder.py pretty capture.log
    python tools/smartcraft_decoder.py compare idle.log 2500.log --report diff.md
    python tools/smartcraft_decoder.py heatmap capture.log --report heatmap.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from smartcraft_toolkit.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
