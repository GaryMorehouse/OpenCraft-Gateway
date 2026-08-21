import unittest

from . import _pathfix  # noqa: F401

from app.candidates import CANDIDATES, FITTED, HYPOTHESIS, RAW, UNANCHORED, Guess, InterpolatedGuess


class TestCandidateTable(unittest.TestCase):
    def test_labels_are_unique(self):
        labels = [c.label for c in CANDIDATES]
        self.assertEqual(len(labels), len(set(labels)), "duplicate candidate labels")

    def test_every_candidate_has_a_valid_tier(self):
        for c in CANDIDATES:
            self.assertIn(c.tier, (HYPOTHESIS, RAW), c.label)

    def test_every_candidate_cites_a_source(self):
        for c in CANDIDATES:
            self.assertTrue(c.source, c.label)
            self.assertIn("docs/", c.source, c.label)

    def test_can_ids_are_uppercase_hex(self):
        for c in CANDIDATES:
            self.assertEqual(c.key.can_id, c.key.can_id.upper(), c.label)
            int(c.key.can_id, 16)  # raises if not valid hex

    def test_confidence_is_percentage_or_unscored_sentinel(self):
        for c in CANDIDATES:
            self.assertTrue(c.confidence_pct == -1 or 0 <= c.confidence_pct <= 100, c.label)

    def test_hypothesis_tier_only_used_for_moderate_or_better_confidence(self):
        # Mirrors this replay tool's own documented rule (candidates.py's
        # module docstring): "hypothesis" is reserved for candidates the
        # analysis report calls at least moderate confidence -- OR that are
        # unscored (-1) because they aren't one of the formal Phase 2 tool's
        # 6 named hypotheses at all (e.g. Engine Hours), as opposed to
        # having been scored and found weak. -1 is never used as a way to
        # dodge this rule for one of the 6 named hypotheses.
        NAMED_HYPOTHESES = {"RPM", "Coolant Temperature", "Oil Pressure",
                             "Raw Water Pressure", "Fuel Level", "Depth",
                             "Battery Voltage"}
        for c in CANDIDATES:
            if c.tier != HYPOTHESIS:
                continue
            is_named = any(c.label.startswith(name) for name in NAMED_HYPOTHESES)
            if is_named:
                self.assertGreaterEqual(c.confidence_pct, 50, c.label)
            else:
                self.assertEqual(c.confidence_pct, -1, c.label)

    def test_every_guess_has_a_valid_basis_unit_and_note(self):
        for c in CANDIDATES:
            if c.guess is None:
                continue
            self.assertIn(c.guess.basis, (FITTED, UNANCHORED), c.label)
            self.assertTrue(c.guess.unit, c.label)
            self.assertTrue(c.guess.note, c.label)

    def test_status_flag_candidate_has_no_guess(self):
        # A structural status/counter byte isn't a physical quantity -- no
        # unit guess should be attached to it.
        status_flag = next(c for c in CANDIDATES if c.label == "Engine/mode status flag")
        self.assertIsNone(status_flag.guess)

    def test_rpm_candidate_uses_interpolated_guess(self):
        # RPM is one of the candidates with enough real anchor points to show
        # its response isn't a single straight line -- confirm it's using
        # the piecewise mechanism, not a plain Guess.
        rpm = next(c for c in CANDIDATES if c.label == "RPM candidate")
        self.assertIsInstance(rpm.guess, InterpolatedGuess)

    def test_water_candidate_uses_interpolated_guess(self):
        water = next(c for c in CANDIDATES if c.label == "Raw Water Pressure candidate")
        self.assertIsInstance(water.guess, InterpolatedGuess)

    def test_water_candidate_is_hypothesis_tier_after_cross_validation(self):
        # Upgraded from raw back to hypothesis on 2026-08-19 after its fit
        # (built from one RPM step test) predicted a second, independent
        # test's readings well -- see the Guess note for the numbers.
        water = next(c for c in CANDIDATES if c.label == "Raw Water Pressure candidate")
        self.assertEqual(water.tier, HYPOTHESIS)

    def test_coolant_steady_candidate_uses_interpolated_guess_and_stays_named(self):
        # New leading coolant candidate, 2026-08-20: found after Gary
        # reported the deployed candidate collapsing well below 152F near
        # the end of the test, when real coolant should hold steady there.
        # Named "Coolant Temperature ..." so held to the >=50% rule.
        coolant2 = next(c for c in CANDIDATES if c.label == "Coolant Temperature candidate (steady)")
        self.assertEqual(coolant2.tier, HYPOTHESIS)
        self.assertGreaterEqual(coolant2.confidence_pct, 50)
        self.assertIsInstance(coolant2.guess, InterpolatedGuess)
        self.assertAlmostEqual(coolant2.guess.apply(35), 95.0)
        self.assertAlmostEqual(coolant2.guess.apply(71), 159.0)

    def test_water_pressure_rpm_proxy_shares_water_candidates_key_and_is_unscored(self):
        # Derived estimate, 2026-08-21: same raw byte as Raw Water Pressure,
        # just mapped to RPM using the same real-world anchor moments.
        # Doesn't start with any of the 6 named-hypothesis prefixes, so
        # unscored (-1) is correct even though its label mentions RPM.
        proxy = next(c for c in CANDIDATES if c.label == "Water-Pressure RPM Proxy candidate")
        water = next(c for c in CANDIDATES if c.label == "Raw Water Pressure candidate")
        self.assertEqual(proxy.key, water.key)
        self.assertEqual(proxy.tier, HYPOTHESIS)
        self.assertEqual(proxy.confidence_pct, -1)
        self.assertIsInstance(proxy.guess, InterpolatedGuess)
        self.assertEqual(proxy.guess.unit, "RPM")
        self.assertAlmostEqual(proxy.guess.apply(45385), 2570)

    def test_oil_pressure_inverse_candidate_uses_interpolated_guess_at_moderate_confidence(self):
        # New leading oil-pressure candidate, 2026-08-20: an inversely
        # correlated byte, cross-validated against a second independent
        # RPM test (see the Guess note). Named "Oil Pressure ..." so it's
        # held to the >=50% rule like the other 6 named hypotheses, not
        # treated as an unscored structural finding.
        oil2 = next(c for c in CANDIDATES if c.label == "Oil Pressure candidate (inverse byte3)")
        self.assertEqual(oil2.tier, HYPOTHESIS)
        self.assertGreaterEqual(oil2.confidence_pct, 50)
        self.assertIsInstance(oil2.guess, InterpolatedGuess)
        # anchors are inversely ordered: lowest raw -> highest real PSI
        raws = [p[0] for p in oil2.guess.points]
        self.assertEqual(raws, sorted(raws))
        self.assertAlmostEqual(oil2.guess.apply(11), 65.9)
        self.assertAlmostEqual(oil2.guess.apply(39), 0.5)

    def test_trim_direction_candidate_is_unscored_hypothesis_with_signed_interpolated_guess(self):
        # New structural finding, 2026-08-20: exactly 6 pulses alternating
        # between two raw values, occurring nowhere else in the whole file,
        # matching the field sheet's 6 documented trim movements in both
        # count and order. Not one of the formal tool's 6 named hypotheses,
        # so unscored (-1) rather than percent-rated.
        trim_dir = next(c for c in CANDIDATES if c.label == "Trim Direction candidate")
        self.assertEqual(trim_dir.tier, HYPOTHESIS)
        self.assertEqual(trim_dir.confidence_pct, -1)
        self.assertIsInstance(trim_dir.guess, InterpolatedGuess)
        self.assertAlmostEqual(trim_dir.guess.apply(0), 0.0)
        self.assertAlmostEqual(trim_dir.guess.apply(1), 1.0)
        self.assertAlmostEqual(trim_dir.guess.apply(2), -1.0)

    def test_trim_position_estimate_candidate_is_unscored_with_passthrough_guess(self):
        # Derived (not raw-CAN-read) candidate, 2026-08-20: dead-reckons
        # trim position by integrating the Trim Direction candidate over
        # time (see app/derived.py). scale=1/offset=0 because 'value' for
        # this candidate is already the estimated percentage.
        est = next(c for c in CANDIDATES if c.label == "Trim Estimated Position (derived)")
        self.assertEqual(est.tier, HYPOTHESIS)
        self.assertEqual(est.confidence_pct, -1)
        self.assertIsInstance(est.guess, Guess)
        self.assertEqual(est.guess.scale, 1.0)
        self.assertEqual(est.guess.offset, 0.0)
        self.assertAlmostEqual(est.guess.apply(37), 37.0)

    def test_trim_position_estimate_key_never_matches_a_real_frame(self):
        # Its CandidateKey is a placeholder (this candidate's value is
        # computed in main.py, not read from the log) -- confirm the
        # placeholder ID doesn't collide with any real CAN ID this project
        # knows about.
        est = next(c for c in CANDIDATES if c.label == "Trim Estimated Position (derived)")
        real_ids = {c.key.can_id for c in CANDIDATES if c.label != est.label}
        self.assertNotIn(est.key.can_id, real_ids)

    def test_engine_hours_candidate_is_unscored_hypothesis_with_plain_guess(self):
        # New structural finding, 2026-08-20: a wall-clock-driven counter
        # (~59.58s/tick, stdev 0.006s across 21 ticks) categorically unlike
        # the frame-driven counters elsewhere in the capture. Not one of the
        # formal tool's 6 named hypotheses, so it's unscored (-1) rather than
        # given a numeric confidence.
        hours = next(c for c in CANDIDATES if c.label == "Engine Hours/Minutes candidate")
        self.assertEqual(hours.tier, HYPOTHESIS)
        self.assertEqual(hours.confidence_pct, -1)
        self.assertIsInstance(hours.guess, Guess)
        self.assertEqual(hours.guess.unit, "min")
        # anchor: raw 23 at key-on rebases to 0 minutes elapsed
        self.assertAlmostEqual(hours.guess.apply(23), 0.0)


class TestGuess(unittest.TestCase):
    def test_apply_scales_and_offsets(self):
        g = Guess(scale=0.5, offset=10, unit="X", basis=FITTED, note="test")
        self.assertAlmostEqual(g.apply(100), 60.0)

    def test_apply_zero_scale_returns_offset(self):
        g = Guess(scale=0.0, offset=42, unit="X", basis=UNANCHORED, note="test")
        self.assertAlmostEqual(g.apply(999), 42.0)


class TestInterpolatedGuess(unittest.TestCase):
    def setUp(self):
        self.g = InterpolatedGuess(
            points=((0, 0), (100, 10), (200, 100)),
            unit="X", basis=FITTED, note="test",
        )

    def test_exact_anchor_points_return_the_anchor_value(self):
        self.assertAlmostEqual(self.g.apply(0), 0)
        self.assertAlmostEqual(self.g.apply(100), 10)
        self.assertAlmostEqual(self.g.apply(200), 100)

    def test_interpolates_between_two_points_on_the_same_segment(self):
        # halfway through the first (shallow) segment
        self.assertAlmostEqual(self.g.apply(50), 5.0)
        # halfway through the second (steep) segment
        self.assertAlmostEqual(self.g.apply(150), 55.0)

    def test_extrapolates_below_the_first_point_using_its_segment_slope(self):
        # segment 0: slope = (10-0)/(100-0) = 0.1
        self.assertAlmostEqual(self.g.apply(-100), -10.0)

    def test_extrapolates_above_the_last_point_using_its_segment_slope(self):
        # segment 1: slope = (100-10)/(200-100) = 0.9
        self.assertAlmostEqual(self.g.apply(300), 190.0)

    def test_rpm_candidates_own_anchor_points_are_internally_consistent(self):
        rpm_guess = next(c for c in CANDIDATES if c.label == "RPM candidate").guess
        # each confirmed anchor must round-trip exactly
        for raw, real in rpm_guess.points:
            self.assertAlmostEqual(rpm_guess.apply(raw), real)


if __name__ == "__main__":
    unittest.main()
