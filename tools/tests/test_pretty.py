import unittest

from . import _pathfix  # noqa: F401

from smartcraft_toolkit.pretty import format_packet, format_packets
from smartcraft_toolkit.reconstruct import LogicalPacket


def packet(ts, can_id, records, complete=True):
    return LogicalPacket(
        can_id=can_id,
        timestamp=ts,
        end_timestamp=ts,
        records={k: bytes.fromhex(v) for k, v in records.items()},
        complete=complete,
        frame_count=len(records),
    )


class TestFormatPacket(unittest.TestCase):
    def test_matches_expected_layout(self):
        p = packet(
            1.0,
            "170",
            {
                "00": "076D040C63FFFF",
                "01": "025973A01AAC00",
                "02": "00090000000000",
            },
        )
        text = format_packet(p, 127)
        expected = (
            "Packet 127\n"
            "170\n"
            "00 076D040C63FFFF\n"
            "01 025973A01AAC00\n"
            "02 00090000000000"
        )
        self.assertEqual(text, expected)

    def test_incomplete_packet_is_flagged(self):
        p = packet(1.0, "170", {"00": "AA"}, complete=False)
        text = format_packet(p, 0)
        self.assertIn("incomplete", text)


class TestFormatPackets(unittest.TestCase):
    def test_multiple_packets_are_indexed_in_order_and_blank_line_separated(self):
        packets = [packet(1.0, "170", {"00": "AA"}), packet(2.0, "1A0", {"00": "BB"})]
        text = format_packets(packets)
        self.assertEqual(text, "Packet 0\n170\n00 AA\n\nPacket 1\n1A0\n00 BB")


if __name__ == "__main__":
    unittest.main()
