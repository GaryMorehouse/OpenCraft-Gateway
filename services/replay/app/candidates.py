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
from typing import Optional

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
    scale: float
    offset: float
    unit: str
    basis: str  # FITTED or UNANCHORED
    note: str  # human-readable explanation, shown in the panel description

    def apply(self, raw_value: int) -> float:
        return raw_value * self.scale + self.offset


@dataclass(frozen=True)
class ReplayCandidate:
    label: str  # panel-facing name; also the InfluxDB "hypothesis" tag value
    key: CandidateKey
    tier: str  # HYPOTHESIS or RAW
    confidence_pct: int  # -1 if unscored by the formal Phase 2 engine
    source: str  # where this assessment is documented, for traceability
    guess: Optional[Guess] = None  # None = no defensible guess; show raw only


MASTER_TEST01_CANDIDATES: list[ReplayCandidate] = [
    ReplayCandidate(
        "RPM candidate", CandidateKey("170", "01", 4, 2, "BE"), HYPOTHESIS, 65,
        "docs/master-test01-analysis.md section 5",
        Guess(
            scale=0.125, offset=0, unit="RPM", basis=FITTED,
            note="Fitted from raw~4270-4590 during the field sheet's real idle "
            "540-590 RPM window (section 5). Known to be a poor fit at higher "
            "RPM -- this candidate's own dynamic range is far too small "
            "relative to real RPM's, per the same section.",
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
            "guess will not reproduce correctly.",
        ),
    ),
    ReplayCandidate(
        "Oil Pressure candidate", CandidateKey("170", "00", 1, 1, ""), HYPOTHESIS, 80,
        "docs/master-test01-analysis.md section 7 (Phase 2 tool score 80%; the "
        "report itself downgrades this to 'moderate' -- see the section for why)",
        Guess(
            scale=0.599, offset=0, unit="PSI", basis=FITTED,
            note="Fitted from raw~84 at t=120s vs. the field sheet's real 50.3 "
            "PSI at the same moment (section 7). The report also documents this "
            "candidate declining ~55% during a window where real oil pressure "
            "stayed flat -- treat any steady decline this guess shows with that "
            "in mind.",
        ),
    ),
    ReplayCandidate(
        "Raw Water Pressure candidate", CandidateKey("1A0", "05", 1, 2, "LE"), RAW, 60,
        "docs/master-test01-analysis.md section 8 (downgraded to 'weak' there; "
        "shown here as a raw field despite a formal-engine score, per that "
        "downgrade)",
        Guess(
            scale=0.0000296, offset=-0.0076, unit="PSI", basis=FITTED,
            note="Fitted from raw 256 -> 0 PSI (key-on floor) and raw ~34000 -> "
            "1 PSI (idle) per the field sheet (section 8). Section 8 also found "
            "this candidate's step-test response far smaller than real water "
            "pressure's -- this guess will under-read once RPM rises.",
        ),
    ),
    ReplayCandidate(
        "Fuel Level candidate", CandidateKey("170", "00", 2, 1, ""), RAW, 40,
        "docs/master-test01-analysis.md section 9 (indistinguishable from Depth "
        "with this dataset)",
        Guess(
            scale=100 / 255, offset=0, unit="%", basis=UNANCHORED,
            note="Naive 'byte range = 0-100%' assumption, NOT fitted to any real "
            "reading. The field sheet's real fuel level was ~100% throughout "
            "(section 9) -- if this guess reads far below that, it's evidence "
            "against this candidate/assumption, not a sign the tank was low.",
        ),
    ),
    ReplayCandidate(
        "Depth candidate", CandidateKey("170", "01", 1, 2, "LE"), RAW, 40,
        "docs/master-test01-analysis.md section 10 (indistinguishable from Fuel "
        "with this dataset)",
        Guess(
            scale=100 / 65535, offset=0, unit="ft", basis=UNANCHORED,
            note="Naive 'word range = 0-100ft' assumption, NOT fitted to any "
            "real reading. The field sheet's real depth was ~8.9-9.1ft "
            "(section 10) -- a large mismatch here is evidence against this "
            "candidate/assumption, not a real depth change.",
        ),
    ),
    ReplayCandidate(
        "Battery Voltage candidate", CandidateKey("00000B41", "83", 0, 2, "LE"), RAW, 55,
        "docs/master-test01-analysis.md section 11 -- shows the steady-state "
        "record-83 field; the specific record-81 candidate scored in the report "
        "has too few samples in this capture to display continuously",
        Guess(
            scale=4 / 65535, offset=12, unit="V", basis=UNANCHORED,
            note="Naive 'word range = 12-16V' assumption, NOT fitted to any real "
            "reading. This field only ever takes 2 distinct raw values in the "
            "whole capture (section 3/11) -- a real battery voltage should vary "
            "continuously, so treat this gauge flipping between two fixed "
            "numbers as evidence this candidate probably ISN'T battery voltage.",
        ),
    ),
    ReplayCandidate(
        "Trim candidate", CandidateKey("1A0", "0B", 3, 1, ""), RAW, -1,
        "docs/master-test01-analysis.md section 12 ('very weak / exploratory'; "
        "not scored by the formal Phase 2 engine)",
        Guess(
            scale=-100 / 255, offset=100, unit="%", basis=FITTED,
            note="Inverted 'byte range = 0-100%' guess, anchored on the field "
            "sheet's trim starting fully DOWN (0%) at key-on, matching this "
            "candidate's near-constant raw ~239-244 at the start of the capture "
            "(section 12). Direction (which end is 'down') is a guess; magnitude "
            "during the actual trim-cycle window is not confirmed.",
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
