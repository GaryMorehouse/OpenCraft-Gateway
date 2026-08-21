import unittest

from . import _pathfix  # noqa: F401

from app.candidates import FITTED, ReplayCandidate, RAW, Guess
from app.config import Config
from app.publisher import ReplayPublisher
from smartcraft_toolkit.signals import CandidateKey

WITH_GUESS = ReplayCandidate(
    "With guess", CandidateKey("170", "01", 0, 1, ""), RAW, -1, "docs/test",
    Guess(scale=2.0, offset=1.0, unit="PSI", basis=FITTED, note="test"),
)
WITHOUT_GUESS = ReplayCandidate(
    "Without guess", CandidateKey("170", "01", 1, 1, ""), RAW, -1, "docs/test", None,
)


def make_config():
    return Config(
        log_path=__file__,  # unused -- publisher never touches this
        capture_name="unit-test",
        speed_label="1",
        speed_multiplier=1.0,
        publish_interval_s=1.0,
        influxdb_url="http://unused.invalid:8086",
        influxdb_org="unused",
        influxdb_bucket="unused",
        influxdb_token="unused",
    )


class RecordingPublisher(ReplayPublisher):
    """A ReplayPublisher that records the Points it would write instead of
    actually writing them, so this can be tested without a real InfluxDB."""

    def __init__(self, config):
        self._config = config
        self.written = []

    def _write(self, points):
        self.written.extend(points)


class TestPublishCandidates(unittest.TestCase):
    def test_candidate_with_guess_gets_guess_value_field_and_unit_tag(self):
        pub = RecordingPublisher(make_config())
        by_label = {"With guess": WITH_GUESS}
        pub.publish_candidates("master-test01", {"With guess": 10}, by_label)

        self.assertEqual(len(pub.written), 1)
        line = pub.written[0].to_line_protocol()
        self.assertIn("value=10i", line)
        self.assertIn("guess_value=21", line)  # 10*2.0 + 1.0
        self.assertIn('unit=PSI', line)
        self.assertIn('tier=raw', line)

    def test_candidate_without_guess_has_no_guess_value_field(self):
        pub = RecordingPublisher(make_config())
        by_label = {"Without guess": WITHOUT_GUESS}
        pub.publish_candidates("master-test01", {"Without guess": 5}, by_label)

        line = pub.written[0].to_line_protocol()
        self.assertIn("value=5i", line)
        self.assertNotIn("guess_value", line)
        # influxdb-client drops empty-string tags from line protocol entirely
        # rather than writing unit= -- absence is the correct signal here.
        self.assertNotIn("unit=", line)


class TestPublishStatus(unittest.TestCase):
    def test_timing_mode_defaults_to_real(self):
        pub = RecordingPublisher(make_config())
        pub.publish_status("master-test01", "playing", 0.0, 100.0, "1")
        line = pub.written[0].to_line_protocol()
        self.assertIn('timing_mode="real"', line)

    def test_timing_mode_can_be_set_to_synthetic(self):
        pub = RecordingPublisher(make_config())
        pub.publish_status("drive03", "playing", 0.0, 100.0, "1", timing_mode="synthetic")
        line = pub.written[0].to_line_protocol()
        self.assertIn('timing_mode="synthetic"', line)


if __name__ == "__main__":
    unittest.main()
