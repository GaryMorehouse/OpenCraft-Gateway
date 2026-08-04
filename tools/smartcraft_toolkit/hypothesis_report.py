"""Orchestrates Phase 2 hypothesis generation end to end: load the
registered experiments, generate every byte/word candidate, score every
named hypothesis against every candidate, categorize every single byte, and
render the Markdown report.

Re-running this after adding a new Experiment to experiments.py is the
whole mechanism by which confidence values are meant to move automatically
as more captures are collected -- nothing here is specific to today's five
logs.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from .experiments import EXPERIMENTS, Experiment
from .hypotheses import HYPOTHESIS_SCORERS, HypothesisResult, compute_features
from .parser import Frame, parse_file
from .protocol_map import MapEntry, categorize_byte
from .signals import (
    CandidateKey,
    FrameGroups,
    all_candidate_keys,
    build_traces,
    determine_sequenced_ids,
    group_frames,
)

TOP_N_PER_HYPOTHESIS = 3
TRIM_NOTE = (
    "Trim cannot be scored yet: the only capture meant to exercise trim "
    "(trim-cycles.log) turned out to contain no real signal -- see Data "
    "Quality below. No candidates are reported for this hypothesis; that is "
    "an honest 'not yet testable', not a 0% confidence finding."
)
DATA_QUALITY_NOTE = (
    "Two capture sessions exist on disk. The session analyzed here -- "
    "idle, 1000rpm, 1650rpm, 1900rpm, idle2, in that order, ~8.4 minutes "
    "total -- is clean: every consecutive frame is genuinely distinct. "
    "A separate, ~18-hours-earlier session (key-cycle.log, rpm-steps.log, "
    "trim-cycles.log, smartcrafttest.log) was also captured, but every one "
    "of those four files turned out to contain a single CAN frame "
    "(record 00 of ID 170) retransmitted 100,000+ times with no other "
    "content -- consistent with a Listen-Only capture against a bus with "
    "no other node available to ACK it, not real telemetry. They are "
    "excluded from this analysis. Re-capturing a real trim cycle, key "
    "cycle, and RPM step test remains open follow-up work."
)


def load_experiment_frames(experiments: List[Experiment] = EXPERIMENTS) -> Dict[str, List[Frame]]:
    frames_by_experiment = {}
    for exp in experiments:
        result = parse_file(exp.path)
        frames_by_experiment[exp.name] = result.frames
    return frames_by_experiment


def build_groups(frames_by_experiment: Dict[str, List[Frame]]) -> Dict[str, FrameGroups]:
    all_frames = [f for frames in frames_by_experiment.values() for f in frames]
    sequenced_ids = determine_sequenced_ids(all_frames)
    return {name: group_frames(frames, sequenced_ids) for name, frames in frames_by_experiment.items()}


def run_analysis(experiments: List[Experiment] = EXPERIMENTS):
    """Returns (all_hypothesis_results, map_entries)."""
    frames_by_experiment = load_experiment_frames(experiments)
    groups_by_experiment = build_groups(frames_by_experiment)
    keys = all_candidate_keys(groups_by_experiment)

    all_results: List[HypothesisResult] = []
    map_entries: List[MapEntry] = []

    for key in keys:
        traces = build_traces(key, groups_by_experiment)
        features = compute_features(key, traces, experiments)
        for scorer in HYPOTHESIS_SCORERS:
            all_results.append(scorer(features))
        if key.width == 1:
            map_entries.append(categorize_byte(key, traces, experiments))

    return all_results, map_entries


def top_candidates_per_hypothesis(
    all_results: List[HypothesisResult], top_n: int = TOP_N_PER_HYPOTHESIS
) -> Dict[str, List[HypothesisResult]]:
    by_name: Dict[str, List[HypothesisResult]] = defaultdict(list)
    for result in all_results:
        by_name[result.name].append(result)
    top: Dict[str, List[HypothesisResult]] = {}
    for name, results in by_name.items():
        ordered = sorted(
            results,
            key=lambda r: (-r.confidence, r.key.can_id, r.key.record, r.key.offset, r.key.width),
        )
        top[name] = ordered[:top_n]
    return top


def _render_candidate(result: HypothesisResult, index: int) -> str:
    record_label = f"record {result.key.record}" if result.key.record else "(whole payload, no record byte)"
    lines = [
        f"### Candidate #{index}",
        "",
        f"**{result.key.can_id}**, {record_label}, {result.key.label}",
        "",
        f"Possible {result.name}",
        "",
        f"**Confidence: {result.confidence}%**",
        "",
        "Evidence for:",
        "",
    ]
    lines += [f"- {item}" for item in result.evidence_for] or ["- (none)"]
    lines += ["", "Evidence against:", ""]
    lines += [f"- {item}" for item in result.evidence_against] or ["- (none)"]
    lines += ["", "Suggested experiment:", "", result.suggested_experiment, ""]
    return "\n".join(lines)


def render_hypothesis_sections(all_results: List[HypothesisResult]) -> str:
    top = top_candidates_per_hypothesis(all_results)
    sections = []
    for name in sorted(top):
        candidates = top[name]
        sections.append(f"## {name}")
        sections.append("")
        if candidates and candidates[0].confidence < 30:
            sections.append(
                f"_No candidate currently exceeds 30% confidence for {name}. "
                "The strongest candidates found so far are shown below so the "
                "evidence (or lack of it) is visible._"
            )
            sections.append("")
        for i, result in enumerate(candidates, start=1):
            sections.append(_render_candidate(result, i))
    sections.append("## Trim")
    sections.append("")
    sections.append(TRIM_NOTE)
    sections.append("")
    return "\n".join(sections)


def render_protocol_map(map_entries: List[MapEntry]) -> str:
    by_id: Dict[str, List[MapEntry]] = defaultdict(list)
    for entry in map_entries:
        by_id[entry.key.can_id].append(entry)

    lines = ["# Current Protocol Map", "", DATA_QUALITY_NOTE, ""]
    for can_id in sorted(by_id):
        lines.append(f"## {can_id}")
        lines.append("")
        lines.append("| record | byte | category | detail |")
        lines.append("|---|---|---|---|")
        entries = sorted(by_id[can_id], key=lambda e: (e.key.record, e.key.offset))
        for entry in entries:
            record_label = entry.key.record or "(none)"
            lines.append(f"| {record_label} | {entry.key.offset} | {entry.category} | {entry.detail} |")
        lines.append("")
    return "\n".join(lines)


def render_full_report(all_results: List[HypothesisResult], map_entries: List[MapEntry]) -> str:
    parts = [
        "# SmartCraft Phase 2 -- Signal Hypotheses",
        "",
        "Theories, not conclusions. Every candidate below is scored purely "
        "from the evidence in the experiments currently registered in "
        "`tools/smartcraft_toolkit/experiments.py`; nothing is hardcoded to "
        "a specific CAN ID or byte. Re-run `tools/smartcraft_decoder.py "
        "hypotheses` after adding more captures to update every confidence "
        "value.",
        "",
        "The same byte can legitimately show up as a top candidate for more "
        "than one hypothesis below (e.g. something that scales with RPM fits "
        "both RPM and Raw Water Pressure, since both plausibly increase "
        "together). That is not a bug -- it means the current experiments "
        "don't yet distinguish those two theories, and is exactly the kind "
        "of gap the suggested experiments are meant to close.",
        "",
        "## Data Quality",
        "",
        DATA_QUALITY_NOTE,
        "",
        render_hypothesis_sections(all_results),
        render_protocol_map(map_entries),
    ]
    return "\n".join(parts)
