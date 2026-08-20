"""SmartCraft capture replay publisher.

Feeds a real, already-captured CAN log (candump -L format) through the
same telemetry pipeline the simulator/gateway publisher uses (InfluxDB ->
Grafana), so real capture data can be watched moving through the existing
dashboard for human validation -- see docs/replay.md.

This package adds no new CAN decoding: candidates.py transcribes the
byte/word locations already scored by tools/smartcraft_toolkit's Phase 2
hypothesis engine and documented in docs/master-test01-analysis.md,
reader.py extracts them using smartcraft_toolkit.parser/signals directly.

`tools/` has zero third-party dependencies by design (see tools/README.md)
and is not an installed package, so this makes it importable by adding the
repo's tools/ directory to sys.path -- done once here, at package import
time, rather than in every module that needs smartcraft_toolkit.
"""
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parents[3] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
