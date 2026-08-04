import unittest

from . import _pathfix  # noqa: F401

from smartcraft_toolkit.experiments import Experiment
from smartcraft_toolkit.protocol_map import categorize_byte
from smartcraft_toolkit.signals import CandidateKey, Trace

EXPERIMENTS = [
    Experiment("idle", None, rpm_rank=0, session_order=0, tags=("idle",)),
    Experiment("1000rpm", None, rpm_rank=1, session_order=1, tags=("rpm",)),
    Experiment("1650rpm", None, rpm_rank=2, session_order=2, tags=("rpm",)),
    Experiment("1900rpm", None, rpm_rank=3, session_order=3, tags=("rpm",)),
    Experiment("idle2", None, rpm_rank=0, session_order=4, tags=("idle", "idle_replicate")),
]
KEY = CandidateKey("170", "00", 0, 1, "")


def trace(values):
    t = Trace()
    t.values = list(values)
    t.timestamps = [float(i) for i in range(len(values))]
    return t


class TestCategorizeByte(unittest.TestCase):
    def test_constant_zero_byte_is_padding(self):
        traces = {name: trace([0, 0, 0]) for name in ["idle", "1000rpm", "1650rpm", "1900rpm", "idle2"]}
        entry = categorize_byte(KEY, traces, EXPERIMENTS)
        self.assertEqual(entry.category, "Likely padding/reserved")
        self.assertIn("0x00", entry.detail)

    def test_ever_increasing_byte_is_a_counter(self):
        traces = {
            "idle": trace([1, 2]),
            "1000rpm": trace([3, 4]),
            "1650rpm": trace([5, 6]),
            "1900rpm": trace([7, 8]),
            "idle2": trace([9, 10]),
        }
        entry = categorize_byte(KEY, traces, EXPERIMENTS)
        self.assertEqual(entry.category, "Likely counters")

    def test_two_distinct_values_is_status_bits(self):
        traces = {
            "idle": trace([0, 1, 0]),
            "1000rpm": trace([1, 0]),
            "1650rpm": trace([0, 1]),
            "1900rpm": trace([1, 0]),
            "idle2": trace([0, 1]),
        }
        entry = categorize_byte(KEY, traces, EXPERIMENTS)
        self.assertEqual(entry.category, "Likely status bits")

    def test_clean_rpm_shaped_byte_is_labeled_with_its_best_hypothesis(self):
        traces = {
            "idle": trace([10, 10, 11]),
            "1000rpm": trace([40, 41, 40]),
            "1650rpm": trace([70, 71, 70]),
            "1900rpm": trace([100, 101, 100]),
            "idle2": trace([10, 11, 10]),
        }
        entry = categorize_byte(KEY, traces, EXPERIMENTS)
        self.assertTrue(entry.category.startswith("Likely"))
        self.assertNotEqual(entry.category, "Unknown")

    def test_noisy_uncorrelated_byte_is_unknown(self):
        traces = {
            "idle": trace([5, 200, 30, 180, 60]),
            "1000rpm": trace([190, 10, 150, 40, 220]),
            "1650rpm": trace([20, 170, 90, 130, 15]),
            "1900rpm": trace([210, 5, 160, 35, 195]),
            "idle2": trace([50, 140, 25, 205, 70]),
        }
        entry = categorize_byte(KEY, traces, EXPERIMENTS)
        self.assertEqual(entry.category, "Unknown")


if __name__ == "__main__":
    unittest.main()
