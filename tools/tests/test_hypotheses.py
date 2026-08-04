import unittest

from . import _pathfix  # noqa: F401

from smartcraft_toolkit.experiments import Experiment
from smartcraft_toolkit.hypotheses import (
    CandidateFeatures,
    compute_features,
    score_battery_voltage,
    score_coolant_temperature,
    score_fuel_or_depth,
    score_oil_pressure,
    score_raw_water_pressure,
    score_rpm,
)
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


def features_from(traces_dict):
    return compute_features(KEY, traces_dict, EXPERIMENTS)


class TestRpmScoring(unittest.TestCase):
    def test_clean_rpm_signal_scores_high_confidence(self):
        traces = {
            "idle": trace([10, 10, 11]),
            "1000rpm": trace([40, 41, 40]),
            "1650rpm": trace([70, 71, 70]),
            "1900rpm": trace([100, 101, 100]),
            "idle2": trace([10, 11, 10]),
        }
        result = score_rpm(features_from(traces))
        self.assertGreaterEqual(result.confidence, 70)
        self.assertTrue(result.evidence_for)

    def test_flat_signal_scores_low_confidence_with_stated_reason(self):
        traces = {name: trace([50, 50, 50]) for name in ["idle", "1000rpm", "1650rpm", "1900rpm", "idle2"]}
        result = score_rpm(features_from(traces))
        self.assertLess(result.confidence, 30)
        self.assertTrue(any("barely changes" in reason for reason in result.evidence_against))

    def test_ever_increasing_counter_is_penalized_even_though_it_correlates_with_rpm_order(self):
        traces = {
            "idle": trace([1, 2]),
            "1000rpm": trace([10, 11]),
            "1650rpm": trace([20, 21]),
            "1900rpm": trace([30, 31]),
            "idle2": trace([40, 41]),  # keeps climbing instead of returning to idle's value
        }
        result = score_rpm(features_from(traces))
        self.assertTrue(any("counter" in reason for reason in result.evidence_against))

    def test_every_result_carries_a_suggested_experiment(self):
        traces = {name: trace([1, 2, 3]) for name in ["idle", "1000rpm", "1650rpm", "1900rpm", "idle2"]}
        result = score_rpm(features_from(traces))
        self.assertTrue(result.suggested_experiment)


class TestOilPressureScoring(unittest.TestCase):
    def test_rises_with_rpm_but_drops_between_idle_and_idle2_scores_well(self):
        traces = {
            "idle": trace([60, 60]),
            "1000rpm": trace([65, 65]),
            "1650rpm": trace([70, 70]),
            "1900rpm": trace([75, 75]),
            "idle2": trace([50, 50]),  # lower than idle -- warmed up
        }
        result = score_oil_pressure(features_from(traces))
        self.assertGreaterEqual(result.confidence, 50)

    def test_rises_between_idle_and_idle2_contradicts_hypothesis(self):
        traces = {
            "idle": trace([60, 60]),
            "1000rpm": trace([65, 65]),
            "1650rpm": trace([70, 70]),
            "1900rpm": trace([75, 75]),
            "idle2": trace([90, 90]),  # rose instead of dropping
        }
        result = score_oil_pressure(features_from(traces))
        self.assertTrue(any("opposite" in reason for reason in result.evidence_against))


class TestRawWaterPressureScoring(unittest.TestCase):
    def test_lowest_at_idle_and_increases_with_rpm_scores_well(self):
        traces = {
            "idle": trace([5, 5]),
            "1000rpm": trace([20, 20]),
            "1650rpm": trace([35, 35]),
            "1900rpm": trace([50, 50]),
            "idle2": trace([5, 5]),
        }
        result = score_raw_water_pressure(features_from(traces))
        self.assertGreaterEqual(result.confidence, 50)

    def test_pegged_at_zero_even_at_full_rpm_contradicts_hypothesis(self):
        traces = {name: trace([0, 0]) for name in ["idle", "1000rpm", "1650rpm", "1900rpm", "idle2"]}
        result = score_raw_water_pressure(features_from(traces))
        self.assertLess(result.confidence, 30)

    def test_always_notes_the_untestable_engine_off_floor(self):
        traces = {
            "idle": trace([5, 5]),
            "1000rpm": trace([20, 20]),
            "1650rpm": trace([35, 35]),
            "1900rpm": trace([50, 50]),
            "idle2": trace([5, 5]),
        }
        result = score_raw_water_pressure(features_from(traces))
        self.assertTrue(any("untestable" in reason for reason in result.evidence_against))


class TestBatteryVoltageScoring(unittest.TestCase):
    def test_flat_across_rpm_scores_better_than_rpm_correlated(self):
        # same mean (~140) in every experiment, jitter only within each one --
        # a 1-count wobble on a 4-point rank correlation is noise-dominated,
        # so give it enough samples per experiment that the means actually tie
        flat_traces = {
            "idle": trace([140, 142, 138, 140]),
            "1000rpm": trace([141, 139, 140, 142]),
            "1650rpm": trace([139, 141, 140, 138]),
            "1900rpm": trace([140, 138, 142, 140]),
            "idle2": trace([142, 140, 138, 141]),
        }
        rpm_like_traces = {
            "idle": trace([10, 10]),
            "1000rpm": trace([40, 40]),
            "1650rpm": trace([70, 70]),
            "1900rpm": trace([100, 100]),
            "idle2": trace([10, 10]),
        }
        flat_result = score_battery_voltage(features_from(flat_traces))
        rpm_like_result = score_battery_voltage(features_from(rpm_like_traces))
        self.assertGreater(flat_result.confidence, rpm_like_result.confidence)

    def test_always_flags_missing_key_on_step_test(self):
        traces = {name: trace([140, 141]) for name in ["idle", "1000rpm", "1650rpm", "1900rpm", "idle2"]}
        result = score_battery_voltage(features_from(traces))
        self.assertTrue(any("step" in reason for reason in result.evidence_against))


class TestFuelOrDepthScoring(unittest.TestCase):
    def test_near_constant_with_minor_noise_scores_moderately(self):
        traces = {
            "idle": trace([120, 121, 120]),
            "1000rpm": trace([121, 120, 121]),
            "1650rpm": trace([120, 121, 120]),
            "1900rpm": trace([121, 120, 121]),
            "idle2": trace([120, 121, 120]),
        }
        result = score_fuel_or_depth(features_from(traces))
        self.assertGreaterEqual(result.confidence, 20)
        self.assertTrue(any("indistinguishable" in reason for reason in result.evidence_against))

    def test_rpm_correlated_signal_is_penalized(self):
        traces = {
            "idle": trace([10, 10]),
            "1000rpm": trace([40, 40]),
            "1650rpm": trace([70, 70]),
            "1900rpm": trace([100, 100]),
            "idle2": trace([10, 10]),
        }
        result = score_fuel_or_depth(features_from(traces))
        self.assertTrue(any("RPM" in reason for reason in result.evidence_against))


if __name__ == "__main__":
    unittest.main()
