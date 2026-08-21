"""Loader for a candump *default* (non `-L`) capture that has no per-frame
timestamps -- e.g. `candump can0 > file.log` instead of `candump -L can0`.

`drive03.log` (2026-08-21) is the first capture in this project to arrive
in this format: lines look like

    can0  170   [8]  FF 00 00 00 00 00 00 00

with no leading `(timestamp)`. Real elapsed time between frames is NOT
recoverable from a file like this -- there is no timestamp column to read,
and none should be invented as if it were real. This loader assigns each
frame a purely synthetic, evenly-spaced timestamp (`index * interval_s`)
so the existing replay pipeline -- built around real elapsed time for
pacing and every Guess/InterpolatedGuess fit -- can still play the frames
back in their ORIGINAL ORDER at a readable pace. Nothing more. Every
duration, cadence, or speed conclusion drawn from a synthetically-timed
replay is meaningless; only frame order and raw values are real. See
docs/replay.md.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from smartcraft_toolkit.parser import Frame, ParseResult

_LINE_RE = re.compile(
    r"^\s*(?P<interface>\S+)\s+(?P<can_id>[0-9A-Fa-f]+)\s+\[(?P<len>\d+)\]\s+(?P<data>[0-9A-Fa-f ]*)\s*$"
)

# Arbitrary -- chosen only to produce a watchable dashboard pace (roughly
# the order of magnitude of real inter-frame gaps seen in master-test01,
# which had a real timestamp column). NOT derived from any timing evidence
# in a no-timestamp file, since none exists there to derive it from.
DEFAULT_SYNTHETIC_INTERVAL_S = 0.005


def parse_no_timestamp_line(line: str) -> Optional[tuple[str, str, bytes]]:
    """Returns (interface, can_id, data) for a line matching candump's
    default format, or None if the line doesn't match (e.g. shell noise
    like 'nohup: ignoring input', or an odd-length hex payload)."""
    match = _LINE_RE.match(line.rstrip("\n"))
    if not match:
        return None
    data_hex = match.group("data").replace(" ", "")
    if len(data_hex) % 2:
        return None
    return (
        match.group("interface"),
        match.group("can_id").upper(),
        bytes.fromhex(data_hex),
    )


def load_frames_synthetic_timing(
    log_path: Path, interval_s: float = DEFAULT_SYNTHETIC_INTERVAL_S
) -> ParseResult:
    """Reads a no-timestamp candump capture, returning frames in their
    original file order, each given a synthetic timestamp `index *
    interval_s`. Unparseable lines are collected as errors rather than
    raising, matching smartcraft_toolkit.parser's convention -- read-only,
    never writes to log_path."""
    frames: list[Frame] = []
    errors: list[str] = []
    index = 0
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            if not raw_line.strip():
                continue
            parsed = parse_no_timestamp_line(raw_line)
            if parsed is None:
                errors.append(raw_line.rstrip("\n"))
                continue
            interface, can_id, data = parsed
            frames.append(
                Frame(timestamp=index * interval_s, interface=interface, can_id=can_id, data=data)
            )
            index += 1
    return ParseResult(frames=frames, errors=errors)
