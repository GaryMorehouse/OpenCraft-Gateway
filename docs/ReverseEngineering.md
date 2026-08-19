# Reverse Engineering SmartCraft

We do not have Mercury's SmartCraft protocol specification. Everything about
the CAN traffic captured off the 2006 Sea Ray 240 Sundancer / MerCruiser 5.0
MPI (ECM555) has to be established from evidence in real captures, not
assumed.

**Rule: no byte gets a name (RPM, trim, oil pressure, ...) until it's been
correlated against a known ground truth** (a gauge reading, a commanded trim
position, a logged RPM from another source, etc.) at the moment the frame
was captured. Until then, bytes are referred to only by `(CAN ID, record,
byte index)`.

## Tooling

[`tools/smartcraft_decoder.py`](../tools/smartcraft_decoder.py) (usage:
[tools/README.md](../tools/README.md)) reconstructs fragmented CAN messages
from `candump -L` logs and reports which bytes changed and which didn't. It
is the first step for any new capture: reconstruct, then look for bytes
whose value tracks something you changed on the boat (throttle, trim, key
position) between two captures.

Workflow:

1. Capture two logs that differ in exactly one condition you can name (e.g.
   `idle.log` vs `1900rpm.log`, or before/after a trim change).
2. `smartcraft_decoder.py compare log_a log_b --report diff.md` — bytes
   marked `changed` (disjoint value ranges between the two logs) are the
   candidates for whatever you varied.
3. `smartcraft_decoder.py heatmap log.log --report heatmap.md` — within a
   single log, a byte that's "never changed" is very unlikely to be a live
   engine signal (more likely a checksum, a constant, or padding); a byte
   that changes on nearly every frame is a strong live-signal candidate.
4. Cross-reference (2) and (3) across multiple RPM/trim points before naming
   anything. A byte can be `changed` between two logs for reasons unrelated
   to the condition you varied (e.g. incidental voltage drift).

## Capture setup

- Raspberry Pi Zero 2 W + MCP2515 (8 MHz) via SocketCAN
- `candump -L`, 250000 baud, Listen Only mode

## Structural findings so far

These describe frame *structure*, not meaning — see the rule above.

| CAN ID | Frame type | Records observed | Notes |
|---|---|---|---|
| `170` | fragmented | `00`-`06`, `FF` | |
| `1A0` | fragmented | `00`-`0C`, `FF` | |
| `1E0` | fragmented | `00`-`17`, `FF` | |
| `1F0` | fragmented | `00`, `01`, `FF` | |
| `1FFD4041` | **uncertain** (extended/29-bit ID) | `02`-`05` only | never shows `00`, `01`, or `FF` in any capture -- classify_ids therefore treats it as atomic (no confirmed terminator), but it does cycle through 4 distinct leading-byte values, so it may use a different framing convention entirely. Phase 2's candidate scan groups it by leading byte anyway (see `signals.py`) without asserting it fragments the same way 170 does. |
| `00000B41` | atomic in short captures; a multi-shape handshake immediately after key-ON in longer ones | — | earlier finding ("3-byte payload, first byte constant `0x83`") only held for the mid-session slice the five short sample logs happened to cover. In `master-test01` (a full session starting at key-ON) it opens with a ~5s burst of several distinct, varying-length payloads (1/2/3/5 bytes), then settles into the previously-documented steady-state pattern. See [docs/master-test01-analysis.md](master-test01-analysis.md) section 3. |
| `0000410B` | atomic in short captures; a multi-shape handshake immediately after key-ON in longer ones | — | same correction as `00000B41` above -- earlier "1-byte payload, constant `0x01`" only held for the mid-session slice; opens with a varying-length (1/2/4-byte) handshake burst in `master-test01`. Its steady-state messages match `00000B41`'s timestamps exactly, suggesting a request/response pair or shared broadcast. |
| `0E3792F3` | atomic (single-frame) | — | seen only in `smartcrafttest.log`, which is no longer on disk to re-check. `master-test01` separately shows an ID `0E3790F3` (note: `90`, not `92`) with a similar burst-then-silence pattern -- possibly the same ID misrecorded in this earlier note, possibly a genuinely different ID. Unresolved; see [docs/master-test01-analysis.md](master-test01-analysis.md) section 2. |

"Fragmented" here means `smartcraft_decoder.py` detected the record-number /
`0xFF`-terminator convention from the frames actually seen (see
`tools/smartcraft_toolkit/reconstruct.py::classify_ids`) — it isn't
hardcoded per ID.

## Phase 2: hypothesis generation

Phase 1 (above) finds bytes that changed; it doesn't say what they might
mean. Phase 2 (`smartcraft_decoder.py hypotheses`) goes one step further:
it scores every candidate byte/word against six named signal theories (RPM,
Coolant Temperature, Oil Pressure, Raw Water Pressure, Battery Voltage,
Fuel Level/Depth) using only generic, evidence-based shape tests (does it
track commanded RPM, does it drift across the session, does it stay in a
narrow band, does it look like a counter, ...) -- never a hardcoded
CAN ID or byte answer. Every result carries a confidence score, evidence for
and against, and a suggested experiment that would move that confidence in
either direction. See [tools/README.md](../tools/README.md#hypotheses-phase-2)
for the mechanics and [docs/HypothesisReport.md](HypothesisReport.md) for the
current generated report and Current Protocol Map (every observed byte
bucketed by evidence, not asserted).

**Confidence values are meant to move as more captures are collected.**
Adding a real trim cycle, key cycle, or RPM step test means adding one entry
to `tools/smartcraft_toolkit/experiments.py` and re-running the command --
nothing else needs to change.

## Sample data

Five short real captures (idle and three RPM points) are committed under
[tools/samples/logs/](../tools/samples/logs/) as test fixtures / usage
examples, and are also the experiments Phase 2 currently scores against.

A separate, ~18-hours-earlier capture session also exists on disk
(`key-cycle.log`, `rpm-steps.log`, `smartcrafttest.log`, `trim-cycles.log`,
5-10MB each) but was found, on inspection, to contain no real signal at all
-- every one of those four files is a single CAN frame retransmitted
100,000+ times with no other content, consistent with a Listen-Only capture
against a bus with no other node available to ACK it. They are not
committed and are excluded from Phase 2's analysis. Those raw files no
longer exist on disk as of the `master-test01` analysis below, so this
description can no longer be independently re-verified.

**`master-test01.txt`** (committed alongside the five logs above) is a
single ~22-minute continuous capture spanning key-ON, engine start,
extended idle, two RPM-step tests, trim cycles, and shutdown -- the real
trim cycle, key cycle, and RPM step test called for above. It has a real,
timestamped field sheet of gauge readings behind it and its own dedicated
analysis: see [docs/master-test01-analysis.md](master-test01-analysis.md).
It is registered as a `continuous`-tagged `Experiment` (not a single
steady-state condition) in `experiments.py` and is included in the
regenerated [docs/HypothesisReport.md](HypothesisReport.md).
