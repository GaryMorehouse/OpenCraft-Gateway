"""JSON and CSV exporters for reconstructed packets and atomic messages."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Union

from .reconstruct import AtomicMessage, LogicalPacket

PathLike = Union[str, Path]


def _iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def packet_to_dict(packet: LogicalPacket) -> dict:
    return {
        "timestamp": _iso(packet.timestamp),
        "id": packet.can_id,
        "complete": packet.complete,
        "records": {key: value.hex().upper() for key, value in sorted(packet.records.items())},
    }


def atomic_to_dict(message: AtomicMessage) -> dict:
    return {
        "timestamp": _iso(message.timestamp),
        "id": message.can_id,
        "payload": message.data.hex().upper(),
    }


def export_json(
    packets: List[LogicalPacket],
    atomic_messages: List[AtomicMessage],
    path: PathLike,
) -> None:
    document = {
        "packets": [packet_to_dict(p) for p in packets],
        "atomic_messages": [atomic_to_dict(m) for m in atomic_messages],
    }
    Path(path).write_text(json.dumps(document, indent=2), encoding="utf-8")


def export_csv_packets(packets: List[LogicalPacket], path: PathLike) -> List[Path]:
    """Write one CSV per CAN ID (id-suffixed when there's more than one).

    Each record becomes a column (``rec_00``, ``rec_01``, ... ``rec_FF``),
    since different CAN IDs have different record layouts and a single
    shared column set would be sparse and confusing.
    """
    base = Path(path)
    by_id: Dict[str, List[LogicalPacket]] = {}
    for packet in packets:
        by_id.setdefault(packet.can_id, []).append(packet)

    written: List[Path] = []
    for can_id, id_packets in by_id.items():
        record_keys = sorted({key for p in id_packets for key in p.records})
        out_path = base if len(by_id) == 1 else base.with_name(f"{base.stem}_{can_id}{base.suffix}")
        with open(out_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "id", "complete", "frame_count", *[f"rec_{k}" for k in record_keys]])
            for packet in sorted(id_packets, key=lambda p: p.timestamp):
                row = [_iso(packet.timestamp), packet.can_id, packet.complete, packet.frame_count]
                for key in record_keys:
                    value = packet.records.get(key)
                    row.append(value.hex().upper() if value is not None else "")
                writer.writerow(row)
        written.append(out_path)
    return written


def export_csv_atomic(messages: List[AtomicMessage], path: PathLike) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "id", "payload"])
        for message in sorted(messages, key=lambda m: m.timestamp):
            writer.writerow([_iso(message.timestamp), message.can_id, message.data.hex().upper()])
