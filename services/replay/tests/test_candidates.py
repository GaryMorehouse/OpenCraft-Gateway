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
        # analysis report calls at least moderate confidence.
        for c in CANDIDATES:
            if c.tier == HYPOTHESIS:
                self.assertGreaterEqual(c.confidence_pct, 50, c.label)

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
        # RPM is the one candidate with enough real anchor points to show
        # its response isn't a single straight line -- confirm it's using
        # the piecewise mechanism, not a plain Guess.
        rpm = next(c for c in CANDIDATES if c.label == "RPM candidate")
        self.assertIsInstance(rpm.guess, InterpolatedGuess)


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
