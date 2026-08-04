"""Fragmented-packet reconstruction.

Observed convention: for some CAN IDs, the first payload byte of every frame
is a record/sequence number, and a frame whose record number is 0xFF
terminates one logical multi-frame packet. This module *detects* whether a
given CAN ID follows that convention from the frames actually seen -- it
never assumes it for any specific ID. An ID only qualifies as "fragmented"
when the evidence supports it (a 0xFF terminator plus at least one other
record value observed). Everything else is passed through unmodified as an
atomic, single-frame message.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from .parser import Frame

TERMINATOR = 0xFF


@dataclass(frozen=True)
class LogicalPacket:
    can_id: str
    timestamp: float  # timestamp of the first frame in the packet
    end_timestamp: float  # timestamp of the last frame in the packet
    records: Dict[str, bytes]  # record number, e.g. "00" -> payload with the record byte stripped
    complete: bool  # True if a 0xFF terminator frame was observed
    frame_count: int


@dataclass(frozen=True)
class AtomicMessage:
    can_id: str
    timestamp: float
    data: bytes


def classify_ids(frames: List[Frame]) -> Dict[str, bool]:
    """Decide, per CAN ID, whether its frames follow the record/terminator convention."""
    first_bytes: Dict[str, Set[int]] = {}
    for frame in frames:
        if not frame.data:
            continue
        first_bytes.setdefault(frame.can_id, set()).add(frame.data[0])

    fragmented: Dict[str, bool] = {}
    for can_id, seen in first_bytes.items():
        non_terminator = seen - {TERMINATOR}
        fragmented[can_id] = TERMINATOR in seen and len(non_terminator) >= 2
    return fragmented


class _OpenPacket:
    __slots__ = ("records", "start_ts", "end_ts")

    def __init__(self, timestamp: float) -> None:
        self.records: Dict[str, bytes] = {}
        self.start_ts = timestamp
        self.end_ts = timestamp


def reconstruct(
    frames: List[Frame],
) -> Tuple[List[LogicalPacket], List[AtomicMessage], Set[str]]:
    """Group frames into logical packets.

    Returns (packets, atomic_messages, fragmented_ids), packets and atomic
    messages both sorted by timestamp.
    """
    fragmented_ids = {can_id for can_id, is_frag in classify_ids(frames).items() if is_frag}

    open_packets: Dict[str, _OpenPacket] = {}
    packets: List[LogicalPacket] = []
    atomic_messages: List[AtomicMessage] = []

    def flush(can_id: str, complete: bool) -> None:
        open_packet = open_packets.pop(can_id)
        packets.append(
            LogicalPacket(
                can_id=can_id,
                timestamp=open_packet.start_ts,
                end_timestamp=open_packet.end_ts,
                records=dict(open_packet.records),
                complete=complete,
                frame_count=len(open_packet.records),
            )
        )

    for frame in frames:
        if frame.can_id not in fragmented_ids:
            atomic_messages.append(AtomicMessage(frame.can_id, frame.timestamp, frame.data))
            continue

        record_byte = frame.data[0]
        record_key = f"{record_byte:02X}"
        payload = frame.data[1:]

        open_packet = open_packets.get(frame.can_id)
        if record_byte == 0 and open_packet is not None and open_packet.records:
            # A new record 00 arrived without a terminator for the previous
            # packet -- flush what was collected as incomplete and start fresh.
            flush(frame.can_id, complete=False)
            open_packet = None
        if open_packet is None:
            open_packet = _OpenPacket(frame.timestamp)
            open_packets[frame.can_id] = open_packet

        open_packet.records[record_key] = payload
        open_packet.end_ts = frame.timestamp

        if record_byte == TERMINATOR:
            flush(frame.can_id, complete=True)

    for can_id in list(open_packets):
        flush(can_id, complete=False)

    packets.sort(key=lambda p: p.timestamp)
    atomic_messages.sort(key=lambda m: m.timestamp)
    return packets, atomic_messages, fragmented_ids
