"""Byte-level statistics: single-log heat maps and two-log comparisons.

Every classification here is derived purely from observed values. Nothing
about what a byte *means* is assumed -- the output tells you which bytes
moved and which didn't, not why.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .reconstruct import LogicalPacket

ByteKey = Tuple[str, str, int]  # (can_id, record, byte_index)


class Verdict:
    CONSTANT = "constant"  # same single value in both logs
    CHANGED = "changed"  # value sets don't overlap at all between logs
    VARIABLE = "variable"  # ambiguous: multi-valued in at least one log, sets overlap


@dataclass
class ByteStats:
    can_id: str
    record: str
    byte_index: int
    values: Counter = field(default_factory=Counter)
    transitions: int = 0
    transitions_changed: int = 0

    @property
    def distinct_values(self) -> int:
        return len(self.values)

    @property
    def is_constant(self) -> bool:
        return self.distinct_values <= 1

    @property
    def change_rate(self) -> float:
        if self.transitions == 0:
            return 0.0
        return 100.0 * self.transitions_changed / self.transitions

    @property
    def dominant_value(self):
        return self.values.most_common(1)[0][0] if self.values else None


def compute_byte_stats(packets: List[LogicalPacket]) -> Dict[ByteKey, ByteStats]:
    """Compute per-byte value distributions and change rates.

    For each (can_id, record) group, packets are walked in chronological
    order and each byte's value is compared against the previous occurrence
    of that same record, giving a change rate independent of how often other
    records fired in between.
    """
    packets_by_group: Dict[Tuple[str, str], List[LogicalPacket]] = defaultdict(list)
    for packet in packets:
        for record in packet.records:
            packets_by_group[(packet.can_id, record)].append(packet)

    stats: Dict[ByteKey, ByteStats] = {}
    for (can_id, record), group_packets in packets_by_group.items():
        group_packets = sorted(group_packets, key=lambda p: p.timestamp)
        previous_payload = None
        for packet in group_packets:
            payload = packet.records[record]
            for byte_index, value in enumerate(payload):
                key = (can_id, record, byte_index)
                stat = stats.setdefault(key, ByteStats(can_id, record, byte_index))
                stat.values[value] += 1
                if previous_payload is not None and byte_index < len(previous_payload):
                    stat.transitions += 1
                    if previous_payload[byte_index] != value:
                        stat.transitions_changed += 1
            previous_payload = payload
    return stats


@dataclass
class ByteComparison:
    can_id: str
    record: str
    byte_index: int
    verdict: str
    stats_a: ByteStats
    stats_b: ByteStats


def compare_logs(
    packets_a: List[LogicalPacket], packets_b: List[LogicalPacket]
) -> List[ByteComparison]:
    """Compare byte-level statistics between two logs (e.g. idle vs 2500 RPM).

    Only bytes observed in both logs (same can_id/record/byte_index) are
    compared. Bytes present in only one log are omitted -- there's nothing
    to contrast them against.
    """
    stats_a = compute_byte_stats(packets_a)
    stats_b = compute_byte_stats(packets_b)

    comparisons: List[ByteComparison] = []
    for key in sorted(set(stats_a) & set(stats_b)):
        a, b = stats_a[key], stats_b[key]
        values_a = set(a.values)
        values_b = set(b.values)
        if values_a == values_b and len(values_a) == 1:
            verdict = Verdict.CONSTANT
        elif values_a.isdisjoint(values_b):
            verdict = Verdict.CHANGED
        else:
            verdict = Verdict.VARIABLE
        can_id, record, byte_index = key
        comparisons.append(ByteComparison(can_id, record, byte_index, verdict, a, b))
    return comparisons
