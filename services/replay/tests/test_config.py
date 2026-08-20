import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from . import _pathfix  # noqa: F401

from app.config import Config, DEFAULT_LOG


REQUIRED_ENV = {
    "INFLUXDB_ORG": "opencraft",
    "INFLUXDB_BUCKET": "telemetry",
    "INFLUXDB_TOKEN": "test-token",
}


class TestConfigFromArgs(unittest.TestCase):
    def test_default_log_points_at_master_test01(self):
        self.assertTrue(str(DEFAULT_LOG).endswith("master-test01.txt"))

    def test_missing_log_file_exits(self):
        with mock.patch.dict(os.environ, REQUIRED_ENV, clear=False):
            with self.assertRaises(SystemExit):
                Config.from_args(["--log", "/no/such/file.txt"])

    def test_speed_defaults_to_1(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            with mock.patch.dict(os.environ, REQUIRED_ENV, clear=False):
                config = Config.from_args(["--log", f.name])
        self.assertEqual(config.speed_label, "1")
        self.assertEqual(config.speed_multiplier, 1.0)

    def test_max_speed_has_no_multiplier(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            with mock.patch.dict(os.environ, REQUIRED_ENV, clear=False):
                config = Config.from_args(["--log", f.name, "--speed", "max"])
        self.assertIsNone(config.speed_multiplier)

    def test_capture_name_defaults_to_log_filename_stem(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", prefix="my-capture-") as f:
            with mock.patch.dict(os.environ, REQUIRED_ENV, clear=False):
                config = Config.from_args(["--log", f.name])
        self.assertEqual(config.capture_name, Path(f.name).stem)

    def test_capture_name_override(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            with mock.patch.dict(os.environ, REQUIRED_ENV, clear=False):
                config = Config.from_args(["--log", f.name, "--capture-name", "custom"])
        self.assertEqual(config.capture_name, "custom")

    def test_missing_required_env_var_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            env = {k: v for k, v in REQUIRED_ENV.items() if k != "INFLUXDB_TOKEN"}
            with mock.patch.dict(os.environ, env, clear=True):
                with self.assertRaises(RuntimeError):
                    Config.from_args(["--log", f.name])

    def test_influxdb_url_defaults_to_localhost_for_local_dev_use(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            env = dict(REQUIRED_ENV)
            with mock.patch.dict(os.environ, env, clear=True):
                os.environ.pop("INFLUXDB_URL", None)
                config = Config.from_args(["--log", f.name])
        self.assertEqual(config.influxdb_url, "http://localhost:8086")


if __name__ == "__main__":
    unittest.main()
