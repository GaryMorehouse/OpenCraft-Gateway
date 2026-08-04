import unittest

from . import _pathfix  # noqa: F401

from smartcraft_toolkit.compare import Verdict, compare_logs, compute_byte_stats
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


class TestComputeByteStats(unittest.TestCase):
    def test_never_changed_byte_has_zero_change_rate(self):
        packets = [
            packet(1.0, "170", {"00": "0102"}),
            packet(2.0, "170", {"00": "0102"}),
            packet(3.0, "170", {"00": "0102"}),
        ]
        stats = compute_byte_stats(packets)
        self.assertEqual(stats[("170", "00", 0)].change_rate, 0.0)
        self.assertEqual(stats[("170", "00", 0)].distinct_values, 1)
        self.assertTrue(stats[("170", "00", 0)].is_constant)

    def test_always_changing_byte_has_100_percent_change_rate(self):
        packets = [
            packet(1.0, "170", {"00": "0100"}),
            packet(2.0, "170", {"00": "0200"}),
            packet(3.0, "170", {"00": "0300"}),
        ]
        stats = compute_byte_stats(packets)
        self.assertEqual(stats[("170", "00", 0)].change_rate, 100.0)
        self.assertEqual(stats[("170", "00", 1)].change_rate, 0.0)

    def test_stats_are_scoped_per_record_not_shared_across_records(self):
        packets = [
            packet(1.0, "170", {"00": "01", "01": "AA"}),
            packet(2.0, "170", {"00": "02", "01": "AA"}),
        ]
        stats = compute_byte_stats(packets)
        self.assertEqual(stats[("170", "00", 0)].change_rate, 100.0)
        self.assertEqual(stats[("170", "01", 0)].change_rate, 0.0)


class TestCompareLogs(unittest.TestCase):
    def test_identical_constant_byte_is_constant(self):
        packets_a = [packet(1.0, "170", {"00": "AA"})]
        packets_b = [packet(1.0, "170", {"00": "AA"})]
        comparisons = compare_logs(packets_a, packets_b)
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0].verdict, Verdict.CONSTANT)

    def test_disjoint_value_ranges_are_changed(self):
        # e.g. idle sits at 0x10-0x12, 2500rpm sits at 0x80-0x82 -- clean signal
        packets_a = [
            packet(1.0, "170", {"00": "10"}),
            packet(2.0, "170", {"00": "11"}),
        ]
        packets_b = [
            packet(1.0, "170", {"00": "80"}),
            packet(2.0, "170", {"00": "81"}),
        ]
        comparisons = compare_logs(packets_a, packets_b)
        self.assertEqual(comparisons[0].verdict, Verdict.CHANGED)

    def test_overlapping_multi_valued_byte_is_variable_not_guessed(self):
        packets_a = [
            packet(1.0, "170", {"00": "01"}),
            packet(2.0, "170", {"00": "02"}),
        ]
        packets_b = [
            packet(1.0, "170", {"00": "02"}),
            packet(2.0, "170", {"00": "03"}),
        ]
        comparisons = compare_logs(packets_a, packets_b)
        self.assertEqual(comparisons[0].verdict, Verdict.VARIABLE)

    def test_byte_missing_from_one_log_is_omitted_not_fabricated(self):
        packets_a = [packet(1.0, "170", {"00": "AA"})]
        packets_b = [packet(1.0, "1A0", {"00": "AA"})]
        comparisons = compare_logs(packets_a, packets_b)
        self.assertEqual(comparisons, [])


if __name__ == "__main__":
    unittest.main()
