"""Named-signal hypothesis scoring, built entirely from the generic features
in signals.py.

This module is the only place that mentions RPM, coolant, oil pressure,
etc. Every rubric below is a short, fixed, documented point rule applied
uniformly to every candidate -- nothing here looks at a specific CAN ID or
byte offset and decides it "must" be a given signal. Confidence is capped
at 100 and floored at 0; it is a summary of the evidence below it, not an
independent claim.

Every HypothesisResult must carry both supporting AND contradicting
evidence (even when one list is empty, that absence is itself meaningful
and is left for the caller to notice), plus a suggested experiment that
would move the confidence in either direction. That is the contract Phase 2
asked for: theories, not conclusions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .experiments import Experiment
from .signals import (
    CandidateKey,
    Trace,
    always_at_minimum,
    distinct_value_count,
    global_range,
    idle_replicate_drift,
    idle_vs_rpm_separation,
    monotonic_nondecreasing_fraction,
    near_constant_score,
    rpm_correlation,
    session_drift,
    within_condition_stability,
)


def clamp(value: float, lo: int = 0, hi: int = 100) -> int:
    return int(max(lo, min(hi, round(value))))


@dataclass
class CandidateFeatures:
    key: CandidateKey
    traces: dict
    rpm_corr: Optional[float]
    session_drift: Optional[float]
    stability: float
    idle_rpm_sep: Optional[float]
    idle_drift: Optional[float]
    near_constant: float
    distinct_count: int
    monotonic_frac: Optional[float]
    pegged_at_rpm_floor: bool  # never leaves the global minimum during any RPM-tagged experiment


def compute_features(key: CandidateKey, traces: dict, experiments: List[Experiment]) -> CandidateFeatures:
    all_names = [e.name for e in experiments]
    rpm_names = [e.name for e in experiments if "rpm" in e.tags]
    return CandidateFeatures(
        key=key,
        traces=traces,
        rpm_corr=rpm_correlation(traces, experiments),
        session_drift=session_drift(traces, experiments),
        stability=within_condition_stability(traces, all_names),
        idle_rpm_sep=idle_vs_rpm_separation(traces, experiments),
        idle_drift=idle_replicate_drift(traces, experiments),
        near_constant=near_constant_score(traces, key),
        distinct_count=distinct_value_count(traces),
        monotonic_frac=monotonic_nondecreasing_fraction(traces, experiments),
        pegged_at_rpm_floor=always_at_minimum(traces, rpm_names),
    )


@dataclass
class HypothesisResult:
    name: str
    key: CandidateKey
    confidence: int
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    suggested_experiment: str = ""


DATA_GAP_NOTE = (
    "current captures are five steady-state snapshots (idle, idle again, "
    "1000/1650/1900 RPM) taken ~30-40s apart within one ~8.4-minute session -- "
    "there is no key-ON/engine-OFF phase and no long warm-up window in this "
    "dataset yet."
)


def score_rpm(f: CandidateFeatures) -> HypothesisResult:
    points = 0.0
    evidence_for, evidence_against = [], []

    if f.rpm_corr is not None and f.rpm_corr >= 0.95:
        points += 40
        evidence_for.append("increases monotonically with RPM across idle -> 1000 -> 1650 -> 1900")
    elif f.rpm_corr is not None and f.rpm_corr >= 0.6:
        points += 20
        evidence_for.append(f"trends upward with RPM (rank correlation {f.rpm_corr:.2f}), but not cleanly monotonic")
    elif f.rpm_corr is not None and f.rpm_corr <= -0.6:
        evidence_against.append(f"trends *downward* with RPM (rank correlation {f.rpm_corr:.2f}) -- opposite of expected")
    elif f.rpm_corr is None:
        evidence_against.append("not enough distinct values to test correlation with RPM")

    if f.stability >= 0.8:
        points += 15
        evidence_for.append("stable within each individual steady-RPM capture")
    if f.idle_rpm_sep is not None and f.idle_rpm_sep >= 0.3:
        points += 15
        evidence_for.append("clear gap between idle and RPM-running values")
    if f.idle_drift is not None and abs(f.idle_drift) < 0.1:
        points += 10
        evidence_for.append("returns to the same value at idle2 as at idle (repeatable, not a one-way drift)")
    elif f.idle_drift is not None and abs(f.idle_drift) >= 0.3:
        evidence_against.append("idle2 differs substantially from idle despite being the same commanded RPM")

    if f.near_constant >= 0.85:
        points -= 30
        evidence_against.append("value barely changes at all across the dataset -- contradicts an RPM-proportional signal")
    if f.monotonic_frac is not None and f.monotonic_frac >= 0.95 and (f.idle_drift is None or f.idle_drift >= 0):
        points -= 20
        evidence_against.append("behaves like an ever-increasing counter rather than a value that returns to baseline at idle2")

    return HypothesisResult(
        "RPM", f.key, clamp(points), evidence_for, evidence_against,
        "Hold a single RPM (e.g. 2500) steady for 30+ seconds and confirm the "
        "value stays flat; then log a tachometer reading alongside a capture "
        "to establish the scaling factor.",
    )


def score_coolant_temperature(f: CandidateFeatures) -> HypothesisResult:
    points = 0.0
    evidence_for, evidence_against = [], []

    if f.session_drift is not None and f.session_drift >= 0.6:
        points += 25
        evidence_for.append("trends upward across the session (idle -> ... -> idle2), consistent with continued warm-up")
    if f.idle_drift is not None and f.idle_drift > 0.05:
        points += 20
        evidence_for.append("higher at idle2 (end of session) than at idle (start of session)")
    elif f.idle_drift is not None and f.idle_drift < -0.05:
        evidence_against.append("lower at idle2 than at idle -- a warming engine shouldn't cool down")

    if f.rpm_corr is None or abs(f.rpm_corr) < 0.3:
        points += 15
        evidence_for.append("not tightly coupled to RPM, consistent with a slow thermal-lag signal")
    elif abs(f.rpm_corr) >= 0.7:
        points -= 25
        evidence_against.append(f"tracks RPM closely (rank correlation {f.rpm_corr:.2f}) -- too fast-responding for coolant temperature")

    if f.stability >= 0.8:
        points += 10
        evidence_for.append("steady within each short capture, as expected for a slow-changing analog reading")

    if f.near_constant >= 0.9:
        points -= 15
        evidence_against.append(
            "shows essentially no movement in this data -- either already at thermostat plateau, or this isn't "
            "the right byte; indistinguishable from fuel/depth/reserved with current data"
        )

    evidence_against.append(f"warm-up curve untestable directly yet: {DATA_GAP_NOTE}")

    return HypothesisResult(
        "Coolant Temperature", f.key, clamp(points), evidence_for, evidence_against,
        "Capture continuously from a cold start (~72°F ambient) through at "
        "least 10-15 minutes of idle to observe the full warm-up curve and "
        "confirm it plateaus near thermostat temperature.",
    )


def score_oil_pressure(f: CandidateFeatures) -> HypothesisResult:
    points = 0.0
    evidence_for, evidence_against = [], []

    if f.rpm_corr is not None and f.rpm_corr >= 0.6:
        points += 35
        evidence_for.append(f"increases with RPM (rank correlation {f.rpm_corr:.2f})")
    elif f.rpm_corr is not None and f.rpm_corr <= -0.6:
        evidence_against.append("decreases with RPM -- opposite of expected")

    if f.idle_drift is not None and f.idle_drift < -0.05:
        points += 30
        evidence_for.append("lower at idle2 (after the RPM run) than at idle (start of session) -- consistent with pressure easing as the engine warms")
    elif f.idle_drift is not None and f.idle_drift > 0.05:
        points -= 15
        evidence_against.append("rose from idle to idle2, opposite of the expected warm-engine pressure drop")

    if f.stability >= 0.8:
        points += 15
        evidence_for.append("stable within each individual capture")

    if f.near_constant >= 0.85:
        points -= 20
        evidence_against.append("no measurable change across the dataset")

    return HypothesisResult(
        "Oil Pressure", f.key, clamp(points), evidence_for, evidence_against,
        "Log a mechanical oil pressure gauge reading at cold idle and again "
        "after ~10 minutes of idle to directly confirm the expected drop, "
        "then compare timestamps against this byte.",
    )


def score_raw_water_pressure(f: CandidateFeatures) -> HypothesisResult:
    points = 0.0
    evidence_for, evidence_against = [], []

    if f.rpm_corr is not None and f.rpm_corr >= 0.7:
        points += 35
        evidence_for.append(f"increases with RPM (rank correlation {f.rpm_corr:.2f})")
    elif f.rpm_corr is not None and f.rpm_corr <= -0.6:
        evidence_against.append("decreases with RPM -- opposite of expected")

    if f.idle_rpm_sep is not None and f.idle_rpm_sep > 0.3:
        points += 30
        evidence_for.append("lowest at idle among the four RPM conditions, consistent with an impeller-driven pressure")

    if f.stability >= 0.8:
        points += 15
        evidence_for.append("stable low value at idle rather than noisy")

    if f.pegged_at_rpm_floor:
        points -= 15
        evidence_against.append("never leaves the observed minimum even at 1900 RPM -- contradicts 'increases with RPM'")
    if f.near_constant >= 0.85:
        points -= 20
        evidence_against.append("no measurable change across the dataset")

    evidence_against.append(
        f"the '0 psi with key ON / engine OFF' half of this hypothesis is untestable yet: {DATA_GAP_NOTE}"
    )

    return HypothesisResult(
        "Raw Water Pressure", f.key, clamp(points), evidence_for, evidence_against,
        "Capture a log starting with the key ON and the engine OFF for at "
        "least 10 seconds before cranking, to directly test the expected "
        "0 psi floor before the impeller turns.",
    )


def score_battery_voltage(f: CandidateFeatures) -> HypothesisResult:
    points = 0.0
    evidence_for, evidence_against = [], []

    flat_across_rpm = f.rpm_corr is None or abs(f.rpm_corr) < 0.3
    narrow_range = f.near_constant >= 0.5  # a regulated ~12.5-14.2V rail should occupy only a small slice of the byte's range

    if flat_across_rpm and narrow_range:
        points += 35
        evidence_for.append(
            "stays essentially flat across idle/1000/1650/1900 RPM AND occupies only a narrow "
            "slice of this byte's range, consistent with a regulated voltage rail"
        )
        if f.near_constant >= 0.995:
            evidence_against.append("shows literally zero fluctuation -- can't rule out a dead/reserved byte rather than a real regulated signal")
        else:
            points += 10
            evidence_for.append("small real-world fluctuation without tracking RPM, consistent with normal voltage ripple")
    elif flat_across_rpm:
        evidence_against.append(
            "doesn't correlate with RPM, but uses most of this byte's dynamic range -- inconsistent with a "
            "narrow regulated band, more consistent with noise or an unrelated signal"
        )
    elif abs(f.rpm_corr) >= 0.6:
        points -= 30
        evidence_against.append(f"tracks RPM (rank correlation {f.rpm_corr:.2f}) -- a regulated battery/alternator voltage shouldn't do this")

    if f.session_drift is None or abs(f.session_drift) < 0.2:
        points += 10
        evidence_for.append("no session-long drift")
    elif abs(f.session_drift) >= 0.6:
        evidence_against.append("drifts steadily across the session -- inconsistent with a regulated rail")

    evidence_against.append(
        "the single most distinguishing test for this hypothesis -- the ~12.5V (engine off) -> "
        f"~13.8-14.2V (alternator charging) step -- is untestable yet: {DATA_GAP_NOTE}"
    )

    return HypothesisResult(
        "Battery Voltage", f.key, clamp(points), evidence_for, evidence_against,
        "Capture a log spanning key-ON (engine off) through cranking and into "
        "a stable idle, to directly capture the expected voltage step.",
    )


def score_fuel_or_depth(f: CandidateFeatures) -> HypothesisResult:
    points = 0.0
    evidence_for, evidence_against = [], []

    if f.near_constant >= 0.9 and f.distinct_count > 1:
        points += 40
        evidence_for.append("nearly constant with only small fluctuations, matching both the fuel (~48%, constant) and depth (~8-9ft, constant) ground truth")
    elif f.near_constant >= 0.98:
        evidence_against.append("perfectly frozen (zero fluctuation) -- fuel/depth sensors normally show at least minor sensor noise; more consistent with padding/reserved")

    if f.rpm_corr is not None and abs(f.rpm_corr) >= 0.5:
        points -= 30
        evidence_against.append("correlates with RPM -- neither fuel level nor depth should depend on engine speed")

    evidence_against.append(
        "fuel and depth are indistinguishable from each other (and from a generic reserved/constant byte) "
        "with only RPM/idle experiments -- neither ground truth value depends on RPM, so this dataset "
        "structurally cannot tell them apart yet"
    )

    return HypothesisResult(
        "Fuel Level / Depth (indistinguishable)", f.key, clamp(points), evidence_for, evidence_against,
        "Fuel: compare two captures at meaningfully different fuel levels (e.g. "
        "before/after a long run). Depth: compare two captures at different "
        "water depths (e.g. different dock/anchorage). A real signal shifts; "
        "reserved/padding bytes won't.",
    )


HYPOTHESIS_SCORERS = [
    score_rpm,
    score_coolant_temperature,
    score_oil_pressure,
    score_raw_water_pressure,
    score_battery_voltage,
    score_fuel_or_depth,
]
