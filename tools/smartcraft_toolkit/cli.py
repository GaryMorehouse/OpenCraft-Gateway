"""Command-line interface for the SmartCraft protocol-analysis toolkit.

Subcommands:
    decode      parse candump -L log(s), reconstruct packets, write JSON/CSV
    pretty      parse and print a human-readable packet dump
    compare     compare byte-level behavior between two logs (e.g. idle vs 2500 RPM)
    heatmap     show per-byte change rates within a single log
    hypotheses  Phase 2: score every registered experiment's evidence against
                named signal hypotheses (RPM, coolant, oil pressure, ...) and
                render the candidate report + Current Protocol Map
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from .compare import compare_logs, compute_byte_stats
from .exporters import export_csv_atomic, export_csv_packets, export_json
from .hypothesis_report import render_full_report, run_analysis
from .pretty import format_packets
from .reconstruct import AtomicMessage, LogicalPacket, reconstruct
from .report import render_comparison_report, render_heatmap_report


def _load(path: Path):
    from .parser import parse_file

    result = parse_file(path)
    for error in result.errors:
        print(f"warning: could not parse line in {path}: {error!r}", file=sys.stderr)
    return reconstruct(result.frames)


def _filter_ids(items, ids: Optional[Sequence[str]]):
    if not ids:
        return items
    wanted = {i.upper() for i in ids}
    return [item for item in items if item.can_id in wanted]


def cmd_decode(args: argparse.Namespace) -> int:
    all_packets: List[LogicalPacket] = []
    all_atomic: List[AtomicMessage] = []
    for log_path in args.logs:
        packets, atomic_messages, _fragmented_ids = _load(Path(log_path))
        all_packets.extend(packets)
        all_atomic.extend(atomic_messages)

    all_packets.sort(key=lambda p: p.timestamp)
    all_atomic.sort(key=lambda m: m.timestamp)

    packets = _filter_ids(all_packets, args.ids)
    atomic_messages = _filter_ids(all_atomic, args.ids)

    wrote_something = False
    if args.json:
        export_json(packets, atomic_messages, args.json)
        print(f"wrote {args.json}")
        wrote_something = True
    if args.csv:
        for out_path in export_csv_packets(packets, args.csv):
            print(f"wrote {out_path}")
        if atomic_messages:
            csv_path = Path(args.csv)
            atomic_path = csv_path.with_name(f"{csv_path.stem}_atomic{csv_path.suffix}")
            export_csv_atomic(atomic_messages, atomic_path)
            print(f"wrote {atomic_path}")
        wrote_something = True
    if args.pretty or not wrote_something:
        print(format_packets(packets))
    return 0


def cmd_pretty(args: argparse.Namespace) -> int:
    packets, _atomic_messages, _fragmented_ids = _load(Path(args.log))
    packets = _filter_ids(packets, args.ids)
    print(format_packets(packets))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    packets_a, _atomic_a, _frag_a = _load(Path(args.log_a))
    packets_b, _atomic_b, _frag_b = _load(Path(args.log_b))
    packets_a = _filter_ids(packets_a, args.ids)
    packets_b = _filter_ids(packets_b, args.ids)

    label_a = args.label_a or Path(args.log_a).stem
    label_b = args.label_b or Path(args.log_b).stem

    comparisons = compare_logs(packets_a, packets_b)
    report = render_comparison_report(comparisons, label_a, label_b)

    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
        print(f"wrote {args.report}")
    else:
        print(report)
    return 0


def cmd_heatmap(args: argparse.Namespace) -> int:
    packets, _atomic_messages, _fragmented_ids = _load(Path(args.log))
    packets = _filter_ids(packets, args.ids)
    stats = compute_byte_stats(packets)
    report = render_heatmap_report(stats)

    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
        print(f"wrote {args.report}")
    else:
        print(report)
    return 0


def cmd_hypotheses(args: argparse.Namespace) -> int:
    all_results, map_entries = run_analysis()
    report = render_full_report(all_results, map_entries)

    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
        print(f"wrote {args.report}")
    else:
        print(report)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smartcraft_decoder",
        description="Protocol-agnostic CAN log analysis toolkit for reverse-engineering SmartCraft.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    decode = subparsers.add_parser("decode", help="parse log(s) and export reconstructed packets")
    decode.add_argument("logs", nargs="+", help="candump -L log file(s)")
    decode.add_argument("--json", metavar="PATH", help="write JSON output to PATH")
    decode.add_argument("--csv", metavar="PATH", help="write CSV output to PATH (one file per CAN ID)")
    decode.add_argument("--pretty", action="store_true", help="also print a human-readable dump to stdout")
    decode.add_argument("--ids", nargs="+", metavar="ID", help="only include these CAN IDs (hex)")
    decode.set_defaults(handler=cmd_decode)

    pretty = subparsers.add_parser("pretty", help="print a human-readable packet dump")
    pretty.add_argument("log", help="candump -L log file")
    pretty.add_argument("--ids", nargs="+", metavar="ID", help="only include these CAN IDs (hex)")
    pretty.set_defaults(handler=cmd_pretty)

    compare = subparsers.add_parser("compare", help="compare byte behavior between two logs")
    compare.add_argument("log_a", help="first candump -L log file (e.g. idle.log)")
    compare.add_argument("log_b", help="second candump -L log file (e.g. 2500.log)")
    compare.add_argument("--label-a", help="label for log_a in the report (default: filename)")
    compare.add_argument("--label-b", help="label for log_b in the report (default: filename)")
    compare.add_argument("--report", metavar="PATH", help="write the Markdown report to PATH instead of stdout")
    compare.add_argument("--ids", nargs="+", metavar="ID", help="only include these CAN IDs (hex)")
    compare.set_defaults(handler=cmd_compare)

    heatmap = subparsers.add_parser("heatmap", help="show per-byte change rates within a single log")
    heatmap.add_argument("log", help="candump -L log file")
    heatmap.add_argument("--report", metavar="PATH", help="write the Markdown report to PATH instead of stdout")
    heatmap.add_argument("--ids", nargs="+", metavar="ID", help="only include these CAN IDs (hex)")
    heatmap.set_defaults(handler=cmd_heatmap)

    hypotheses = subparsers.add_parser(
        "hypotheses",
        help="score registered experiments against named signal hypotheses (Phase 2)",
    )
    hypotheses.add_argument("--report", metavar="PATH", help="write the Markdown report to PATH instead of stdout")
    hypotheses.set_defaults(handler=cmd_hypotheses)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
