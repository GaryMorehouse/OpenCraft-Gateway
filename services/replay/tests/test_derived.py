import unittest

from . import _pathfix  # noqa: F401

from app.derived import TrimPositionEstimator


class TestTrimPositionEstimator(unittest.TestCase):
    def test_starts_at_zero_by_default(self):
        e = TrimPositionEstimator()
        self.assertEqual(e.position, 0.0)

    def test_idle_direction_does_not_move_position(self):
        e = TrimPositionEstimator()
        e.update(0, 5.0)
        self.assertEqual(e.position, 0.0)

    def test_up_moves_position_toward_100(self):
        e = TrimPositionEstimator()
        e.update(1, e.FULL_STROKE_S / 2)
        self.assertAlmostEqual(e.position, 50.0, places=3)

    def test_full_stroke_up_reaches_exactly_100(self):
        e = TrimPositionEstimator()
        e.update(1, e.FULL_STROKE_S)
        self.assertAlmostEqual(e.position, 100.0, places=3)

    def test_up_clamps_at_100_even_if_held_longer_than_a_full_stroke(self):
        e = TrimPositionEstimator()
        e.update(1, e.FULL_STROKE_S * 3)
        self.assertEqual(e.position, 100.0)

    def test_down_moves_position_toward_zero_and_clamps(self):
        e = TrimPositionEstimator(start_position=50.0)
        e.update(2, e.FULL_STROKE_S)
        self.assertEqual(e.position, 0.0)
        e.update(2, 100.0)
        self.assertEqual(e.position, 0.0)

    def test_example_from_gary_two_up_clicks_at_1s_each(self):
        # Gary's own example: "2 up clicks at 1s each" against an ~8s full
        # stroke should land around 2/8.275 =~ 24.2%, i.e. roughly the
        # "25%" ballpark he used -- not exact since FULL_STROKE_S is
        # 8.275s, not a round 8s.
        e = TrimPositionEstimator()
        e.update(1, 1.0)
        e.update(1, 1.0)
        self.assertAlmostEqual(e.position, 200.0 / e.FULL_STROKE_S, places=3)
        self.assertAlmostEqual(e.position, 24.17, places=1)

    def test_zero_or_negative_dt_is_a_no_op(self):
        e = TrimPositionEstimator(start_position=42.0)
        e.update(1, 0.0)
        self.assertEqual(e.position, 42.0)


if __name__ == "__main__":
    unittest.main()
