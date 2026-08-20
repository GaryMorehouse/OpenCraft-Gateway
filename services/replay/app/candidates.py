"""The exact set of candidate CAN fields this replay tool surfaces,
transcribed directly from the evidence-scored hypotheses already published
in docs/master-test01-analysis.md and docs/HypothesisReport.md.

This module adds NO new CAN decoding. Every entry below names a byte/word
location that tools/smartcraft_toolkit's Phase 2 hypothesis engine already
scored against real capture evidence; nothing is invented for replay.

`tier` reflects that published assessment, per the replay task's own
instructions:

    "hypothesis" -- docs/master-test01-analysis.md calls this candidate at
                    least "moderate" confidence. Shown labeled with its
                    hypothesis name and confidence score, but still
                    explicitly as an unconfirmed candidate -- no unit
                    conversion is applied to any candidate here, hypothesis
                    or raw, because the published confidence only
                    identifies *which byte*, never a scale factor.
    "raw"       -- that report calls the candidate "weak" or leaves it
                   unscored. Shown as a plain raw CAN field, not tied to a
                   named physical signal ("if a candidate is not
                   sufficiently supported, show the raw CAN field rather
                   than inventing a value").

Re-run `python tools/smartcraft_decoder.py hypotheses` and update
docs/master-test01-analysis.md before changing any tier or confidence
value here -- this table should always follow the evidence, never the
other way around. To replay a different capture with its own candidate
bytes, add a new list here (or a new module) rather than editing these
master-test01-specific entries in place.
"""
from __future__ import annotations

from dataclasses import dataclass

from smartcraft_toolkit.signals import CandidateKey

HYPOTHESIS = "hypothesis"
RAW = "raw"


@dataclass(frozen=True)
class ReplayCandidate:
    label: str  # panel-facing name; also the InfluxDB "hypothesis" tag value
    key: CandidateKey
    tier: str  # HYPOTHESIS or RAW
    confidence_pct: int  # -1 if unscored by the formal Phase 2 engine
    source: str  # where this assessment is documented, for traceability


MASTER_TEST01_CANDIDATES: list[ReplayCandidate] = [
    ReplayCandidate(
        "RPM candidate", CandidateKey("170", "01", 4, 2, "BE"), HYPOTHESIS, 65,
        "docs/master-test01-analysis.md section 5",
    ),
    ReplayCandidate(
        "Coolant Temperature candidate", CandidateKey("170", "03", 0, 2, "LE"), HYPOTHESIS, 55,
        "docs/master-test01-analysis.md section 6",
    ),
    ReplayCandidate(
        "Oil Pressure candidate", CandidateKey("170", "00", 1, 1, ""), HYPOTHESIS, 80,
        "docs/master-test01-analysis.md section 7 (Phase 2 tool score 80%; the "
        "report itself downgrades this to 'moderate' -- see the section for why)",
    ),
    ReplayCandidate(
        "Raw Water Pressure candidate", CandidateKey("1A0", "05", 1, 2, "LE"), RAW, 60,
        "docs/master-test01-analysis.md section 8 (downgraded to 'weak' there; "
        "shown here as a raw field despite a formal-engine score, per that "
        "downgrade)",
    ),
    ReplayCandidate(
        "Fuel Level candidate", CandidateKey("170", "00", 2, 1, ""), RAW, 40,
        "docs/master-test01-analysis.md section 9 (indistinguishable from Depth "
        "with this dataset)",
    ),
    ReplayCandidate(
        "Depth candidate", CandidateKey("170", "01", 1, 2, "LE"), RAW, 40,
        "docs/master-test01-analysis.md section 10 (indistinguishable from Fuel "
        "with this dataset)",
    ),
    ReplayCandidate(
        "Battery Voltage candidate", CandidateKey("00000B41", "83", 0, 2, "LE"), RAW, 55,
        "docs/master-test01-analysis.md section 11 -- shows the steady-state "
        "record-83 field; the specific record-81 candidate scored in the report "
        "has too few samples in this capture to display continuously",
    ),
    ReplayCandidate(
        "Trim candidate", CandidateKey("1A0", "0B", 3, 1, ""), RAW, -1,
        "docs/master-test01-analysis.md section 12 ('very weak / exploratory'; "
        "not scored by the formal Phase 2 engine)",
    ),
    ReplayCandidate(
        "Engine/mode status flag", CandidateKey("1A0", "00", 1, 1, ""), RAW, -1,
        "docs/master-test01-analysis.md section 3 -- a structural status flag, "
        "not a physical-value candidate; included as a diagnostic curiosity",
    ),
]

# The active candidate set. When replaying a capture other than
# master-test01, point this at that capture's own candidate list instead
# (see the module docstring) rather than editing the entries above.
CANDIDATES: list[ReplayCandidate] = MASTER_TEST01_CANDIDATES
