import unittest

from . import _pathfix  # noqa: F401

from app.candidates import CANDIDATES, HYPOTHESIS, RAW


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


if __name__ == "__main__":
    unittest.main()
