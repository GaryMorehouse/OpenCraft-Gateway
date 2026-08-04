import csv
import json
import tempfile
import unittest
from pathlib import Path

from . import _pathfix  # noqa: F401

from smartcraft_toolkit.exporters import export_csv_atomic, export_csv_packets, export_json
from smartcraft_toolkit.reconstruct import AtomicMessage, LogicalPacket


def packet(ts, can_id, records, complete=True):
    return LogicalPacket(
        can_id=can_id,
        timestamp=ts,
        end_timestamp=ts,
        records={k: bytes.fromhex(v) for k, v in records.items()},
        complete=complete,
        frame_count=len(records),
    )


class TestExportJson(unittest.TestCase):
    def test_json_shape_matches_spec(self):
        packets = [packet(1785862423.342612, "170", {"00": "076D040C63FFFF", "FF": "00000000000000"})]
        atomic = [AtomicMessage("0000410B", 1785862423.0, bytes.fromhex("0100000000000000"))]
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "out.json"
            export_json(packets, atomic, out_path)
            document = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(len(document["packets"]), 1)
        entry = document["packets"][0]
        self.assertEqual(entry["id"], "170")
        self.assertIn("timestamp", entry)
        self.assertEqual(entry["records"], {"00": "076D040C63FFFF", "FF": "00000000000000"})

        self.assertEqual(len(document["atomic_messages"]), 1)
        self.assertEqual(document["atomic_messages"][0]["payload"], "0100000000000000")


class TestExportCsvPackets(unittest.TestCase):
    def test_single_id_writes_one_file_with_record_columns(self):
        packets = [
            packet(1.0, "170", {"00": "AA", "01": "BB"}),
            packet(2.0, "170", {"00": "CC"}),  # record "01" missing this cycle
        ]
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "out.csv"
            written = export_csv_packets(packets, out_path)
            self.assertEqual(written, [out_path])
            with open(out_path, newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(rows[0]["rec_00"], "AA")
        self.assertEqual(rows[0]["rec_01"], "BB")
        self.assertEqual(rows[1]["rec_00"], "CC")
        self.assertEqual(rows[1]["rec_01"], "")  # missing record -> blank, not fabricated

    def test_multiple_ids_write_separate_id_suffixed_files(self):
        packets = [
            packet(1.0, "170", {"00": "AA"}),
            packet(1.0, "1A0", {"00": "BB"}),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "out.csv"
            written = export_csv_packets(packets, out_path)
            names = sorted(p.name for p in written)
            self.assertEqual(names, ["out_170.csv", "out_1A0.csv"])


class TestExportCsvAtomic(unittest.TestCase):
    def test_writes_payload_column(self):
        messages = [AtomicMessage("0000410B", 1.0, bytes.fromhex("0100000000000000"))]
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "atomic.csv"
            export_csv_atomic(messages, out_path)
            with open(out_path, newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0]["id"], "0000410B")
        self.assertEqual(rows[0]["payload"], "0100000000000000")


if __name__ == "__main__":
    unittest.main()
