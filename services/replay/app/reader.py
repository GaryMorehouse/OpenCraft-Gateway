"""Reads a candump -L capture and, per frame, extracts the current value of
every registered replay candidate (candidates.py).

All CAN frame parsing is done by tools/smartcraft_toolkit.parser; all
byte/word extraction is done by tools/smartcraft_toolkit.signals.read_value.
This module adds no CAN parsing of its own -- it only matches frames
against the already-published candidate locations and reads them with the
existing toolkit function.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional

from smartcraft_toolkit.parser import Frame, parse_file
from smartcraft_toolkit.signals import read_value

from .candidates import ReplayCandidate


def load_frames(log_path: Path) -> list[Frame]:
    """Parses the log and returns its frames sorted by timestamp. Read-only
    -- never writes to log_path."""
    result = parse_file(log_path)
    return sorted(result.frames, key=lambda f: f.timestamp)


def extract(frame: Frame, candidate: ReplayCandidate) -> Optional[int]:
    """The raw integer value candidate.key reads from frame, or None if
    this frame doesn't match that candidate's CAN ID/record/length."""
    key = candidate.key
    if frame.can_id != key.can_id:
        return None
    if key.record:
        if not frame.data or f"{frame.data[0]:02X}" != key.record:
            return None
        payload = frame.data[1:]
    else:
        payload = frame.data
    if len(payload) < key.offset + key.width:
        return None
    return read_value(payload, key)


def iter_snapshots(
    frames: list[Frame], candidates: list[ReplayCandidate]
) -> Iterator[tuple[Frame, dict[str, int]]]:
    """Walks frames in order, yielding (frame, updates) for every frame that
    matches at least one candidate -- updates maps candidate label to the
    value just read from that frame. Frames matching no candidate are
    skipped (nothing to publish); since each yielded frame still carries
    its own real timestamp, a caller pacing playback off consecutive
    yielded frames' timestamps (pacing.py) still reproduces the real gaps
    correctly even across skipped frames."""
    for frame in frames:
        updates: dict[str, int] = {}
        for candidate in candidates:
            value = extract(frame, candidate)
            if value is not None:
                updates[candidate.label] = value
        if updates:
            yield frame, updates
