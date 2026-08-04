"""Markdown report rendering for the two-log comparison and single-log heat map."""
from __future__ import annotations

from typing import Dict, List

from .compare import ByteComparison, ByteKey, ByteStats


def render_comparison_report(comparisons: List[ByteComparison], label_a: str, label_b: str) -> str:
    lines = [f"# Comparison: {label_a} vs {label_b}", ""]

    by_id: Dict[str, List[ByteComparison]] = {}
    for comparison in comparisons:
        by_id.setdefault(comparison.can_id, []).append(comparison)

    for can_id in sorted(by_id):
        lines.append(f"## {can_id}")
        by_record: Dict[str, List[ByteComparison]] = {}
        for comparison in by_id[can_id]:
            by_record.setdefault(comparison.record, []).append(comparison)
        for record in sorted(by_record):
            lines.append(f"### record {record}")
            lines.append("")
            lines.append(f"| byte | verdict | values in {label_a} | values in {label_b} |")
            lines.append("|---|---|---|---|")
            for comparison in sorted(by_record[record], key=lambda c: c.byte_index):
                values_a = ",".join(f"{v:02X}" for v in sorted(comparison.stats_a.values))
                values_b = ",".join(f"{v:02X}" for v in sorted(comparison.stats_b.values))
                lines.append(f"| {comparison.byte_index} | {comparison.verdict} | {values_a} | {values_b} |")
            lines.append("")
    return "\n".join(lines)


def render_heatmap_report(stats: Dict[ByteKey, ByteStats]) -> str:
    lines = ["# Byte Change Heat Map", ""]

    by_id: Dict[str, Dict[str, List[ByteStats]]] = {}
    for (can_id, record, _byte_index), stat in stats.items():
        by_id.setdefault(can_id, {}).setdefault(record, []).append(stat)

    for can_id in sorted(by_id):
        lines.append(f"## {can_id}")
        for record in sorted(by_id[can_id]):
            lines.append(f"### record {record}")
            for stat in sorted(by_id[can_id][record], key=lambda s: s.byte_index):
                descriptor = "never changed" if stat.change_rate == 0 else f"changed {stat.change_rate:.0f}%"
                lines.append(f"- byte {stat.byte_index}: {descriptor} ({stat.distinct_values} distinct value(s))")
            lines.append("")
    return "\n".join(lines)
