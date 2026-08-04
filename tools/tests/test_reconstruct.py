import unittest

from . import _pathfix  # noqa: F401

from smartcraft_toolkit.parser import Frame
from smartcraft_toolkit.reconstruct import classify_ids, reconstruct


def frame(ts, can_id, hexdata, interface="can0"):
    return Frame(timestamp=ts, interface=interface, can_id=can_id, data=bytes.fromhex(hexdata))


class TestClassifyIds(unittest.TestCase):
    def test_id_with_terminator_and_sequence_is_fragmented(self):
        frames = [
            frame(1.0, "170", "0002470415A8FFFF"),
            frame(2.0, "170", "01015A73A0116700"),
            frame(3.0, "170", "FF00000000000000"),
        ]
        self.assertEqual(classify_ids(frames), {"170": True})

    def test_id_with_single_constant_first_byte_is_atomic(self):
        # e.g. a noise/keepalive frame whose first byte never changes
        frames = [frame(1.0, "0E3792F3", "83E9EB7D3A267B16") for _ in range(5)]
        self.assertEqual(classify_ids(frames), {"0E3792F3": False})

    def test_id_with_only_two_distinct_bytes_no_terminator_is_atomic(self):
        # only ever seen record byte 0x01 -- no 0xFF terminator observed, no evidence of the convention
        frames = [frame(1.0, "0000410B", "0100000000000000")]
        self.assertEqual(classify_ids(frames), {"0000410B": False})

    def test_terminator_alone_without_other_records_is_atomic(self):
        # 0xFF present but nothing else -- not enough evidence of a real sequence
        frames = [frame(1.0, "1F0", "FF00000000000000")]
        self.assertEqual(classify_ids(frames), {"1F0": False})


class TestReconstruct(unittest.TestCase):
    def test_full_170_cycle_reconstructs_into_one_packet(self):
        frames = [
            frame(0.0, "170", "FF00000000000000"),
            frame(1.0, "170", "00076D040C63FFFF"),
            frame(2.0, "170", "01025973A01AAC00"),
            frame(3.0, "170", "0200090000000000"),
            frame(4.0, "170", "030515000000FFFF"),
            frame(5.0, "170", "0400000000000000"),
            frame(6.0, "170", "0500000000000000"),
            frame(7.0, "170", "0600000000000000"),
            frame(8.0, "170", "FF00000000000000"),
        ]
        packets, atomic_messages, fragmented_ids = reconstruct(frames)
        self.assertEqual(fragmented_ids, {"170"})
        self.assertEqual(atomic_messages, [])
        # the leading bare FF at t=0 (log starting mid-cycle, as real captures
        # do) has nothing collected yet, so it flushes immediately as its own
        # 1-record packet; the real 00..FF cycle that follows is the second.
        self.assertEqual(len(packets), 2)

        leading, cycle = packets
        self.assertTrue(leading.complete)
        self.assertEqual(set(leading.records), {"FF"})
        self.assertEqual(leading.timestamp, 0.0)

        self.assertTrue(cycle.complete)
        self.assertEqual(set(cycle.records), {"00", "01", "02", "03", "04", "05", "06", "FF"})
        self.assertEqual(cycle.records["00"], bytes.fromhex("076D040C63FFFF"))
        self.assertEqual(cycle.records["03"], bytes.fromhex("0515000000FFFF"))
        self.assertEqual(cycle.timestamp, 1.0)
        self.assertEqual(cycle.end_timestamp, 8.0)
        self.assertEqual(cycle.frame_count, 8)

    def test_missing_terminator_flushes_as_incomplete_on_next_00(self):
        frames = [
            frame(1.0, "170", "0002470415A8FFFF"),
            frame(2.0, "170", "01015A73A0116700"),
            # no FF here -- next cycle starts with 00 again
            frame(3.0, "170", "0002470415A9FFFF"),
            frame(4.0, "170", "FF00000000000000"),
        ]
        packets, _atomic, _fragmented = reconstruct(frames)
        self.assertEqual(len(packets), 2)
        self.assertFalse(packets[0].complete)
        self.assertEqual(set(packets[0].records), {"00", "01"})
        self.assertTrue(packets[1].complete)
        self.assertEqual(set(packets[1].records), {"00", "FF"})

    def test_trailing_incomplete_packet_is_flushed_at_end_of_stream(self):
        frames = [
            # an earlier complete cycle establishes evidence of the
            # record/terminator convention for this CAN ID
            frame(1.0, "170", "0002470415A8FFFF"),
            frame(2.0, "170", "01015A73A0116700"),
            frame(3.0, "170", "FF00000000000000"),
            # the capture ends mid-cycle, with no terminator frame
            frame(4.0, "170", "0002470415A9FFFF"),
            frame(5.0, "170", "01015A73A0116800"),
        ]
        packets, _atomic, _fragmented = reconstruct(frames)
        self.assertEqual(len(packets), 2)
        self.assertTrue(packets[0].complete)
        self.assertFalse(packets[1].complete)
        self.assertEqual(set(packets[1].records), {"00", "01"})

    def test_atomic_id_passes_through_unmodified(self):
        frames = [
            frame(1.0, "0000410B", "0100000000000000"),
            frame(2.0, "0000410B", "0100000000000001"),
        ]
        packets, atomic_messages, fragmented_ids = reconstruct(frames)
        self.assertEqual(packets, [])
        self.assertEqual(fragmented_ids, set())
        self.assertEqual(len(atomic_messages), 2)
        self.assertEqual(atomic_messages[0].data, bytes.fromhex("0100000000000000"))

    def test_multiple_can_ids_are_tracked_independently(self):
        frames = [
            frame(1.0, "170", "0002470415A8FFFF"),
            frame(1.1, "1A0", "0003010100000000"),
            frame(1.5, "170", "01015A73A0116700"),
            frame(2.0, "170", "FF00000000000000"),
            frame(2.1, "1A0", "0180000000000000"),
            frame(2.2, "1A0", "FF00000000000000"),
        ]
        packets, _atomic, fragmented_ids = reconstruct(frames)
        self.assertEqual(fragmented_ids, {"170", "1A0"})
        by_id = {p.can_id: p for p in packets}
        self.assertEqual(set(by_id), {"170", "1A0"})
        self.assertTrue(by_id["170"].complete)
        self.assertTrue(by_id["1A0"].complete)


if __name__ == "__main__":
    unittest.main()
