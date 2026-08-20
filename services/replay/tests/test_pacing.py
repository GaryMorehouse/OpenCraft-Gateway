import unittest

from . import _pathfix  # noqa: F401

from app.pacing import SPEED_MULTIPLIERS, pct_complete, playback_delay


class TestPlaybackDelay(unittest.TestCase):
    def test_1x_matches_real_time_gap(self):
        self.assertAlmostEqual(playback_delay(2.0, 1.0), 2.0)

    def test_5x_divides_by_speed(self):
        self.assertAlmostEqual(playback_delay(2.0, 5.0), 0.4)

    def test_10x_divides_by_speed(self):
        self.assertAlmostEqual(playback_delay(1.0, 10.0), 0.1)

    def test_max_speed_has_no_delay_regardless_of_gap(self):
        self.assertEqual(playback_delay(1000.0, None), 0.0)

    def test_negative_or_zero_gap_never_produces_negative_sleep(self):
        self.assertEqual(playback_delay(-5.0, 1.0), 0.0)
        self.assertEqual(playback_delay(0.0, 1.0), 0.0)

    def test_speed_choices_match_cli(self):
        self.assertEqual(set(SPEED_MULTIPLIERS), {"1", "5", "10", "max"})
        self.assertIsNone(SPEED_MULTIPLIERS["max"])
        self.assertEqual(SPEED_MULTIPLIERS["1"], 1.0)


class TestPctComplete(unittest.TestCase):
    def test_halfway(self):
        self.assertAlmostEqual(pct_complete(50.0, 100.0), 50.0)

    def test_zero_duration_is_zero_not_a_crash(self):
        self.assertEqual(pct_complete(5.0, 0.0), 0.0)

    def test_clamped_to_0_100(self):
        self.assertEqual(pct_complete(-10.0, 100.0), 0.0)
        self.assertEqual(pct_complete(150.0, 100.0), 100.0)


if __name__ == "__main__":
    unittest.main()
