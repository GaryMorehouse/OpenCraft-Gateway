"""Makes `app` (this service) and `smartcraft_toolkit` (tools/) importable
when tests are run from any working directory."""
import sys
from pathlib import Path

_REPLAY_DIR = Path(__file__).resolve().parent.parent  # services/replay
_TOOLS_DIR = _REPLAY_DIR.parent.parent / "tools"  # <repo root>/tools

for _dir in (_REPLAY_DIR, _TOOLS_DIR):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
