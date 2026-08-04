"""Human-readable packet dump.

    Packet 127
    170
    00 076D040C63FFFF
    01 025973A01AAC00
    ...
"""
from __future__ import annotations

from typing import Iterable, List

from .reconstruct import LogicalPacket


def format_packet(packet: LogicalPacket, index: int) -> str:
    lines = [f"Packet {index}", packet.can_id]
    for key in sorted(packet.records):
        lines.append(f"{key} {packet.records[key].hex().upper()}")
    if not packet.complete:
        lines.append("(incomplete -- no terminator frame observed)")
    return "\n".join(lines)


def format_packets(packets: Iterable[LogicalPacket], start_index: int = 0) -> str:
    blocks: List[str] = [format_packet(packet, start_index + offset) for offset, packet in enumerate(packets)]
    return "\n\n".join(blocks)
