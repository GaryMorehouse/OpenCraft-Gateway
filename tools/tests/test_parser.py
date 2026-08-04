import unittest
from pathlib import Path

from . import _pathfix  # noqa: F401

from smartcraft_toolkit.parser import parse_file, parse_line, parse_lines

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "idle_excerpt.txt"


class TestParseLine(unittest.TestCase):
    def test_standard_id(self):
        frame = parse_line("(1785862423.342612) can0 170#FF00000000000000")
        self.assertIsNotNone(frame)
        self.assertEqual(frame.timestamp, 1785862423.342612)
        self.assertEqual(frame.interface, "can0")
        self.assertEqual(frame.can_id, "170")
        self.assertEqual(frame.data, bytes.fromhex("FF00000000000000"))

    def test_extended_id(self):
        frame = parse_line("(1785862423.430371) can0 1FFD4041#0201BC0000000000")
        self.assertEqual(frame.can_id, "1FFD4041")
        self.assertEqual(frame.data, bytes.fromhex("0201BC0000000000"))

    def test_lowercase_id_is_normalized_uppercase(self):
        frame = parse_line("(1.0) can0 1ffd4041#0201bc0000000000")
        self.assertEqual(frame.can_id, "1FFD4041")
        self.assertEqual(frame.data, bytes.fromhex("0201BC0000000000"))

    def test_malformed_line_returns_none(self):
        self.assertIsNone(parse_line("this is not a candump line"))

    def test_odd_length_data_returns_none(self):
        self.assertIsNone(parse_line("(1.0) can0 170#ABC"))

    def test_empty_payload_is_valid(self):
        frame = parse_line("(1.0) can0 100#")
        self.assertIsNotNone(frame)
        self.assertEqual(frame.data, b"")


class TestParseLines(unittest.TestCase):
    def test_malformed_lines_are_collected_not_dropped_silently(self):
        result = parse_lines(
            [
                "(1.0) can0 170#FF00000000000000",
                "garbage line",
                "(2.0) can0 170#0002470415A8FFFF",
            ]
        )
        self.assertEqual(len(result.frames), 2)
        self.assertEqual(result.errors, ["garbage line"])

    def test_blank_lines_are_skipped_without_error(self):
        result = parse_lines(["(1.0) can0 170#FF00000000000000", "", "   "])
        self.assertEqual(len(result.frames), 1)
        self.assertEqual(result.errors, [])


class TestParseFile(unittest.TestCase):
    def test_parses_real_fixture(self):
        result = parse_file(FIXTURE)
        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.frames), 80)
        can_ids = {frame.can_id for frame in result.frames}
        self.assertEqual(can_ids, {"170", "1A0", "1FFD4041"})


if __name__ == "__main__":
    unittest.main()
