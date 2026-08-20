"""Derived (computed, not read-from-a-CAN-byte) replay signals.

Unlike every entry in candidates.py, these values aren't extracted from a
byte position via reader.py's extract() -- they're computed by
integrating an existing candidate's raw value over elapsed time. Kept
structurally separate from the CandidateKey-based lookups because there's
no byte position to read: the value only exists as running state, updated
frame-by-frame in main.py's playback loop.
"""
from __future__ import annotations


class TrimPositionEstimator:
    """Dead-reckons an estimated trim position (0 = full down, 100 = full
    up) by integrating the Trim Direction candidate's raw value (0=idle,
    1=up, 2=down) over elapsed simulated time, on the assumption that each
    of that candidate's ~8s pulses represents one full end-to-end stroke.

    Gary's own proposed technique (2026-08-20): if a full stroke takes
    ~8.3s, N seconds of a commanded Up/Down pulse should move trim
    roughly N/8.3 of the way across its range. The full-stroke assumption
    is grounded in two things: the field sheet documents each of the 6
    movements in this capture as a FULL up or FULL down stroke (not a
    partial tap), and the 6 measured pulse durations are tightly
    clustered (8.04-8.64s) -- consistent with each one reaching the
    physical end of travel rather than an arbitrarily-held button. See
    docs/master-test01-analysis.md section 12.

    Never independently validated against a real intermediate trim
    position reading -- this capture's field sheet only documents the
    full-down/full-up endpoints, not any position in between. A search for
    an independent min/max limit-switch signal to calibrate or validate
    this assumption against (2026-08-20) found no clean candidate. Treat
    this as an illustrative estimate, the same caution as every Guess/
    InterpolatedGuess in candidates.py, not a confirmed decode.
    """

    FULL_STROKE_S = 8.275  # mean of the 6 measured pulse durations in
    # master-test01 (8.640, 8.639, 8.143, 8.143, 8.043, 8.043s) -- see
    # docs/master-test01-analysis.md section 12.

    def __init__(self, start_position: float = 0.0) -> None:
        self.position = start_position
        self._rate_pct_per_s = 100.0 / self.FULL_STROKE_S

    def update(self, direction_raw: int, dt: float) -> float:
        if dt > 0:
            if direction_raw == 1:  # Up
                self.position = min(100.0, self.position + self._rate_pct_per_s * dt)
            elif direction_raw == 2:  # Down
                self.position = max(0.0, self.position - self._rate_pct_per_s * dt)
        return self.position
