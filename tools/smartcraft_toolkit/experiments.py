"""The experiment manifest: which captured logs exist and what controlled
condition each one represents.

This is the only place that encodes what we *did* during capture (idle,
1000/1650/1900 RPM, in this order, ~8.4 minutes apart) -- it does not encode
any belief about what any CAN byte means. Adding a new capture (a real
trim-cycle, key-cycle, or RPM-step log, once one exists) means adding one
entry here; every hypothesis in hypotheses.py recomputes from whatever
experiments are registered.

Data-quality note: two other files exist on disk from an earlier ~18-hours-
prior session -- key-cycle.log, rpm-steps.log, trim-cycles.log, and
smartcrafttest.log -- but every one of them turned out to contain a stuck
CAN bus retry storm (the same single frame retransmitted 100,000+ times,
consistent with a Listen-Only capture against a bus with no other node to
ACK it) rather than real telemetry. They are intentionally not registered
here. See docs/HypothesisReport.md "Data Quality" section.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples" / "logs"


@dataclass(frozen=True)
class Experiment:
    name: str
    path: Path
    # Rank among steady-state RPM conditions, low-to-high. Ties (idle/idle2)
    # are the same commanded condition captured twice. None if this
    # experiment isn't an RPM steady-state point at all (e.g. a future
    # trim-cycle log).
    rpm_rank: Optional[int]
    # Chronological order across the whole capture session (0 = first).
    # Used to detect slow drift (e.g. warm-up) independent of RPM.
    session_order: int
    # Free-form tags for experiment kinds beyond RPM/idle, e.g. "trim_cycle",
    # "key_cycle" -- so future evidence functions can select by kind without
    # every hypothesis having to know about rpm_rank/session_order.
    tags: Tuple[str, ...] = ()


EXPERIMENTS = [
    Experiment("idle", SAMPLES_DIR / "idle.txt", rpm_rank=0, session_order=0, tags=("idle",)),
    Experiment("1000rpm", SAMPLES_DIR / "1000rpm.txt", rpm_rank=1, session_order=1, tags=("rpm",)),
    Experiment("1650rpm", SAMPLES_DIR / "1650rpm.txt", rpm_rank=2, session_order=2, tags=("rpm",)),
    Experiment("1900rpm", SAMPLES_DIR / "1900rpm.txt", rpm_rank=3, session_order=3, tags=("rpm",)),
    Experiment("idle2", SAMPLES_DIR / "idle2.txt", rpm_rank=0, session_order=4, tags=("idle", "idle_replicate")),
]
