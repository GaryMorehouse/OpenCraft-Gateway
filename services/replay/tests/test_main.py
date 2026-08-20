import unittest

from . import _pathfix  # noqa: F401

from app.candidates import (
    CANDIDATES,
    HYPOTHESIS,
    ReplayCandidate,
    TRIM_DIRECTION_LABEL,
    TRIM_POSITION_ESTIMATE_LABEL,
)
from app.config import Config
from app.main import Controls, run
from smartcraft_toolkit.parser import Frame
from smartcraft_toolkit.signals import CandidateKey

TEST_CANDIDATE = ReplayCandidate(
    "Test candidate", CandidateKey("170", "01", 0, 1, ""), HYPOTHESIS, 90, "docs/test",
)


class FakePublisher:
    def __init__(self):
        self.candidate_calls = []
        self.status_calls = []
        self.closed = False

    def publish_candidates(self, capture, values, by_label):
        self.candidate_calls.append((capture, dict(values)))

    def publish_status(self, capture, state, position_s, duration_s, speed_label):
        self.status_calls.append((capture, state, position_s, duration_s, speed_label))

    def close(self):
        self.closed = True


def make_config(tmp_log, **overrides):
    defaults = dict(
        log_path=tmp_log,
        capture_name="unit-test",
        speed_label="max",
        speed_multiplier=None,
        publish_interval_s=0.0,
        influxdb_url="unused",
        influxdb_org="unused",
        influxdb_bucket="unused",
        influxdb_token="unused",
    )
    defaults.update(overrides)
    return Config(**defaults)


def write_log(path, lines):
    path.write_text("\n".join(lines) + "\n")


class TestControls(unittest.TestCase):
    def test_p_toggles_paused(self):
        c = Controls(read_stdin=False)
        self.assertFalse(c.paused)
        c.handle("p")
        self.assertTrue(c.paused)
        c.handle("p")
        self.assertFalse(c.paused)

    def test_r_sets_restart_and_clears_paused(self):
        c = Controls(read_stdin=False)
        c.paused = True
        c.handle("r")
        self.assertTrue(c.restart)
        self.assertFalse(c.paused)

    def test_q_sets_stop(self):
        c = Controls(read_stdin=False)
        c.handle("q")
        self.assertTrue(c.stop)

    def test_unrecognized_command_does_nothing(self):
        c = Controls(read_stdin=False)
        c.handle("banana")
        self.assertFalse(c.paused or c.stop or c.restart)


class TestRun(unittest.TestCase):
    def test_plays_to_finish_then_stops_on_command(self, tmp_path=None):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "sample.log"
            write_log(
                log_path,
                [
                    "(1000.000000) can0 170#0100000000000000",
                    "(1000.100000) can0 170#0101000000000000",
                ],
            )
            config = make_config(log_path)
            controls = Controls(read_stdin=False)
            publisher = FakePublisher()

            # speed=max means no sleeps happen during playback itself (see
            # pacing.playback_delay) -- the only sleep() calls come from the
            # "idle after finished, waiting for restart/stop" loop. Stop on
            # the first such call so the test doesn't hang.
            calls = {"n": 0}

            def fake_sleep(seconds):
                calls["n"] += 1
                controls.stop = True

            run(
                config, controls=controls, sleep=fake_sleep, publisher=publisher,
                candidates=[TEST_CANDIDATE],
            )

            self.assertGreaterEqual(calls["n"], 1)
            self.assertTrue(publisher.closed)
            states = [call[1] for call in publisher.status_calls]
            self.assertIn("playing", states)
            self.assertIn("finished", states)
            self.assertEqual(states[-1], "stopped")
            # both frames update "Test candidate" (offset 0 of the record-01
            # payload) -- 0x00 then 0x01 -- so the last published value
            # should be the final one, 0x01
            last_candidate_values = publisher.candidate_calls[-1][1]
            self.assertEqual(last_candidate_values["Test candidate"], 0x01)

    def test_trim_position_estimate_integrates_direction_over_elapsed_time(self):
        import tempfile
        from pathlib import Path

        # 170 record 03: record byte 03, then 7 payload bytes; byte offset 2
        # of the payload is the Trim Direction candidate. First frame sets
        # it to 1 (Up) at t=1000.0; second frame sets it back to 0 (idle)
        # at t=1002.0 -- i.e. "Up" was in effect for the 2.0s gap between
        # them, matching Gary's own "N seconds of a click" framing.
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "sample.log"
            write_log(
                log_path,
                [
                    "(1000.000000) can0 170#0300000100000000",
                    "(1002.000000) can0 170#0300000000000000",
                ],
            )
            config = make_config(log_path)
            controls = Controls(read_stdin=False)
            publisher = FakePublisher()
            calls = {"n": 0}

            def fake_sleep(seconds):
                calls["n"] += 1
                controls.stop = True

            direction_candidate = next(c for c in CANDIDATES if c.label == TRIM_DIRECTION_LABEL)
            estimate_candidate = next(c for c in CANDIDATES if c.label == TRIM_POSITION_ESTIMATE_LABEL)

            run(
                config, controls=controls, sleep=fake_sleep, publisher=publisher,
                candidates=[direction_candidate, estimate_candidate],
            )

            last_values = publisher.candidate_calls[-1][1]
            # 2.0s of "Up" against an 8.275s full stroke =~ 24.17%, rounded
            self.assertEqual(last_values[TRIM_POSITION_ESTIMATE_LABEL], 24)
            self.assertEqual(last_values[TRIM_DIRECTION_LABEL], 0)

    def test_stop_before_any_frame_still_publishes_stopped_status(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "sample.log"
            write_log(log_path, ["(1000.000000) can0 170#0100000000000000"])
            config = make_config(log_path)
            controls = Controls(read_stdin=False)
            controls.stop = True  # stop requested before run() even starts
            publisher = FakePublisher()

            run(
                config, controls=controls, sleep=lambda s: None, publisher=publisher,
                candidates=[TEST_CANDIDATE],
            )

            self.assertTrue(publisher.closed)
            self.assertEqual(publisher.status_calls[-1][1], "stopped")


if __name__ == "__main__":
    unittest.main()
