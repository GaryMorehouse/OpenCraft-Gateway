# SmartCraft Decoder (Phase 1 + 2 — Protocol Analysis & Hypothesis Generation)

A protocol-agnostic tool for reconstructing and analyzing Mercury SmartCraft
CAN traffic from `candump -L` captures, so the protocol can be reverse
engineered from evidence rather than guessed.

**This tool does not decode SmartCraft.** It never *asserts* that a byte is
RPM, trim, temperature, etc. Phase 1 (`decode`/`pretty`/`compare`/`heatmap`)
reconstructs fragmented CAN messages and reports which bytes changed and
which didn't. Phase 2 (`hypotheses`) goes one step further and scores named
signal theories (RPM, coolant, oil pressure, ...) against the evidence in
registered capture experiments — but every result is a confidence-scored
theory with stated evidence for and against it, never a conclusion. See
[docs/ReverseEngineering.md](../docs/ReverseEngineering.md) for the workflow
this feeds into and [docs/HypothesisReport.md](../docs/HypothesisReport.md)
for the current generated report.

## Background

SmartCraft splits messages longer than 8 bytes across multiple CAN frames
sharing one CAN ID. By convention observed in captures, the first payload
byte of each frame is a record/sequence number (`00`, `01`, `02`, ...), and a
frame whose record number is `FF` terminates that logical packet:

```
170#00076D040C63FFFF
170#01025973A01AAC00
170#0200090000000000
...
170#FF00000000000000
```

Not every CAN ID follows this convention — some are single-frame ("atomic")
messages. The tool **detects this per CAN ID from the evidence in the log**
(a `0xFF` terminator plus at least one other record value observed) instead
of hardcoding which IDs fragment. See `smartcraft_toolkit/reconstruct.py`.

## Install

No third-party dependencies — Python 3.9+ standard library only.

## Usage

```sh
# Reconstruct packets and export JSON/CSV
python tools/smartcraft_decoder.py decode capture.log --json out.json --csv out.csv

# Human-readable dump ("Packet N / record bytes")
python tools/smartcraft_decoder.py pretty capture.log --ids 170

# Compare two operating conditions (e.g. idle vs 2500 RPM)
python tools/smartcraft_decoder.py compare idle.log 2500.log --report diff.md

# Per-byte change-rate heat map within a single log
python tools/smartcraft_decoder.py heatmap capture.log --report heatmap.md

# Phase 2: score every registered experiment against named signal hypotheses
python tools/smartcraft_decoder.py hypotheses --report docs/HypothesisReport.md
```

The four Phase 1 subcommands accept `--ids 170 1A0` to restrict analysis to
specific CAN IDs (hex, case-insensitive). `hypotheses` doesn't take log
arguments — it reads whatever is registered in `experiments.py` (see below).

### `decode`

Parses one or more logs, reconstructs logical packets, and exports:

- `--json PATH` — one JSON document: `{"packets": [...], "atomic_messages": [...]}`.
  Each packet is `{"timestamp", "id", "complete", "records": {"00": "...", ...}}`,
  where record values are the frame's payload hex with the record byte
  stripped off. `complete` is `false` if no `FF` terminator was seen (e.g.
  the capture ends mid-cycle) — the packet is still emitted with whatever
  records were collected, marked accordingly, so a dropped frame or a log
  boundary doesn't get lost or silently faked as complete.
- `--csv PATH` — one CSV per CAN ID (`PATH` is reused for the only ID, or
  suffixed `_<ID>` when a log has several), with a `rec_XX` column per record
  key seen for that ID. Atomic (non-fragmented) messages get their own
  `<PATH>_atomic.csv` with a single `payload` column.
- `--pretty` — also print the human-readable dump (see below).

### `pretty`

```
Packet 127
170
00 076D040C63FFFF
01 025973A01AAC00
02 00090000000000
...
```

### `compare`

For every `(CAN ID, record, byte index)` seen in **both** logs, classifies
the byte using only observed value sets — no thresholds, no guessing:

| Verdict    | Meaning |
|------------|---------|
| `constant` | same single value in both logs |
| `changed`  | value sets from the two logs never overlap — a strong signal the byte tracks whatever changed between the two captures |
| `variable` | ambiguous: the byte takes multiple values in at least one log and the two logs' value sets overlap — needs closer inspection, not a clean signal either way |

Bytes present in only one of the two logs are omitted rather than guessed at.

### `heatmap`

For every byte within a single log, reports how often it changed from the
*previous* occurrence of that same record (`change_rate`), plus the count of
distinct values observed. A byte that's "never changed" across an entire log
is very unlikely to be an engine signal; a byte that changes on almost every
frame is a strong candidate for something like RPM.

### `hypotheses` (Phase 2)

Scores every candidate byte/word (single bytes, plus adjacent byte pairs in
both endians) across every experiment registered in
`smartcraft_toolkit/experiments.py` against six named hypotheses — RPM,
Coolant Temperature, Oil Pressure, Raw Water Pressure, Battery Voltage, and
Fuel Level/Depth (the last two are reported jointly since nothing in the
current experiments can tell them apart). Trim is deliberately not scored:
the only capture meant to exercise it turned out to contain no real signal
(see the report's Data Quality section) — that's reported as "not yet
testable," not as a low score.

Every scoring rule lives in `hypotheses.py` and is a short, fixed, documented
point rubric built only from the generic features in `signals.py`
(correlation with commanded RPM, stability within a steady-state capture,
drift across the session, dynamic range used, counter-like monotonicity,
...). No rule looks at a specific CAN ID or byte offset — the same six
rubrics run against every candidate. Confidence values are meant to move as
more experiments are added: register a new capture in `experiments.py` and
re-run.

The same output also drives the **Current Protocol Map**, which buckets
*every* observed single byte into one of: a named "Likely `<Signal>`" tag
(if some hypothesis scored above a threshold), `Likely counters`,
`Likely status bits`, `Likely padding/reserved`, `Likely fuel/depth
(near-constant analog)`, or `Unknown`.

## Design

```
smartcraft_toolkit/
  parser.py             candump -L line parsing -> Frame
  reconstruct.py         per-ID fragmentation detection + logical-packet assembly (Phase 1)
  compare.py              per-byte value/​change-rate statistics, two-log comparison (Phase 1)
  report.py                Markdown rendering for compare/heatmap (Phase 1)
  exporters.py             JSON/CSV writers (Phase 1)
  pretty.py                 human-readable packet dump (Phase 1)
  experiments.py             Phase 2 experiment manifest (which logs, which condition)
  signals.py                  Phase 2 generic candidate extraction + statistical features
  hypotheses.py                 Phase 2 named-signal scoring rubrics
  protocol_map.py                Phase 2 per-byte categorization
  hypothesis_report.py            Phase 2 orchestration + Markdown rendering
  cli.py                            argparse subcommands
```

Nothing in this package hardcodes a CAN ID or a byte meaning. Fragmentation
detection, byte-change statistics, comparison verdicts, and hypothesis
confidence are all derived from the frames actually present in whatever
log(s)/experiments are given to it.

## Tests

Stdlib `unittest`, no extra dependencies:

```sh
python -m unittest discover -s tools/tests -t .
```

## Sample data and output

`tools/samples/logs/` holds five short real captures from the 2006 Sea Ray
240 Sundancer / MerCruiser 5.0 MPI (ECM555) test rig: `idle.txt`, `idle2.txt`,
`1000rpm.txt`, `1650rpm.txt`, `1900rpm.txt`. (`.txt`, not `.log`, so they
aren't swept up by the repo's `*.log` gitignore rule.)

`tools/samples/output/` holds generated output from running the tool against
those logs — JSON/CSV decode of `idle.txt`, a pretty-printed dump of its
`170` packets, a heat map of `idle.txt`, and a comparison report between
`idle.txt` and `1900rpm.txt`. Regenerate with:

```sh
python tools/smartcraft_decoder.py decode tools/samples/logs/idle.txt \
  --json tools/samples/output/idle_decoded.json --csv tools/samples/output/idle_decoded.csv
python tools/smartcraft_decoder.py pretty tools/samples/logs/idle.txt --ids 170 \
  > tools/samples/output/idle_170_pretty.txt
python tools/smartcraft_decoder.py heatmap tools/samples/logs/idle.txt \
  --report tools/samples/output/idle_heatmap.md
python tools/smartcraft_decoder.py compare tools/samples/logs/idle.txt tools/samples/logs/1900rpm.txt \
  --label-a idle --label-b 1900rpm --report tools/samples/output/idle_vs_1900rpm_compare.md
```
