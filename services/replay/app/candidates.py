"""The exact set of candidate CAN fields this replay tool surfaces,
transcribed directly from the evidence-scored hypotheses already published
in docs/master-test01-analysis.md and docs/HypothesisReport.md.

This module adds NO new CAN decoding. Every entry below names a byte/word
location that tools/smartcraft_toolkit's Phase 2 hypothesis engine already
scored against real capture evidence; nothing is invented for replay.

`tier` reflects that published assessment, per the replay task's own
instructions:

    "hypothesis" -- docs/master-test01-analysis.md calls this candidate at
                    least "moderate" confidence.
    "raw"       -- that report calls the candidate "weak" or leaves it
                   unscored.

Every candidate's raw CAN value (`app.reader.extract`) is never itself
unit-converted -- the published confidence only identifies *which byte*,
never a scale factor. `guess`, below, is a SEPARATE, clearly-labeled,
purely illustrative layer added on top of that raw value, at Gary's
explicit request, so gauge panels can show a plausible-looking number
instead of a bare integer -- it is a guess, not a decode, and is kept
completely apart from anything docs/master-test01-analysis.md asserts as
evidence. Never mistake `guess.value` for a confirmed reading; the raw
`value` remains the only thing this tool actually measured.

Re-run `python tools/smartcraft_decoder.py hypotheses` and update
docs/master-test01-analysis.md before changing any tier or confidence
value here -- this table should always follow the evidence, never the
other way around. To replay a different capture with its own candidate
bytes, add a new list here (or a new module) rather than editing these
master-test01-specific entries in place.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from smartcraft_toolkit.signals import CandidateKey

HYPOTHESIS = "hypothesis"
RAW = "raw"

# How a guess was arrived at, for the panel description -- distinguishes an
# (still unconfirmed) estimate anchored to a real field-sheet reading from a
# pure placeholder assumption with nothing behind it.
FITTED = "fitted"  # scale/offset solved from >=1 real field-sheet data point
UNANCHORED = "unanchored"  # scale/offset assumed (e.g. "byte range = 0-100%"), not fitted to any known reading


@dataclass(frozen=True)
class Guess:
    """A single straight-line scale/offset guess. Use this unless there's
    evidence the candidate's response is non-linear (see InterpolatedGuess)."""

    scale: float
    offset: float
    unit: str
    basis: str  # FITTED or UNANCHORED
    note: str  # human-readable explanation, shown in the panel description

    def apply(self, raw_value: int) -> float:
        return raw_value * self.scale + self.offset


@dataclass(frozen=True)
class InterpolatedGuess:
    """A guess built from >=2 confirmed (raw, real_value) anchor points,
    linearly interpolated between neighbors and linearly extrapolated beyond
    the first/last point using that nearest segment's slope.

    Exists because at least one candidate (RPM) has enough real anchor
    points now to show its response genuinely isn't a single straight line
    -- forcing one `Guess` scale/offset across the whole range fits none of
    the segments well. This is still a guess, not a decode: interpolating
    between real points is a reasonable estimate: extrapolating beyond the
    last confirmed point is a much shakier one, and callers should treat
    values past `points[-1][0]` accordingly.
    """

    points: tuple[tuple[float, float], ...]  # (raw, real_value), sorted ascending by raw
    unit: str
    basis: str  # always FITTED -- an InterpolatedGuess with no real anchors isn't meaningful
    note: str

    def apply(self, raw_value: int) -> float:
        pts = self.points
        if raw_value <= pts[0][0]:
            (r0, v0), (r1, v1) = pts[0], pts[1]
        elif raw_value >= pts[-1][0]:
            (r0, v0), (r1, v1) = pts[-2], pts[-1]
        else:
            (r0, v0), (r1, v1) = pts[0], pts[1]  # overwritten by the loop below
            for i in range(len(pts) - 1):
                if pts[i][0] <= raw_value <= pts[i + 1][0]:
                    (r0, v0), (r1, v1) = pts[i], pts[i + 1]
                    break
        slope = (v1 - v0) / (r1 - r0)
        return v0 + (raw_value - r0) * slope


@dataclass(frozen=True)
class ReplayCandidate:
    label: str  # panel-facing name; also the InfluxDB "hypothesis" tag value
    key: CandidateKey
    tier: str  # HYPOTHESIS or RAW
    confidence_pct: int  # -1 if unscored by the formal Phase 2 engine
    source: str  # where this assessment is documented, for traceability
    guess: Optional[Union[Guess, InterpolatedGuess]] = None  # None = no defensible guess; show raw only


MASTER_TEST01_CANDIDATES: list[ReplayCandidate] = [
    ReplayCandidate(
        "RPM candidate", CandidateKey("170", "01", 4, 2, "BE"), HYPOTHESIS, 65,
        "docs/master-test01-analysis.md section 5",
        InterpolatedGuess(
            points=((0, 0), (4487, 565), (5960, 900), (6730, 1380), (7108, 2570)),
            unit="RPM", basis=FITTED,
            note="Piecewise fit across 5 real anchor points: raw 0 -> 0 RPM "
            "(engine off), raw~4487 -> ~565 RPM (field sheet idle window, "
            "section 5), raw~5960 -> 900 RPM, raw~6730 -> 1380 RPM, and "
            "raw~7108 -> 2570 RPM (Gary's live observations during the first "
            "RPM-step test, 2026-08-19 -- 2570 was the settled mean of a "
            "plateau he confirmed 'fluctuated up and down before settling', so "
            "that last anchor is noisier than the others). The slope keeps "
            "accelerating across segments (0.13 -> 0.23 -> 0.62 -> 3.15 "
            "RPM/count) -- a single straight line fit none of them, which is "
            "why this uses interpolation instead of scale/offset. Values above "
            "raw~7108 are extrapolated using that last (steep, noisy) "
            "segment's slope and are the least trustworthy part of this "
            "guess.",
        ),
    ),
    ReplayCandidate(
        "Coolant Temperature candidate", CandidateKey("170", "03", 0, 2, "LE"), HYPOTHESIS, 55,
        "docs/master-test01-analysis.md section 6",
        Guess(
            scale=0.001085, offset=89.44, unit="°F", basis=FITTED,
            note="Two-point fit: raw 5126 -> 95°F at key-on, raw 57642 -> "
            "152°F at t=600s (section 6, field sheet). The report notes "
            "unexplained instability late in the session that this linear "
            "guess will not reproduce correctly -- confirmed to start earlier "
            "than 'late session' too: at the settled 2570 RPM plateau "
            "(t~925-953s, 2026-08-19), real coolant was still 152°F (same as "
            "the t=600s anchor) but raw had drifted to ~43818, ~24% off the "
            "~57642 seen at the *same* real 152°F reading -- real, uncaptured "
            "noise/drift in this candidate between the two fitted anchors, not "
            "something a better-shaped curve would fix.",
        ),
    ),
    ReplayCandidate(
        "Oil Pressure candidate", CandidateKey("170", "00", 1, 1, ""), RAW, 80,
        "docs/master-test01-analysis.md section 7 (Phase 2 tool score 80%; the "
        "report downgrades this to 'moderate', and live validation below pushes "
        "it further -- tier changed from hypothesis to raw on 2026-08-19 "
        "despite the tool's unchanged 80% score, which structurally can't see "
        "any of this)",
        Guess(
            scale=0.599, offset=0, unit="PSI", basis=FITTED,
            note="Fitted from a single point: raw~84 at t=120s vs. the field "
            "sheet's real 50.3 PSI at the same moment (section 7) -- kept only "
            "because no better fit exists, not because it's trusted. Two "
            "rounds of live validation (2026-08-19) have made this candidate's "
            "standing worse, not better: it declines ~55% during idle while "
            "real oil pressure stays flat (section 7); and at the settled 2570 "
            "RPM plateau, where real oil pressure peaks at 65.9 PSI (the "
            "highest reading on the whole field sheet), this candidate's raw "
            "value (~35.6) is essentially the same as -- if anything slightly "
            "below -- its own idle raw value (~37.8). It fails to rise at all "
            "across the full confirmed RPM range. This guess is likely "
            "showing a number with very little relationship to real oil "
            "pressure; treat it as illustrative at best.",
        ),
    ),
    ReplayCandidate(
        "Raw Water Pressure candidate", CandidateKey("1A0", "05", 1, 2, "LE"), HYPOTHESIS, 60,
        "docs/master-test01-analysis.md section 8 -- originally downgraded to "
        "'weak' there, UPGRADED back to hypothesis tier on 2026-08-19 after "
        "cross-test validation (see the Guess note below) substantially "
        "addressed that downgrade's reasoning",
        InterpolatedGuess(
            points=((256, 0.0), (34160, 0.75), (38905, 1.7), (42335, 2.8), (45385, 4.1)),
            unit="PSI", basis=FITTED,
            note="Piecewise fit across 5 real anchor points from the FIRST RPM "
            "step test, all confirmed 2026-08-19: raw 256 -> 0 PSI (key-on "
            "floor), raw~34160 -> ~0.75 PSI (idle), raw~38905 -> 1.7 PSI (900 "
            "RPM), raw~42335 -> 2.8 PSI (1380 RPM), raw~45385 -> 4.1 PSI "
            "(settled 2570 RPM). Slope accelerates with RPM (0.000022 -> "
            "0.00020 -> 0.00032 -> 0.00043 PSI/count) -- consistent with a "
            "centrifugal impeller pump, where pressure scales with speed "
            "squared. CROSS-VALIDATED against a SECOND, independent RPM step "
            "test later in the same capture (2026-08-19): applying this exact "
            "curve (fit only from the first test) to the second test's "
            "actual RPM values predicts this candidate's readings to within "
            "~1-11% at four more points (RPM 999/1352/1570/2492 -> predicted "
            "1.93/2.74/3.01/4.02 PSI vs. actual guess 1.72/2.51/3.01/3.94 PSI) "
            "-- one point matched almost exactly. A real physical curve fit "
            "from one trial predicting a second, independent trial this well "
            "is meaningfully stronger evidence than either test alone. (Gary "
            "also asked whether this candidate might instead be fuel "
            "consumption rate, GPH -- checked directly: real GPH during the "
            "second test was 0.7/1.1/1.5/1.7/1.9/0.8, both the wrong absolute "
            "scale and the wrong shape compared to this candidate's actual "
            "readings, while the RPM-pressure curve matched well. Ruled out.) "
            "Section 8's other concerns (coarse 58-value quantization, "
            "onset-timing ambiguity with RPM specifically at engine-start) "
            "still stand and are unaffected by this.",
        ),
    ),
    ReplayCandidate(
        "Fuel Level candidate", CandidateKey("170", "00", 2, 1, ""), RAW, 40,
        "docs/master-test01-analysis.md section 9 (indistinguishable from Depth "
        "with this dataset)",
        Guess(
            scale=0.0, offset=100.0, unit="%", basis=FITTED,
            note="Flat 100% -- this candidate's raw value barely moves at all "
            "(4-5 the entire session, section 9), and Gary confirmed live "
            "(2026-08-19, 25% into a replay) real fuel was ~100% at that point "
            "too, matching the field sheet's 100% throughout. There isn't "
            "enough raw dynamic range to fit a scale, only an offset -- this "
            "guess can't tell a real constant-100% signal apart from any other "
            "near-constant byte, it just no longer contradicts the known value.",
        ),
    ),
    ReplayCandidate(
        "Depth candidate", CandidateKey("170", "01", 1, 2, "LE"), RAW, 40,
        "docs/master-test01-analysis.md section 10 (indistinguishable from Fuel "
        "with this dataset)",
        Guess(
            scale=0.0016, offset=-38.204, unit="ft", basis=FITTED,
            note="Two-point fit: raw 29440 -> 8.9ft at key-on (field sheet), "
            "raw 29565 -> 9.1ft at 25% into a replay Gary watched live "
            "(2026-08-19, t~328s). Small raw range behind this fit (125 counts) "
            "-- treat the slope as a rough estimate, not a calibrated scale.",
        ),
    ),
    ReplayCandidate(
        "Battery Voltage candidate", CandidateKey("00000B41", "83", 0, 2, "LE"), RAW, 55,
        "docs/master-test01-analysis.md section 11 -- shows the steady-state "
        "record-83 field; the specific record-81 candidate scored in the report "
        "has too few samples in this capture to display continuously",
        Guess(
            scale=4 / 65535, offset=9.815, unit="V", basis=FITTED,
            note="Anchored on raw 65284 -> 13.8V, confirmed live by Gary "
            "(2026-08-19, 25% into a replay, t~328s) -- coincidentally the same "
            "raw value seen at end-of-capture too. This field only ever takes 2 "
            "distinct raw values in the whole capture (section 3/11); the OTHER "
            "state (5895) maps to ~10.2V under this same fit, which a real "
            "battery voltage should not do while running -- still evidence this "
            "candidate probably isn't a clean, continuous voltage signal, even "
            "though one of its two states now reads correctly. CONFIRMED LIVE "
            "(2026-08-20): Gary watched this gauge square-wave cleanly between "
            "10.2V and 13.8V on a strict ~15-18s cadence throughout, with shore "
            "power connected the entire test (field sheet) -- a shore-powered "
            "battery should read stable, not toggle like this. Strengthens the "
            "case that this raw field is not battery voltage, most likely two "
            "different pieces of status/diagnostic data alternating in the same "
            "byte slot (matches the record-83 alternation already documented in "
            "section 3 of the analysis).",
        ),
    ),
    ReplayCandidate(
        "Trim candidate", CandidateKey("1A0", "0B", 3, 1, ""), RAW, -1,
        "docs/master-test01-analysis.md section 12 ('very weak / exploratory'; "
        "not scored by the formal Phase 2 engine)",
        Guess(
            scale=-100 / 255, offset=94.12, unit="%", basis=FITTED,
            note="Inverted 'byte range = 0-100%' guess, recentered so the "
            "observed ~239-240 raw 'down' baseline reads ~0% -- confirmed by "
            "both the field sheet (trim starts fully DOWN at key-on, raw~239) "
            "and Gary's live observation (2026-08-19, 25% into a replay, "
            "raw~240, expected ~0%). Direction (which end is 'down') is still "
            "a guess; magnitude during the actual trim-cycle window is not "
            "confirmed.",
        ),
    ),
    ReplayCandidate(
        "Engine/mode status flag", CandidateKey("1A0", "00", 1, 1, ""), RAW, -1,
        "docs/master-test01-analysis.md section 3 -- a structural status flag, "
        "not a physical-value candidate; included as a diagnostic curiosity",
        None,  # not a physical quantity -- no unit guess makes sense
    ),
]

# The active candidate set. When replaying a capture other than
# master-test01, point this at that capture's own candidate list instead
# (see the module docstring) rather than editing the entries above.
CANDIDATES: list[ReplayCandidate] = MASTER_TEST01_CANDIDATES
