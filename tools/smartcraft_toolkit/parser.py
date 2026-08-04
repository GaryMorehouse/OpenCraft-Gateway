"""Parser for SocketCAN ``candump -L`` log files.

Log line format::

    (1785862423.342612) can0 170#FF00000000000000

Lines that do not match this format are collected as errors rather than
raising, so a single malformed or truncated line doesn't abort a run over a
multi-megabyte capture.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

_LINE_RE = re.compile(
    r"^\((?P<timestamp>\d+\.\d+)\)\s+(?P<interface>\S+)\s+"
    r"(?P<can_id>[0-9A-Fa-f]+)#(?P<data>[0-9A-Fa-f]*)\s*$"
)


@dataclass(frozen=True)
class Frame:
    """A single CAN frame read from a candump -L log."""

    timestamp: float
    interface: str
    can_id: str  # uppercase hex, no '0x' prefix, exactly as it appeared on the bus
    data: bytes


@dataclass
class ParseResult:
    frames: List[Frame]
    errors: List[str]  # raw lines that could not be parsed, kept for transparency


def parse_line(line: str) -> Optional[Frame]:
    match = _LINE_RE.match(line.strip())
    if not match:
        return None
    data_hex = match.group("data")
    if len(data_hex) % 2:
        return None
    return Frame(
        timestamp=float(match.group("timestamp")),
        interface=match.group("interface"),
        can_id=match.group("can_id").upper(),
        data=bytes.fromhex(data_hex),
    )


def parse_lines(lines) -> ParseResult:
    frames: List[Frame] = []
    errors: List[str] = []
    for raw_line in lines:
        raw_line = raw_line.rstrip("\n")
        if not raw_line.strip():
            continue
        frame = parse_line(raw_line)
        if frame is None:
            errors.append(raw_line)
        else:
            frames.append(frame)
    return ParseResult(frames=frames, errors=errors)


def parse_file(path: Union[str, Path]) -> ParseResult:
    with open(path, "r", encoding="ascii", errors="replace") as handle:
        return parse_lines(handle)
