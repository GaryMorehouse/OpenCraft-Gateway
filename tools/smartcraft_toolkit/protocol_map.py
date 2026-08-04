"""Buckets every observed single byte into the Current Protocol Map.

Every rule here is generic (constant-value, counter-shaped, low-cardinality,
or "some named hypothesis scored above a threshold") and applied uniformly.
No byte is placed by hand.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .experiments import Experiment
from .hypotheses import HYPOTHESIS_SCORERS, compute_features
from .signals import CandidateKey, Trace, distinct_value_count, monotonic_nondecreasing_fraction

MAP_CONFIDENCE_THRESHOLD = 20


@dataclass
class MapEntry:
    key: CandidateKey
    category: str
    detail: str


def categorize_byte(key: CandidateKey, traces: Dict[str, Trace], experiments: List[Experiment]) -> MapEntry:
    assert key.width == 1, "the protocol map is built at single-byte granularity"

    distinct = distinct_value_count(traces)
    if distinct <= 1:
        values = {v for trace in traces.values() for v in trace.values}
        value = next(iter(values)) if values else None
        if value is None:
            return MapEntry(key, "Unknown", "no data observed for this byte in any experiment")
        detail = f"constant at 0x{value:02X} across every experiment"
        if value in (0x00, 0xFF):
            detail += " (0x00/0xFF is a conventional padding/sentinel value)"
        return MapEntry(key, "Likely padding/reserved", detail)

    monotonic = monotonic_nondecreasing_fraction(traces, experiments)
    if monotonic is not None and monotonic >= 0.9:
        return MapEntry(key, "Likely counters", f"{monotonic:.0%} of consecutive samples are non-decreasing")

    if distinct <= 4:
        return MapEntry(key, "Likely status bits", f"only {distinct} distinct values observed")

    features = compute_features(key, traces, experiments)
    best_name, best_confidence = None, 0
    for scorer in HYPOTHESIS_SCORERS:
        result = scorer(features)
        if result.confidence > best_confidence:
            best_name, best_confidence = result.name, result.confidence

    if best_confidence >= MAP_CONFIDENCE_THRESHOLD:
        return MapEntry(key, f"Likely {best_name}", f"confidence {best_confidence}%")

    if features.near_constant >= 0.85:
        return MapEntry(
            key, "Likely fuel/depth (near-constant analog)",
            "mostly flat but not frozen; no named hypothesis scored above the map threshold",
        )

    return MapEntry(key, "Unknown", f"{distinct} distinct values, no hypothesis scored >= {MAP_CONFIDENCE_THRESHOLD}%")
