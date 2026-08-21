import tempfile
import unittest
from pathlib import Path

from . import _pathfix  # noqa: F401

from app.notimestamp import DEFAULT_SYNTHETIC_INTERVAL_S, load_frames_synthetic_timing, parse_no_timestamp_line


class TestParseNoTimestampLine(unittest.TestCase):
    def test_parses_a_valid_line(self):
        result = parse_no_timestamp_line("  can0  170   [8]  FF 00 00 00 00 00 00 00\n")
        self.assertEqual(result, ("can0", "170", bytes.fromhex("FF00000000000000")))

    def test_parses_an_extended_id(self):
        result = parse_no_timestamp_line("can0  1FFD4041   [8]  05 00 00 01 00 0F 0F 00")
        self.assertEqual(result[1], "1FFD4041")

    def test_uppercases_the_can_id(self):
        result = parse_no_timestamp_line("can0  1a0   [1]  05")
        self.assertEqual(result[1], "1A0")

    def test_rejects_shell_noise(self):
        self.assertIsNone(parse_no_timestamp_line("nohup: ignoring input"))

    def test_rejects_odd_length_hex(self):
        self.assertIsNone(parse_no_timestamp_line("can0  170   [1]  F"))

    def test_rejects_blank_line(self):
        self.assertIsNone(parse_no_timestamp_line(""))


class TestLoadFramesSyntheticTiming(unittest.TestCase):
    def test_assigns_evenly_spaced_synthetic_timestamps_in_file_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "sample.log"
            log_path.write_text(
                "nohup: ignoring input\n"
                "can0  170   [8]  01 00 00 00 00 00 00 00\n"
                "can0  170   [8]  02 00 00 00 00 00 00 00\n"
                "can0  1A0   [8]  03 00 00 00 00 00 00 00\n"
            )
            result = load_frames_synthetic_timing(log_path, interval_s=0.01)

            self.assertEqual(len(result.frames), 3)
            self.assertEqual(len(result.errors), 1)
            self.assertIn("nohup", result.errors[0])
            self.assertAlmostEqual(result.frames[0].timestamp, 0.0)
            self.assertAlmostEqual(result.frames[1].timestamp, 0.01)
            self.assertAlmostEqual(result.frames[2].timestamp, 0.02)
            # order preserved, not sorted by any other key
            self.assertEqual([f.data[0] for f in result.frames], [1, 2, 3])

    def test_default_interval_is_used_when_not_specified(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "sample.log"
            log_path.write_text("can0  170   [1]  00\ncan0  170   [1]  01\n")
            result = load_frames_synthetic_timing(log_path)
            self.assertAlmostEqual(result.frames[1].timestamp - result.frames[0].timestamp, DEFAULT_SYNTHETIC_INTERVAL_S)

    def test_never_writes_to_the_log_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "sample.log"
            original = "can0  170   [1]  00\n"
            log_path.write_text(original)
            load_frames_synthetic_timing(log_path, interval_s=0.01)
            self.assertEqual(log_path.read_text(), original)


if __name__ == "__main__":
    unittest.main()
