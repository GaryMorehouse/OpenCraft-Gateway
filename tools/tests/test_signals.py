import unittest

from . import _pathfix  # noqa: F401

from smartcraft_toolkit.experiments import Experiment
from smartcraft_toolkit.parser import Frame
from smartcraft_toolkit.signals import (
    CandidateKey,
    Trace,
    always_at_minimum,
    build_traces,
    candidate_keys_for_group,
    determine_sequenced_ids,
    distinct_value_count,
    global_range,
    group_frames,
    idle_replicate_drift,
    idle_vs_rpm_separation,
    monotonic_nondecreasing_fraction,
    near_constant_score,
    rank_correlation,
    read_value,
    rpm_correlation,
    session_drift,
    within_condition_stability,
)

EXPERIMENTS = [
    Experiment("idle", None, rpm_rank=0, session_order=0, tags=("idle",)),
    Experiment("1000rpm", None, rpm_rank=1, session_order=1, tags=("rpm",)),
    Experiment("1650rpm", None, rpm_rank=2, session_order=2, tags=("rpm",)),
    Experiment("1900rpm", None, rpm_rank=3, session_order=3, tags=("rpm",)),
    Experiment("idle2", None, rpm_rank=0, session_order=4, tags=("idle", "idle_replicate")),
]


def frame(ts, can_id, hexdata):
    return Frame(timestamp=ts, interface="can0", can_id=can_id, data=bytes.fromhex(hexdata))


def trace(values):
    t = Trace()
    t.values = list(values)
    t.timestamps = [float(i) for i in range(len(values))]
    return t


class TestGroupFrames(unittest.TestCase):
    def test_sequenced_id_groups_by_first_byte(self):
        frames = [frame(1.0, "170", "0002470415A8FFFF"), frame(2.0, "170", "FF00000000000000")]
        sequenced = determine_sequenced_ids(frames)
        self.assertTrue(sequenced["170"])
        groups = group_frames(frames, sequenced)
        self.assertEqual(set(groups), {("170", "00"), ("170", "FF")})

    def test_constant_leading_byte_id_is_not_treated_as_sequenced(self):
        # every frame starts with 0x83 -- no evidence it's a sequence selector
        frames = [frame(1.0, "0000B41", "8300000000000000"), frame(2.0, "0000B41", "8300000000000001")]
        sequenced = determine_sequenced_ids(frames)
        self.assertFalse(sequenced["0000B41"])
        groups = group_frames(frames, sequenced)
        # the whole payload is kept, including byte 0 (0x83) -- nothing stripped
        self.assertEqual(set(groups), {("0000B41", "")})
        self.assertEqual(groups[("0000B41", "")][0].data[0], 0x83)

    def test_sequenced_decision_is_global_across_all_experiments_pooled(self):
        # log A alone would look constant (only 0x83); pooled with log B it's clearly sequenced
        log_a = [frame(1.0, "170", "8300000000000000")]
        log_b = [frame(1.0, "170", "8400000000000000")]
        sequenced = determine_sequenced_ids(log_a + log_b)
        self.assertTrue(sequenced["170"])


class TestCandidateKeys(unittest.TestCase):
    def test_generates_singles_and_both_endian_pairs(self):
        keys = candidate_keys_for_group("170", "00", payload_length=3)
        singles = [k for k in keys if k.width == 1]
        pairs = [k for k in keys if k.width == 2]
        self.assertEqual(len(singles), 3)
        self.assertEqual(len(pairs), 4)  # 2 offsets * 2 endians
        self.assertEqual({k.endian for k in pairs}, {"LE", "BE"})

    def test_read_value_endianness(self):
        payload = bytes.fromhex("0102")
        le_key = CandidateKey("170", "00", 0, 2, "LE")
        be_key = CandidateKey("170", "00", 0, 2, "BE")
        self.assertEqual(read_value(payload, le_key), 0x0201)
        self.assertEqual(read_value(payload, be_key), 0x0102)


class TestRankCorrelation(unittest.TestCase):
    def test_perfect_monotonic_increase_is_one(self):
        self.assertAlmostEqual(rank_correlation([0, 1, 2, 3], [10, 20, 30, 40]), 1.0)

    def test_perfect_monotonic_decrease_is_minus_one(self):
        self.assertAlmostEqual(rank_correlation([0, 1, 2, 3], [40, 30, 20, 10]), -1.0)

    def test_no_relationship_returns_none_or_near_zero(self):
        result = rank_correlation([0, 1, 2, 3], [5, 5, 5, 5])
        self.assertIsNone(result)

    def test_too_few_points_returns_none(self):
        self.assertIsNone(rank_correlation([0], [1]))


class TestRpmCorrelation(unittest.TestCase):
    def test_clean_rpm_proportional_signal_scores_high(self):
        traces = {
            "idle": trace([100, 102, 98]),
            "1000rpm": trace([200, 198, 202]),
            "1650rpm": trace([300, 305, 295]),
            "1900rpm": trace([400, 398, 402]),
            "idle2": trace([101, 99, 103]),
        }
        corr = rpm_correlation(traces, EXPERIMENTS)
        self.assertGreater(corr, 0.95)

    def test_flat_signal_has_no_correlation(self):
        flat = trace([50, 51, 49, 50])
        traces = {name: flat for name in ["idle", "1000rpm", "1650rpm", "1900rpm", "idle2"]}
        self.assertIsNone(rpm_correlation(traces, EXPERIMENTS))

    def test_missing_most_experiments_returns_none(self):
        traces = {"idle": trace([1, 2, 3])}
        self.assertIsNone(rpm_correlation(traces, EXPERIMENTS))


class TestSessionDrift(unittest.TestCase):
    def test_warmup_like_monotonic_rise_scores_high(self):
        traces = {
            "idle": trace([70, 71]),
            "1000rpm": trace([90, 91]),
            "1650rpm": trace([110, 111]),
            "1900rpm": trace([130, 131]),
            "idle2": trace([150, 151]),
        }
        self.assertGreater(session_drift(traces, EXPERIMENTS), 0.95)


class TestStabilityAndSeparation(unittest.TestCase):
    def test_noisy_signal_has_low_stability(self):
        # alternating between the two extremes every sample is the worst
        # case under this metric (normalized stdev maxes out at 0.5, since
        # stdev of a value bounded to [0, R] can never exceed R/2) -- so 0.5
        # is the correct floor for "as noisy as it gets", not 0.
        traces = {
            "idle": trace([0, 100, 0, 100]),
            "1000rpm": trace([0, 100]),
            "1650rpm": trace([0, 100]),
            "1900rpm": trace([0, 100]),
            "idle2": trace([0, 100]),
        }
        names = [e.name for e in EXPERIMENTS]
        self.assertAlmostEqual(within_condition_stability(traces, names), 0.5)

    def test_steady_signal_has_high_stability(self):
        traces = {
            "idle": trace([50, 50, 51]),
            "1000rpm": trace([80, 81, 80]),
            "1650rpm": trace([110, 110, 111]),
            "1900rpm": trace([140, 141, 140]),
            "idle2": trace([51, 50, 51]),
        }
        names = [e.name for e in EXPERIMENTS]
        self.assertGreater(within_condition_stability(traces, names), 0.9)

    def test_idle_vs_rpm_separation_sign_and_magnitude(self):
        traces = {
            "idle": trace([10, 10]),
            "1000rpm": trace([90, 90]),
            "1650rpm": trace([90, 90]),
            "1900rpm": trace([90, 90]),
            "idle2": trace([10, 10]),
        }
        sep = idle_vs_rpm_separation(traces, EXPERIMENTS)
        self.assertGreater(sep, 0.9)

    def test_idle_replicate_drift_positive_when_idle2_higher(self):
        traces = {
            "idle": trace([10, 10]),
            "1000rpm": trace([50, 50]),
            "1650rpm": trace([50, 50]),
            "1900rpm": trace([50, 50]),
            "idle2": trace([90, 90]),
        }
        self.assertGreater(idle_replicate_drift(traces, EXPERIMENTS), 0.5)


class TestConstantAndCounterShapes(unittest.TestCase):
    def test_never_changing_byte_is_fully_constant(self):
        traces = {name: trace([7, 7, 7]) for name in ["idle", "1000rpm", "1650rpm", "1900rpm", "idle2"]}
        self.assertEqual(distinct_value_count(traces), 1)
        key = CandidateKey("170", "00", 0, 1, "")
        self.assertEqual(near_constant_score(traces, key), 1.0)

    def test_full_range_byte_has_zero_near_constant_score(self):
        traces = {"idle": trace([0, 255])}
        key = CandidateKey("170", "00", 0, 1, "")
        self.assertEqual(near_constant_score(traces, key), 0.0)

    def test_ever_increasing_trace_is_counter_like(self):
        traces = {
            "idle": trace([1, 2, 3]),
            "1000rpm": trace([4, 5, 6]),
            "1650rpm": trace([7, 8, 9]),
            "1900rpm": trace([10, 11, 12]),
            "idle2": trace([13, 14, 15]),
        }
        frac = monotonic_nondecreasing_fraction(traces, EXPERIMENTS)
        self.assertEqual(frac, 1.0)

    def test_value_that_returns_to_baseline_is_not_counter_like(self):
        traces = {
            "idle": trace([10, 10]),
            "1000rpm": trace([50, 50]),
            "1650rpm": trace([80, 80]),
            "1900rpm": trace([100, 100]),
            "idle2": trace([10, 10]),  # drops back down -- a real counter never would
        }
        frac = monotonic_nondecreasing_fraction(traces, EXPERIMENTS)
        self.assertLess(frac, 1.0)

    def test_always_at_minimum_detects_pegged_floor(self):
        traces = {
            "idle": trace([0, 0]),
            "1000rpm": trace([0, 0]),
            "1650rpm": trace([0, 0]),
            "1900rpm": trace([0, 5]),  # leaves the floor once
        }
        self.assertFalse(always_at_minimum(traces, ["idle", "1000rpm", "1650rpm", "1900rpm"]))
        traces["1900rpm"] = trace([0, 0])
        self.assertTrue(always_at_minimum(traces, ["idle", "1000rpm", "1650rpm", "1900rpm"]))


class TestBuildTraces(unittest.TestCase):
    def test_reads_correct_bytes_from_grouped_frames(self):
        frames = {
            "idle": {("170", "00"): [frame(1.0, "170", "00AABBCCDDEEFF00")]},
        }
        key = CandidateKey("170", "00", 0, 1, "")
        traces = build_traces(key, frames)
        self.assertEqual(traces["idle"].values, [0xAA])

    def test_unsequenced_record_does_not_strip_leading_byte(self):
        frames = {
            "idle": {("0000B41", ""): [frame(1.0, "0000B41", "8301020304050607")]},
        }
        key = CandidateKey("0000B41", "", 0, 1, "")
        traces = build_traces(key, frames)
        self.assertEqual(traces["idle"].values, [0x83])


if __name__ == "__main__":
    unittest.main()
