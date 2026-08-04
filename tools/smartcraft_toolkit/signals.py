"""Generic, protocol-agnostic measurement layer for hypothesis generation.

Everything in this module is reusable across any hypothesis: it groups raw
frames into candidate byte/word locations and computes value traces and
statistical features. Nothing here knows what RPM, coolant, or trim are --
that domain-specific scoring lives in hypotheses.py, built entirely out of
the features computed here.

Grouping note: a CAN ID's frames are grouped by their first payload byte
("record") purely as a way to compare like with like -- e.g. record "00" of
ID 170 across five captures. This is a superset of the strict Phase 1
record/0xFF-terminator fragmentation convention (reconstruct.py): it also
covers IDs like 1FFD4041, which cycles through byte values 02-05 with no
confirmed terminator ever observed. We don't know yet whether 1FFD4041
truly fragments the same way 170 does -- grouping by first byte lets us
generate candidates for it anyway without asserting that it does.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .experiments import Experiment
from .parser import Frame


@dataclass(frozen=True)
class CandidateKey:
    can_id: str
    record: str  # first payload byte, as hex, e.g. "00", "FF", "02"
    offset: int  # byte offset within the payload *after* the record byte
    width: int  # 1 or 2
    endian: str  # "" for width 1, else "LE" or "BE"

    @property
    def label(self) -> str:
        if self.width == 1:
            return f"byte {self.offset}"
        return f"bytes {self.offset}-{self.offset + 1} ({self.endian})"

    @property
    def max_value(self) -> int:
        return 255 if self.width == 1 else 65535


@dataclass
class Trace:
    values: List[int] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.values)

    @property
    def mean(self) -> Optional[float]:
        return sum(self.values) / len(self.values) if self.values else None

    @property
    def stdev(self) -> Optional[float]:
        if len(self.values) < 2:
            return 0.0 if self.values else None
        m = self.mean
        return math.sqrt(sum((v - m) ** 2 for v in self.values) / len(self.values))

    @property
    def min(self) -> Optional[int]:
        return min(self.values) if self.values else None

    @property
    def max(self) -> Optional[int]:
        return max(self.values) if self.values else None


FrameGroups = Dict[Tuple[str, str], List[Frame]]


def determine_sequenced_ids(all_frames: List[Frame]) -> Dict[str, bool]:
    """Per CAN ID, across every experiment pooled together: does the first
    payload byte take more than one value anywhere? If not, there's no
    evidence it's a record/sequence selector at all (e.g. 00000B41 is
    always 0x83) -- treating it as one anyway would silently drop that byte
    from candidate generation. IDs with no such evidence get their full
    payload (including byte 0) treated as plain data instead."""
    seen: Dict[str, set] = defaultdict(set)
    for frame in all_frames:
        if frame.data:
            seen[frame.can_id].add(frame.data[0])
    return {can_id: len(values) > 1 for can_id, values in seen.items()}


def group_frames(frames: List[Frame], sequenced_ids: Dict[str, bool]) -> FrameGroups:
    """Group frames by (can_id, record), where record is the first payload
    byte for IDs with evidence of sequencing, or "" (whole payload treated
    as data, nothing stripped) otherwise. `sequenced_ids` must come from
    determine_sequenced_ids() over the pooled frames from every experiment,
    so a given CAN ID is grouped the same way in every experiment."""
    groups: FrameGroups = defaultdict(list)
    for frame in frames:
        if not frame.data:
            continue
        if sequenced_ids.get(frame.can_id, False):
            record = f"{frame.data[0]:02X}"
        else:
            record = ""
        groups[(frame.can_id, record)].append(frame)
    return groups


def candidate_keys_for_group(can_id: str, record: str, payload_length: int) -> List[CandidateKey]:
    """All single-byte and adjacent-byte-pair (both endians) candidates for one group."""
    keys = [CandidateKey(can_id, record, offset, 1, "") for offset in range(payload_length)]
    for offset in range(payload_length - 1):
        keys.append(CandidateKey(can_id, record, offset, 2, "LE"))
        keys.append(CandidateKey(can_id, record, offset, 2, "BE"))
    return keys


def read_value(payload: bytes, key: CandidateKey) -> int:
    if key.width == 1:
        return payload[key.offset]
    low, high = payload[key.offset], payload[key.offset + 1]
    return (high << 8 | low) if key.endian == "LE" else (low << 8 | high)


def all_candidate_keys(groups_by_experiment: Dict[str, FrameGroups]) -> List[CandidateKey]:
    """Every candidate key observable across all experiments, using each
    group's minimum observed payload length so no candidate ever indexes
    past a real frame's payload."""
    min_payload_len: Dict[Tuple[str, str], int] = {}
    for groups in groups_by_experiment.values():
        for group_key, frames in groups.items():
            _can_id, record = group_key
            strip = 0 if record == "" else 1
            shortest = min(len(f.data) - strip for f in frames)
            if group_key not in min_payload_len or shortest < min_payload_len[group_key]:
                min_payload_len[group_key] = shortest

    keys: List[CandidateKey] = []
    for (can_id, record), payload_length in sorted(min_payload_len.items()):
        keys.extend(candidate_keys_for_group(can_id, record, payload_length))
    return keys


def build_traces(key: CandidateKey, groups_by_experiment: Dict[str, FrameGroups]) -> Dict[str, Trace]:
    traces: Dict[str, Trace] = {}
    needed = key.offset + (2 if key.width == 2 else 1)
    for exp_name, groups in groups_by_experiment.items():
        trace = Trace()
        for frame in groups.get((key.can_id, key.record), []):
            payload = frame.data if key.record == "" else frame.data[1:]
            if len(payload) < needed:
                continue
            trace.values.append(read_value(payload, key))
            trace.timestamps.append(frame.timestamp)
        traces[exp_name] = trace
    return traces


# --------------------------------------------------------------------------
# Generic statistical features. None of these know what a candidate might
# "mean" -- they only describe the shape of its value traces.
# --------------------------------------------------------------------------


def global_range(traces: Dict[str, Trace]) -> int:
    values = [v for trace in traces.values() for v in trace.values]
    return (max(values) - min(values)) if values else 0


def _rank(values: List[float]) -> List[float]:
    """Average ranks, ties broken by averaging (standard Spearman tie handling)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def rank_correlation(xs: List[float], ys: List[float]) -> Optional[float]:
    """Spearman rank correlation, pure stdlib. None if undefined (fewer
    than 2 points, or no variance in either series)."""
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    rx, ry = _rank(xs), _rank(ys)
    mean_rx, mean_ry = sum(rx) / len(rx), sum(ry) / len(ry)
    numerator = sum((a - mean_rx) * (b - mean_ry) for a, b in zip(rx, ry))
    denom_x = math.sqrt(sum((a - mean_rx) ** 2 for a in rx))
    denom_y = math.sqrt(sum((b - mean_ry) ** 2 for b in ry))
    if denom_x == 0 or denom_y == 0:
        return None
    return numerator / (denom_x * denom_y)


def rpm_correlation(traces: Dict[str, Trace], experiments: List[Experiment]) -> Optional[float]:
    """Rank-correlate mean value against rpm_rank, one point per distinct
    rank (ties -- e.g. idle/idle2 -- are averaged into a single point first,
    so a repeated idle capture doesn't get double weight)."""
    by_rank: Dict[int, List[float]] = defaultdict(list)
    for exp in experiments:
        if exp.rpm_rank is None:
            continue
        trace = traces.get(exp.name)
        if trace is None or trace.mean is None:
            continue
        by_rank[exp.rpm_rank].append(trace.mean)
    if len(by_rank) < 3:
        return None
    ranks = sorted(by_rank)
    means = [sum(by_rank[r]) / len(by_rank[r]) for r in ranks]
    return rank_correlation([float(r) for r in ranks], means)


def session_drift(traces: Dict[str, Trace], experiments: List[Experiment]) -> Optional[float]:
    """Rank-correlate mean value against session_order, one point per
    experiment (unlike rpm_correlation, idle/idle2 are NOT merged -- this
    is specifically about drift across the session's real chronology)."""
    orders, means = [], []
    for exp in experiments:
        trace = traces.get(exp.name)
        if trace is None or trace.mean is None:
            continue
        orders.append(float(exp.session_order))
        means.append(trace.mean)
    return rank_correlation(orders, means)


def within_condition_stability(traces: Dict[str, Trace], experiment_names: List[str]) -> float:
    """1.0 = perfectly steady within every named experiment; 0.0 = as noisy
    as the whole observed range within at least one of them."""
    span = global_range(traces) or 1
    normalized = []
    for name in experiment_names:
        trace = traces.get(name)
        if trace is None or trace.stdev is None:
            continue
        normalized.append(min(trace.stdev / span, 1.0))
    if not normalized:
        return 0.0
    return 1.0 - (sum(normalized) / len(normalized))


def idle_vs_rpm_separation(traces: Dict[str, Trace], experiments: List[Experiment]) -> Optional[float]:
    """Signed, normalized gap between mean value at commanded-RPM
    conditions and mean value at idle. Positive => higher at RPM."""
    idle_means = [traces[e.name].mean for e in experiments if "idle" in e.tags and traces.get(e.name) and traces[e.name].mean is not None]
    rpm_means = [traces[e.name].mean for e in experiments if "rpm" in e.tags and traces.get(e.name) and traces[e.name].mean is not None]
    if not idle_means or not rpm_means:
        return None
    span = global_range(traces) or 1
    return ((sum(rpm_means) / len(rpm_means)) - (sum(idle_means) / len(idle_means))) / span


def idle_replicate_drift(traces: Dict[str, Trace], experiments: List[Experiment]) -> Optional[float]:
    """Signed, normalized change between the first and last idle capture of
    the session (idle -> idle2). Positive => rose over the session."""
    idle_replicates = [e for e in experiments if "idle" in e.tags]
    if len(idle_replicates) < 2:
        return None
    first_exp = min(idle_replicates, key=lambda e: e.session_order)
    last_exp = max(idle_replicates, key=lambda e: e.session_order)
    first_trace, last_trace = traces.get(first_exp.name), traces.get(last_exp.name)
    if not first_trace or not last_trace or first_trace.mean is None or last_trace.mean is None:
        return None
    span = global_range(traces) or 1
    return (last_trace.mean - first_trace.mean) / span


def near_constant_score(traces: Dict[str, Trace], key: CandidateKey) -> float:
    """0.0 = uses its full possible range; 1.0 = never moves at all."""
    span = global_range(traces)
    return 1.0 - min(span / key.max_value, 1.0)


def distinct_value_count(traces: Dict[str, Trace]) -> int:
    values = {v for trace in traces.values() for v in trace.values}
    return len(values)


def always_at_minimum(traces: Dict[str, Trace], experiment_names: List[str]) -> bool:
    """True if every named experiment's trace never leaves the global minimum."""
    values = [v for trace in traces.values() for v in trace.values]
    if not values:
        return False
    floor = min(values)
    for name in experiment_names:
        trace = traces.get(name)
        if trace is None or not trace.values:
            continue
        if any(v != floor for v in trace.values):
            return False
    return True


def monotonic_nondecreasing_fraction(traces: Dict[str, Trace], experiments: List[Experiment]) -> Optional[float]:
    """Fraction of consecutive steps that are non-decreasing, walked in
    session order. This includes the boundary between one experiment's last
    sample and the next experiment's first sample -- a true counter (engine
    hours, a sequence number) keeps climbing across a log boundary; a value
    that drops back to baseline between experiments (RPM, oil pressure)
    should show up as a real decrease right at that boundary, not be hidden
    by only ever looking within one log at a time."""
    ordered = sorted(experiments, key=lambda e: e.session_order)
    steps_total = 0
    steps_nondecreasing = 0
    previous_last_value = None
    for exp in ordered:
        trace = traces.get(exp.name)
        if trace is None or not trace.values:
            continue
        if previous_last_value is not None:
            steps_total += 1
            if trace.values[0] >= previous_last_value:
                steps_nondecreasing += 1
        for a, b in zip(trace.values, trace.values[1:]):
            steps_total += 1
            if b >= a:
                steps_nondecreasing += 1
        previous_last_value = trace.values[-1]
    if steps_total == 0:
        return None
    return steps_nondecreasing / steps_total
