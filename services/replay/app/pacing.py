"""Pure playback-timing math, kept separate from the main loop so it can be
unit tested without a real clock, InfluxDB, or a capture file.
"""
from __future__ import annotations

from typing import Optional

# CLI --speed values and their multiplier. "max" has no multiplier -- it
# means "no pacing delay at all," not "a very large speed."
SPEED_MULTIPLIERS: dict[str, Optional[float]] = {"1": 1.0, "5": 5.0, "10": 10.0, "max": None}


def playback_delay(dt_s: float, speed_multiplier: Optional[float]) -> float:
    """How long to sleep before the next frame, given the real gap between
    this frame and the previous one (dt_s, from the capture's own
    timestamps) and the configured speed multiplier.

    speed_multiplier is None for "as fast as possible" -- no delay,
    regardless of dt_s or the sign. A negative or zero dt_s (out-of-order
    or duplicate timestamps) never produces a negative sleep.
    """
    if speed_multiplier is None:
        return 0.0
    return max(0.0, dt_s / speed_multiplier)


def pct_complete(position_s: float, duration_s: float) -> float:
    if duration_s <= 0:
        return 0.0
    return max(0.0, min(100.0, position_s / duration_s * 100.0))
