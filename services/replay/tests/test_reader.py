import unittest
from pathlib import Path

from . import _pathfix  # noqa: F401

from app.candidates import ReplayCandidate, HYPOTHESIS, RAW
from app.reader import extract, iter_snapshots, load_frames
from smartcraft_toolkit.parser import Frame
from smartcraft_toolkit.signals import CandidateKey

SAMPLES_DIR = Path(__file__).resolve().parents[3] / "tools" / "samples" / "logs"


def frame(ts, can_id, hex_payload):
    return Frame(timestamp=ts, interface="can0", can_id=can_id, data=bytes.fromhex(hex_payload))


RPM_CANDIDATE = ReplayCandidate(
    "RPM candidate", CandidateKey("170", "01", 4, 2, "BE"), HYPOTHESIS, 65, "docs/test",
)
WHOLE_PAYLOAD_CANDIDATE = ReplayCandidate(
    "Whole-payload candidate", CandidateKey("00000B41", "", 0, 1, ""), RAW, -1, "docs/test",
)

# record byte 01, then 7 payload bytes 00 00 00 00 AB CD 00 -- offset 4-5
# (payload[4], payload[5]) = AB, CD. read_value's BE formula is
# low<<8|high where low=payload[offset], high=payload[offset+1], so this
# should read as (0xAB << 8) | 0xCD = 0xABCD.
RPM_FRAME_HEX = "0100000000ABCD00"
RPM_FRAME_VALUE = 0xABCD


class TestExtract(unittest.TestCase):
    def test_matches_correct_can_id_and_record(self):
        f = frame(1.0, "170", RPM_FRAME_HEX)
        self.assertEqual(extract(f, RPM_CANDIDATE), RPM_FRAME_VALUE)

    def test_wrong_can_id_returns_none(self):
        f = frame(1.0, "1A0", RPM_FRAME_HEX)
        self.assertIsNone(extract(f, RPM_CANDIDATE))

    def test_wrong_record_returns_none(self):
        f = frame(1.0, "170", "0200000000ABCD00")  # record 02, not 01
        self.assertIsNone(extract(f, RPM_CANDIDATE))

    def test_short_payload_returns_none(self):
        f = frame(1.0, "170", "010000")  # only 2 bytes after record byte, need offset4+2
        self.assertIsNone(extract(f, RPM_CANDIDATE))

    def test_empty_record_reads_whole_payload(self):
        f = frame(1.0, "00000B41", "2A")
        self.assertEqual(extract(f, WHOLE_PAYLOAD_CANDIDATE), 0x2A)


class TestIterSnapshots(unittest.TestCase):
    def test_yields_only_frames_with_at_least_one_match(self):
        frames = [
            frame(0.0, "170", RPM_FRAME_HEX),  # matches RPM candidate
            frame(0.5, "1A0", "050000000000"),  # matches nothing registered here
            frame(1.0, "00000B41", "2A"),  # matches whole-payload candidate
        ]
        candidates = [RPM_CANDIDATE, WHOLE_PAYLOAD_CANDIDATE]
        results = list(iter_snapshots(frames, candidates))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][1], {"RPM candidate": RPM_FRAME_VALUE})
        self.assertEqual(results[1][1], {"Whole-payload candidate": 0x2A})

    def test_single_frame_can_update_multiple_candidates(self):
        f = frame(0.0, "170", RPM_FRAME_HEX)
        second = ReplayCandidate(
            "Second 170 candidate", CandidateKey("170", "01", 0, 1, ""), RAW, -1, "docs/test",
        )
        results = list(iter_snapshots([f], [RPM_CANDIDATE, second]))
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0][1], {"RPM candidate": RPM_FRAME_VALUE, "Second 170 candidate": 0x00}
        )


class TestLoadFrames(unittest.TestCase):
    def test_loads_and_sorts_a_real_sample_log(self):
        frames = load_frames(SAMPLES_DIR / "idle.txt")
        self.assertGreater(len(frames), 0)
        timestamps = [f.timestamp for f in frames]
        self.assertEqual(timestamps, sorted(timestamps))


if __name__ == "__main__":
    unittest.main()
