# master-test01.log — Capture Analysis

Analysis of `master-test01.log`, a controlled SmartCraft capture performed
against the 2006 Sea Ray 240 Sundancer / MerCruiser 5.0 MPI following the
`SmartCraft Controlled Capture Data Sheet` protocol (key-ON, engine start,
extended idle, RPM steps, trim cycles, an optional tach
connect/disconnect/reconnect experiment, engine stop).

**Everything in this document is a theory scored against evidence, not a
decode.** No byte is asserted to mean anything; every candidate below
states what supports it, what argues against it, and what would settle
it. Where this report's read of the evidence differs from
[`docs/HypothesisReport.md`](HypothesisReport.md) (the Phase 2 tool's
automated output), that's flagged explicitly -- the tool is built around
discrete steady-state logs and cannot see within-session structure the
way a manual pass over one long continuous capture can.

A working copy of the raw log is committed at
[`tools/samples/logs/master-test01.txt`](../tools/samples/logs/master-test01.txt)
(byte-identical to the original `master-test01.log`, renamed `.txt` per
this repo's existing sample-log convention so it isn't swept up by
`.gitignore`'s `*.log` rule). The filled-in field sheet for this exact
test is copied to
`tools/samples/SmartCraft Controlled Capture test 01.pdf`. Neither
original file supplied for this analysis was modified.

## 1. Capture integrity

- **File size**: 9,228,288 bytes (9.23 MB); checksum-verified identical to
  the original.
- **Lines**: 198,787. **Parsed frames**: 198,784. **Malformed lines**: 4 --
  one `nohup: ignoring input` banner line (the capture was started under
  `nohup`, and its stdout message leaked into the log), and three lines
  near the very end of the file where the frame text runs directly into a
  long run of `\x00` bytes with no newline between them.
- **Duration**: 1311.86 s (**21 min 52 s**), first frame at capture-relative
  `t=0.000s`, last frame at `t=1311.86s`.
- **Unique CAN IDs**: 11 -- `170`, `1A0`, `1FFD4041`, `1E0`, `1F0`,
  `00000B41`, `0000410B`, `0E3790F3`, plus three singleton IDs (`538`,
  `3E0`, `378`) that each appear exactly once.
- **Standard vs extended**: `170`, `1A0`, `1E0`, `1F0`, `538`, `3E0`, `378`
  are 11-bit standard IDs. `1FFD4041`, `00000B41`, `0000410B`, `0E3790F3`
  are 29-bit extended IDs.
- **Frame counts by ID**:

  | ID | count | payload length(s) | notes |
  |---|---|---|---|
  | `170` | 105,792 | 8 | main fragmented message, ~12.4ms mean gap |
  | `1A0` | 73,840 | 8 | main fragmented message, ~17.8ms mean gap |
  | `1FFD4041` | 16,759 | 8 | ~78ms mean gap, never repeats a payload back-to-back |
  | `1E0` | 1,825 | 8 | ~0.7s mean gap |
  | `1F0` | 216 | 8 | ~5.9s mean gap |
  | `00000B41` | 165 | 1, 2, 3, or 5 bytes | **not** a fixed 3-byte payload -- see section 3 |
  | `0000410B` | 162 | 1, 2, or 4 bytes | **not** a fixed 1-byte payload -- see section 3 |
  | `0E3790F3` | 22 | 8 | 21 identical frames in the first 7ms, one more at t=68.146s |
  | `538`, `3E0`, `378` | 1 each | 8 | singletons, see section 2 |

- **Malformed/noise frames**: besides the `nohup` banner, three lines late
  in the file are corrupted by a run of NUL bytes overwriting what should
  be line breaks, merging that line's timestamp/payload into the next --
  consistent with the destination file having been preallocated (or a
  page zero-filled) and the capture process being torn down without
  cleanly flushing.
- **The capture ends while the engine is still running.** In the last 15
  samples before EOF (t=1310.3-1311.8s), the strongest RPM/pressure-shaped
  candidates (`170` record `00` byte 1, `170` record `01` bytes 4-5, `1A0`
  record `05` bytes 1-2) are all still at mid-session, "running" values.
  This is now explained by the recovered field sheet (section 4): its
  last entry is "23:03, 2500 RPM" with no "Engine STOPPED"/"Key OFF" rows
  filled in at all, and the file's own duration lands almost exactly on
  23:03 when added to the sheet's 22:41 key-on time. So this is not
  evidence of an unplanned truncation mid-protocol -- the capture simply
  appears to end right around when the documented test's last planned RPM
  point was reached. The tail NUL-byte corruption above is still a real,
  separate data-quality issue, just not evidence of a *lost* portion of
  the protocol.
- **Repeated/stuck traffic**: `170`'s longest run of an identical
  consecutive payload is 245 frames, all within the first ~64s
  (key-ON/engine-OFF, before the engine actually turns -- nothing on the
  bus should be changing yet, so this is expected, not a fault). No other
  ID shows a stuck-frame run remotely close to the "100,000+ retransmits
  of one frame" pattern documented for the earlier, unusable capture
  session (section 13/14). `0000410B` spends most of the file alternating
  a single byte (`01`) on a slow ~15s cadence, but that's a real periodic
  message, not a stuck retry (section 3).
- **Verdict: this looks like a genuinely healthy, live SmartCraft
  conversation** -- multiple independently-timed CAN IDs, real dynamic
  range on several fields, a clean key-ON -> crank -> running transition
  recovered directly from the data (section 5), and no sign of the
  single-frame retry storm that made the earlier session's four large
  files unusable.

## 2. CAN ID inventory

Per-byte constant/changing/counter/status classification for every
observed byte is generated mechanically by the existing toolkit and is not
reproduced by hand here -- see the regenerated
[`docs/HypothesisReport.md`](HypothesisReport.md) "Current Protocol Map"
(now includes `master-test01`; see section 4) and the raw heat map at
`tools/samples/output/` for the full table. Headline points not already
obvious from that table:

- **`00000B41` and `0000410B` are not fixed-length, constant-payload
  atomic messages.** The earlier structural finding ("3-byte payload,
  first byte constant 0x83" / "1-byte payload, constant 0x01") was true
  *only* of the narrow mid-session slice the five short sample logs
  happened to capture. In this longer capture, both IDs open with a
  ~5-second burst of several distinct, varying-length payloads
  immediately after key-ON, then settle into the previously-documented
  steady-state pattern for the rest of the session. Full detail in
  section 3.
- **`0E3790F3`** (not `0E3792F3` as an earlier draft of
  `docs/ReverseEngineering.md` recorded for a similarly-named ID seen only
  in one of the now-deleted, unusable old capture files -- that file no
  longer exists to check, so this may be a genuinely different ID or a
  transcription slip in that earlier note; flagged, not resolved) sends
  21 back-to-back identical 8-byte frames in the first 7ms of the capture,
  then one more identical frame at t=68.146s, then nothing for the
  remaining ~1243 seconds of the file.
- **Three singleton standard IDs** (`538` at t=68.146s, `3E0` at
  t=1031.21s, `378` at t=1058.01s) each appear exactly once in the whole
  file. `538`'s single frame lands at *exactly* the same instant as
  `0E3790F3`'s lone late repeat and within ~2 seconds of the
  RPM/oil-pressure/water-pressure candidates' engine-start transition
  (section 5) -- independent corroboration that a real bus-wide event
  (engine start) occurred right around t=66-70s.
- No CAN ID shows a payload-length or fragmentation-convention conflict
  with what `smartcraft_toolkit.reconstruct.classify_ids` already detects
  for `170`/`1A0`/`1E0`/`1F0` (all still cleanly fragmented,
  record+0xFF-terminator). `1FFD4041` still never shows a `00`/`01`/`FF`
  record byte in this capture either, so its true framing convention
  remains unconfirmed.

## 3. Important message structures

### `170`

Unchanged structurally from prior findings: fragmented, records `00`-`06`
plus `FF`, 7-byte payload per record after the record byte. See sections
5-12 for the individual candidate bytes now under test.

### `1A0`

Unchanged structurally: fragmented, records `00`-`0C` plus `FF`. One
notable new candidate: record `00` bytes 1 and 2 (values `{0,1,2}` and
`{0,1}` respectively) step to a new value at **exactly** t=68.4s, 662.1s,
956.1s, 1158.6s, and 1271.8s -- the same five moments where the
RPM/oil-pressure candidates transition between plateaus (section 5). This
looks like a low-cardinality engine/operating-mode status flag, not a
physical analog signal, but it independently corroborates that those five
timestamps are real regime changes, not artifacts of this report's
segmentation method.

**New (2026-08-20), prompted by Gary asking whether engine hours should be
on the bus:** record `02` byte 3 ticks up by exactly 1 count roughly every
59.58s. Measured across 21 consecutive ticks spanning the full 21.9-minute
capture: mean interval 59.576s, stdev 0.006s -- essentially zero jitter,
i.e. wall-clock-driven, not frame-driven. Every other byte in this capture
that behaves like a "counter" ticks once per CAN frame (thousands of times
over the session); this is categorically different. The byte starts at raw
23 (not 0) at key-on and reaches 44 by the end of the capture (22 distinct
values, rise of 21), consistent with a low byte of a continuously-running
engine-hours/run-time meter that was already partway through a count when
this capture began, rather than a "minutes since key-on" field starting
fresh. Replay's guessed gauge rebases this to "minutes elapsed since this
capture started" (raw 23 -> 0) for readability -- that offset is not a
claim about the engine's true accumulated hours, which this single capture
cannot determine. Not one of the toolkit's 6 formally-scored hypotheses,
so it carries a `hypothesis` tier in replay (the evidence for the
counter's identity is strong) but an unscored (-1) confidence rather than
a percentage, distinguishing "found but not run through the formal scorer"
from "scored and weak."

**Cross-validated on a second, independent capture (2026-08-21,
`drive03.log`, Gary's next drive).** This capture has no real timestamps
at all (plain `candump can0`, not `-L` -- see `docs/replay.md`), which
made this counter unusually useful: it still ticks up perfectly cleanly
across the whole ~550,000-frame file (raw 78 -> 139, 62 transitions, zero
skips or resets), and the frame-count gap between every single tick is
9008-9048 frames -- under 0.5% spread, for the *entire* ~61-minute drive
regardless of engine state. That consistency is itself strong evidence
this is a real, stable hardware/RTC-driven clock rather than anything
tied to one session, and it was used to build a proper real-elapsed-time
calibration for this otherwise-timestamp-less file (each tick assumed
59.576s apart, from this capture's own measured mean above), which
every other finding on `drive03.log` in this document relies on. Gary
separately reported the engine's real cumulative-hours meter read ~633
hours at the start of this drive; under the hypothesis that this byte is
literally `(total real minutes) mod 256`, 633.0 hours predicts raw 92,
while the observed start-of-file raw is 78 -- consistent with ~632.77
hours, about 14 minutes off a literal 633.0. Given "633 hours" was a
rounded verbal reading, this is broadly consistent, not an exact
confirmation, and doesn't independently verify the mod-256-total-minutes
model specifically (only that the byte keeps behaving like *a* very
regular counter).

**Also checked and ruled out during this same search (2026-08-20):**
- **Speed/pitot**: no single byte position stands out as a speed
  candidate. Across `170`/`1A0`/`1E0`/`1FFD4041` there are 292 byte
  positions that stay frozen at exactly 0 for the entire capture --
  consistent with Gary's report that the pitot sensor was physically
  unhooked during this test (an unhooked sensor plausibly reports a fixed
  zero/invalid value), but with 292 candidates there is no way to
  distinguish "this one is speed" from the rest using this capture alone.
  A follow-up capture with the pitot connected and boat underway, compared
  against this one, would collapse that field of candidates the same way
  the RPM step-tests did for RPM/water pressure.
- **Fault/overheat codes**: the only known low-cardinality status bytes in
  this capture are `1A0` record `00` bytes 1 and 2 (this section, above),
  and they only ever step at the same five RPM-regime-change timestamps
  already documented in section 5 -- no isolated, fault-like event
  distinct from those five transitions. Separately, the coolant
  temperature candidate (section 6) never exceeds ~159°F anywhere in this
  capture, so no overheat condition is indicated as having occurred
  *during master-test01 itself*, even though Gary has experienced overheat
  on the boat on other occasions. If a capture exists from an actual
  overheat event, that would be a much better place to look for a fault
  code signature than this one.
- **A second, oil-temperature-like signal**: searched `1E0`, `1F0`,
  `1FFD4041`, `00000B41`, and `0000410B` for a second monotonic
  warm-up-shaped byte (the same shape used to identify the coolant
  candidate in section 6). Found nothing matching -- the one slow-changing
  byte in that group (`1FFD4041` record `00` byte 3) declines rather than
  rises and looks like an ordinary wraparound counter, not a temperature
  curve. No oil-temperature candidate is reported.

### `1FFD4041`

Still cycles through leading-byte values with no `00`/`01`/`FF` record
ever observed, and still never repeats an identical payload twice in a
row across 16,759 frames -- the busiest, most continuously-changing ID in
the whole capture relative to its frame count. Framing convention remains
unconfirmed.

### `00000B41` and `0000410B`

These two IDs are the most structurally interesting new finding in this
capture. Both show the same two-phase pattern:

**Phase 1 (t=0.1s-5.1s, immediately after the file starts / key-ON):** a
burst of several distinct payload shapes, repeating roughly every ~2.2s
for three rounds with different data each round --

```
0000410B:  AA | 29 | DB1B0275 | 0206 | 077A8056 | 05      (round 1, t=0.1-1.1s)
0000410B:  AA | 29 | 7440111B | 0206 | 077A8056?| 05      (round 2, t=2.3-2.8s)
0000410B:  AA | 29 | 676A2334 | 0206 | 7CD6C357 | 05      (round 3, t=4.5-5.0s)

00000B41:  55 | C000 | FA0206 | F91C0C508B                (round 1, t=0.1-1.1s)
00000B41:  55 | C000 | FA0206 | F931FB386B | 8005 | 81CC00C02B   (round 2, t=2.3-2.8s)
00000B41:  55 | C000 | FA0206 | F90BA658DB | 8005 | 81998852E3   (round 3, t=4.5-5.0s)
```

The repeated 1-byte tags (`AA`, `29`, `05` / `55`, `05`, `81`) stay
constant across rounds while the 3-4-byte payloads change every round --
the shape of a repeated request/response or address-claim handshake, not
noise. This is exactly the kind of "initialization traffic" section 13
asks about.

**Phase 2 (t=5.1s onward, for the rest of the file):** both IDs settle
into a simple steady-state pattern -- `0000410B` sends a constant 1-byte
`01` roughly every ~15s (in pairs ~3s apart, then a ~15s gap), and
`00000B41` alternates between two 3-byte payloads (`83 07 17` /
`83 04 FF`) on the identical cadence. **The timestamps of `0000410B`'s and
`00000B41`'s steady-state messages match exactly**, frame for frame, for
the rest of the capture. This is strong evidence the two IDs are either a
request/response pair (their ID values, `00 00 0B 41` vs `00 00 41 0B`,
are byte-position-swapped, consistent with a source/destination
addressing scheme in the extended-ID space) or two halves of one periodic
broadcast from the same node.

This fully explains the earlier finding that `00000B41` was "constant at
0x83" and `0000410B` was "constant at 0x01" -- the five short sample logs
were all captured well after key-ON, so they only ever saw this Phase 2
steady-state slice. This capture is the first to catch the actual
power-on sequence.

## 4. Byte-change analysis

### Ground truth: the recovered field sheet

**A filled-in field sheet for this exact test exists**
(`SmartCraft Controlled Capture test 01.pdf`) and supersedes the generic
"expected approximate values" originally used to scope this analysis. It
gives real, clock-timestamped, multi-point gauge readings for this
specific run:

| Time | Event/RPM | Coolant °F | Oil PSI | Water PSI | Voltage | Fuel % | Depth ft | Trim |
|---|---|---|---|---|---|---|---|---|
| 22:41 | Key ON | 95 | 0.5 | 0 | 13.4 | 100 | 8.9 | Down (0) |
| 22:43 | 590 | 102 | 50.3 | 0.6 | 13.8 | 100 | 8.9 | |
| 22:47 | 580 | 141 | 49.6 | 1.0 | 13.9 | 100 | | |
| 22:49 | 560 | 154 | 49.2 | 0.8 | 13.9 | 100 | | |
| 22:50 | 550 | 154 | 49.7 | 0.8 | 13.9 | 100 | | |
| 22:51 | 540 | 152 | 49.9 | 0.7 | 13.8 | 100 | | |
| 22:54 | 900 | 152 | 53.3 | 1.7 | 14.0 | 100 | | |
| 22:54 | 1380 | 152 | 56.3 | 2.8 | 14.0 | 100 | | |
| 22:54 | 1910 | 152 | 61.6 | 3.6 | 14.0 | 100 | | |
| 22:54 | 2570 | 152 | 65.9 | 4.1 | 14.0 | 100 | | |
| 22:58 | 560 | 159 | 46.7 | 0.6 | 14.0 | 100 | | |
| 22:59-23:00 | Trim: Down, Up, Down, Up, Down, Up, Down (see note) | | | | | | | |
| 23:01 | 550, 990, 1400, 2000 | | | | | | | |
| 23:03 | 2500 | | | | | | | |

Notes on the sheet: "Shore power on during this test", "RPM numbers are
approximate", "depth fluctuated between 8.9 and ~9.1 ft", "Times are
approximate" (minute resolution only, no seconds). **The tachometer was
physically connected for the entire test** (confirmed directly by Gary,
who ran the capture); **no "Tach Experiment" rows were filled in**
because the *deliberate connect/disconnect/reconnect A/B toggle* was not
performed during this run -- that is a separate fact from the tach's
connection state, which was "connected" throughout. See section 13.
**Trim note (confirmed directly by Gary)**: the 22:41 "Down (0)" entry is
trim's starting position -- fully trimmed down -- not one of the test's
movements. From that starting position, the 22:59-23:00 sequence is
**three full up/down cycles (6 movements: Up, Down, Up, Down, Up,
Down)**; the sheet's own first "Down" entry at 22:59 restates the
already-established starting position rather than logging a new move.
See section 12. **RPM control note (confirmed directly by Gary)**: the
RPM steps were not held steady at each target -- it was easy to overshoot
the intended test RPM by hand, so the throttle was repeatedly pulled back
and eased up to settle near each target value. The single RPM (and
oil/water PSI) figure logged per step in the table above is therefore an
approximate snapshot taken once things looked roughly settled, not a
reading from a clean, held plateau -- the engine's actual instantaneous
RPM (and, since both respond quickly to RPM, oil pressure and water
pressure) most likely oscillated noticeably around each target during
this maneuvering, wider than the single logged number implies. This
matters directly for sections 5, 7, and 8. A second page lists fuel
consumption (0.7, 1.1, 1.5, 1.7, 1.9, 0.8 Gal/Hr), presumably
corresponding to the idle/900/1380/1910/2570/idle sequence, though not
explicitly linked row-by-row.

**This changes two of the generic ground-truth assumptions the task
started from**: fuel reads **100%** throughout this specific test, not
~48% (a full tank, evidently, for this run), and coolant starts at
**95°F**, not ~72°F (the engine was apparently already warm at key-on).
Depth (8.9-9.1ft) and the oil/water/RPM shapes match the generic priors
reasonably well. All ground-truth statements in sections 5-12 use this
sheet's actual numbers.

**Time alignment**: the sheet gives clock time; the CAN log gives
capture-relative seconds. Treating 22:41 (Key ON) as file `t=0` is well
supported: the file's first ~66 seconds are flat/inert exactly as
expected for key-on/engine-off, and the file's total duration (1311.86s)
added to 22:41 lands at 23:02:52 -- almost exactly the sheet's last entry
("23:03, 2500 RPM"). Given only minute-resolution, approximate clock
times, this mapping should be trusted to roughly +/-30-60s, not tighter --
broad trends and relative-magnitude comparisons are reliable; exact
numeric correlation at the level of a single RPM step is not.

### Hypothesis engine run

`master-test01` has been registered as a new `Experiment` in
`tools/smartcraft_toolkit/experiments.py` (`rpm_rank=None`,
`session_order=5`, tagged `field_session`, `continuous` -- it is not a
single steady-state condition, so it can't claim one `rpm_rank`).
`docs/HypothesisReport.md` has been regenerated from the full
six-experiment set.

**One code change was needed to accommodate it honestly**:
`within_condition_stability` in `signals.py`/`hypotheses.py` previously
assumed every registered experiment is a single steady condition -- true
for the five old logs, false for a 22-minute session that deliberately
sweeps through many conditions. Without a fix, a *real* RPM-like signal
correctly varying within `master-test01` would have been scored as
"unstable" and penalized for doing exactly what it should. `compute_features`
now excludes any experiment tagged `continuous` from that one rubric only
(every other feature -- session drift, near-constant score, distinct-value
count, monotonic-counter detection -- still pools `master-test01`'s data
in). A test (`TestStabilityExcludesContinuousExperiments`) confirms a
synthetic RPM-shaped continuous trace no longer tanks the stability score,
and a second new test file (`test_experiments.py`) sanity-checks that
every registered experiment's log file exists on disk and that
`continuous`-tagged experiments never claim an `rpm_rank`. All 77 existing
+ new tests pass.

**What moved in the regenerated report, and why**:

- **RPM**: top candidate changed from `1A0` record `05` bytes 1-2 (was
  70%) to `170` record `01` bytes 4-5 BE (now top at 65%); `1A0` record
  `05` dropped out of the RPM top-3 entirely -- the tool independently
  reflecting the same shift this report's manual analysis found (section
  5), purely from `master-test01`'s much wider pooled value range
  diluting that candidate's apparent RPM correlation profile.
- **Raw Water Pressure**: `1A0` record `05` bytes 1-2's score fell from
  80% to 65% and it's no longer the sole top candidate; `170` record `00`
  bytes 0-1 BE now appears at 60%.
- **Coolant Temperature**: top candidate changed from `1E0` record `03`
  bytes 2-3 to `170` record `03` bytes 0-1 (LE), confidence up from 40% to
  55% -- reflects the real warm-up trend now visible (section 6).
- **Battery Voltage**: `00000B41` candidates rose from 45% to 55%, but the
  record label shown (`record 81`) is itself an artifact of the new
  handshake-burst evidence -- see the small-sample caveat below.
- **Fuel/Depth, Oil Pressure**: candidate identities and confidence
  essentially unchanged (oil pressure stayed at 80%; fuel/depth stayed at
  40%).

**A methodology caveat surfaced by this run, not hidden from it**: because
`00000B41` and `0000410B` now show real first-byte variation (the
handshake burst, section 3), the toolkit's `determine_sequenced_ids` now
treats them as "sequenced" and groups their frames by first byte the same
way it groups `170`'s genuine record convention. Some of the resulting
groups (e.g. `00000B41` record `81`) have only a handful of samples, all
from the brief startup burst, pooled together with the old five logs'
complete absence of that record. Those specific candidates' confidence
numbers should be read with that small-sample caveat in mind rather than
taken as equally well-supported as, say, the oil-pressure candidate's 80%
(built from thousands of samples across six experiments).

The mechanically-generated per-byte heat map (change rate, distinct-value
count) for the full file is available via
`python tools/smartcraft_decoder.py heatmap tools/samples/logs/master-test01.txt --report <path>`
and is not re-pasted here in full; nothing in it contradicts the specific
candidates discussed in sections 5-12.

## 5. RPM hypothesis

**CAN ID**: `170`
**Bytes**: record `01`, bytes 4-5 (BE) -- current top candidate; record
`01` byte 5 alone also scores.
**Observed behavior**: near-zero/noisy through t=66s (key-ON, engine
OFF), then at **t=66.45s** jumps to 164 and immediately **oscillates
hard** -- rising to 5454 by t=68.5s, dropping to 3297 by t=69s, rising to
4796 by t=69.6s, dropping to 3634 by t=70.3s -- a damped "ringing"
pattern before settling to a noisy plateau (~4300-4600) by t=75-90s.
Stays essentially flat (spread ~4270-4590) through the long idle
stretch (t~120-600s), then rises to a modest ~5200-6700 plateau during
the RPM-step-shaped excursion around t~760-850s.
**Physical observation**: real RPM (field sheet) is 540-590 through the
idle stretch (+9% spread) and steps 900->1380->1910->2570 during the
22:54 RPM test (+186% overall).
**Evidence FOR**: immediate, jagged onset exactly when the engine catches
(t=66.45s, ~1.6-2s before the smoother `1A0` candidate) -- consistent
with a raw crank-speed reading seeing the real roughness of a cold start
and catch; idle-window stability (~7.5% spread) is a good relative match
to real RPM's own idle-window stability (~9% spread) over the same
real-world window. **The candidate's own jaggedness during the RPM-step
window is now better explained, not just noise**: per Gary, the RPM steps
were not held steady -- it was easy to overshoot the target, so the
throttle was repeatedly pulled back and eased up to settle near each
value (section 4). A genuine raw-RPM signal during that kind of manual
overshoot/correction should look bumpy and non-monotonic, not like a
clean staircase, and that's exactly this candidate's shape in that window
(section 5's earlier fine-grained trace shows real back-and-forth
movement, not a smooth ramp).
**Evidence AGAINST**: the observed rise during the RPM-step window
(~+29%) is far short of real RPM's own +186% span between the logged
step values -- and, since those logged values are themselves approximate
snapshots of a moving target rather than held plateaus (section 4), the
engine's true instantaneous range was most likely wider still. If this is
a raw tachometer count, its gain looks heavily compressed relative to the
real RPM range even accounting for that uncertainty. The absence of a
clean 4-level staircase, by itself, is no longer treated as evidence
against this candidate (see above) -- but the gain shortfall remains a
real, unresolved gap.
**Confidence: moderate**, trending toward moderate-to-good. **Update
(2026-08-20)**: Gary confirmed real RPM directly at three points during
live replay (900, 1380, and a settled 2570 RPM, the last one noisier --
he described it as fluctuating before settling), letting
`services/replay` fit this candidate's raw value against real RPM with a
piecewise curve instead of a single line (the slope roughly triples then
triples again across segments: 0.13 -> 0.23 -> 0.62 -> 3.15 RPM/count --
see `candidates.py`). Onset timing, idle-stability, the step-test's
jagged shape, and now three real RPM anchors across the confirmed range
all support this candidate; the main open question is no longer "does it
track RPM" but "how much further compression exists beyond 2570 RPM",
since the field sheet's steps stop there.
**Competing hypothesis**: oil pressure was the leading competing read
here, but section 7's 2026-08-20 update found that candidate fails to
track real oil pressure at all across the same RPM range (flat-to-lower
raw value at 2570 RPM despite real oil pressure peaking there) -- no
longer a strong competitor.
**Best experiment to distinguish it**: log an actual tachometer reading
(not just event timing) alongside a capture, ideally with the RPM steps
each held for a clearly logged, multi-second duration so a scale factor
(if any) can be fit directly against this byte.

**Update (2026-08-21): this candidate appears to break down well above
2570 RPM.** `drive03.log` (Gary's next drive, no real timestamps -- see
section 3's engine-hours-based time calibration) describes varying RPM
several times with a peak around 3700, mostly running 550-1000 RPM. This
candidate's raw value, calibrated the same way as here, never implies
more than ~890 RPM anywhere across the entire ~61-minute file -- it
mostly sits around 550-700 RPM-equivalent with two brief dips to
~225-300, and its single highest value anywhere in 550,000+ frames still
only implies ~890 RPM. A systematic search for a genuine engine-off
signature and for an alternate byte with a clean, sustained high plateau
both came up empty (checked every byte and 16-bit word combination
across `170`/`1A0`/`1E0`/`1F0`) -- nothing in the raw log matches a
sustained on-plane run the way this candidate's own calibration would
require it to. Since this candidate's fit was only ever confirmed up to
a real 2570 RPM anchor (section 4), and its InterpolatedGuess already
flagged extrapolation past that point as "the least trustworthy part of
this guess," the most likely explanation is that whatever relationship
holds between this byte and true RPM below ~1400 RPM does not continue
cleanly at higher engine speeds -- not that drive03 somehow avoided ever
reaching them. See section 8 for an alternate RPM estimate (via water
pressure) that fits drive03's described shape much better.
**Confidence for the extrapolated (>2570 RPM) portion of this candidate
downgraded to weak** as a result; the confirmed idle-to-2570-RPM range
from master-test01 is unaffected by this finding.

## 6. Coolant-temperature hypothesis

**Update (2026-08-20): a much stronger candidate found.** Gary reported,
watching a live replay, that this candidate's instability wasn't just
"unexplained drift" as previously documented -- it visibly drops well
below 152°F near the end of the test, when real coolant should be holding
steady there. Checked directly against the raw log: the guessed value
holds a real 150-152°F plateau from t~480s through t~1000s, then
declines substantially and unevenly for the rest of the file --
20s-window means fall to 127-141°F by t=1040-1080s, dip as low as
~104-119°F in several later windows, with only partial, temporary
recoveries. This is a real decline in the raw data (confirmed directly,
not a display/rolling-mean artifact), not something the field sheet can
explain either way (its last coolant reading is 159°F at 22:58, right
around when this decline starts) -- but nothing about the test (RPM stays
active through a whole second RPM run afterward) gives a physical reason
for coolant to actually drop that much. That prompted the same
ground-truth correlation search that found the better Oil Pressure
candidate, applied to coolant instead:

**CAN ID**: `1A0`
**Bytes**: record `07`, byte 1.
**Observed behavior**: an extraordinarily clean, almost noise-free curve.
Flat at raw 35 through the entire engine-off period (t=0-66s), then a
slow, smooth, nearly monotonic climb (35 -> 68) over the next ~420
seconds -- nothing like the original candidate's immediate, jagged jump.
Reaches a rock-solid plateau at raw 68 right around t=480s and holds it
(67-68, essentially zero jitter) for the next ~500 seconds. Ticks up one
more small step to raw 71 right around t=1010s. **Unlike the original
candidate, it then stays in this same warm 66-71 band for the entire rest
of the file** -- through the trim test and the whole second, independent
RPM test, all the way to the very end (t=1300s: raw 69-70) -- never
collapsing back toward its cold/key-on value.
**Evidence FOR**: matches the field sheet at every anchor -- flat 35 at
95°F (engine off), climbing through 38 at 102°F (22:43) and 65 at 141°F
(22:47), reaching a flat plateau at 68 that holds through 154°F (22:49)
and the entire idle/RPM-step-test window (22:49-22:54), then a small step
up to 71 matching 159°F (22:58). Far less noisy at every single anchor
than the original candidate ever manages. Most importantly, it directly
answers Gary's report: it does NOT drop near the end of the test, staying
in a physically sensible warm band for the rest of the file where the
original candidate collapses.
**Evidence AGAINST**: the anchor-to-anchor scale isn't perfectly linear
(1.4-4.3 °F per raw count across different segments) -- plausibly within
the field sheet's own approximate, minute-resolution readings, but not
independently confirmed to be a clean physical scale. No live-observed
real-world reading exists to confirm the post-22:58 plateau specifically
(the field sheet has no coolant entries after 159°F) -- the claim that it
*should* stay warm is a physical inference (the engine keeps running,
including through a full second RPM test), not a logged fact.
**Confidence: moderate-to-good** -- see `candidates.py`'s `Guess.note` for
the exact numbers.
**Best experiment to distinguish it further**: a longer single-condition
capture (steady idle held for several minutes, well past this test's
duration) would show directly whether real coolant genuinely stays flat
that long, giving a cleaner late-session ground truth than this test's
sheet (which stops recording coolant after the RPM step test).

### Original leading candidate (superseded above, kept for the record)

**CAN ID**: `170`
**Bytes**: record `03`, bytes 0-1 (LE).
**Observed behavior**: flat at `5,126` for t=0-64s (key-ON, engine OFF),
then rises to `42,683`(t=120) -> `46,034`(t=360) -> `56,830`(t=480) ->
`57,423`(t=540) -> `57,642`(t=600) -> `53,085`(t=1020), then becomes
noisier in the back half of the session (t=956s onward), repeatedly
dropping to the 8,500-20,000 range, including a rapid two-state toggle
(`11781`/`5381`) in the file's very last second.
**Physical observation**: real coolant (field sheet) is 95(22:41) ->
102(22:43) -> 141(22:47) -> 154(22:49) -> 154(22:50) -> 152(22:51) ->
159(22:58) -- a sharp early rise (+62% over ~10 minutes) then a plateau
around 150-160°F.
**Evidence FOR**: the candidate's shape matches closely -- a sharp early
rise (+1009% on its own arbitrary units) followed by a plateau starting
at almost exactly the same real-world checkpoint (t~480-600s in both
series), a genuinely good match in both timing and shape, independent of
the two series being on different scales; flat at engine-off, as
expected.
**Evidence AGAINST**: the real gauge ticks *up* slightly (152->159)
between 22:51 and 22:58 while the candidate *drops* (57,642->53,085) over
the same span; the back-half instability (t=956s onward) has no ground
truth to check it against (the field sheet's last coolant entry is
22:58, before this begins) and does not fit a simple monotonic-warm-up-
then-plateau model.
**Confidence: moderate-to-good** for the early rise and plateau timing
(now corroborated against real gauge data); unresolved for the
late-session behavior. **Update (2026-08-20)**: Gary confirmed live that
this late-session issue is real and worse than documented -- superseded
as the leading candidate by `1A0` record `07` byte 1 above, which does
not show this collapse.
**Competing hypothesis**: none strong -- the early-rise/plateau shape and
timing match is distinctive enough that this is this report's most
confidently-supported hypothesis (see section 15), though the late-session
instability is not yet explained by anything.
**Best experiment to distinguish it**: a capture with ground truth
extending past ~22:58-equivalent, and ideally through a confirmed
"Engine STOPPED", to check whether the late-session drops are real
thermostat cycling or something else. Also useful: briefly disconnecting
the coolant-temperature sender's electrical connector at a steady idle
(section 17) -- real coolant temperature is unaffected, so whichever byte
snaps to a fixed value at that moment is very likely this signal. Keep it
brief; an ECM reading "no signal" as a fault could trigger an overheat
warning.

## 7. Oil-pressure hypothesis

**Update (2026-08-20): a much stronger candidate found.** Gary asked
directly whether a better oil-pressure candidate exists, given the
leading candidate below kept failing every check. That prompted a
systematic search: build a real, densely-anchored "expected oil PSI over
time" reference curve from the field sheet (flat ~49.7 PSI through the
whole idle stretch, rising through the confirmed 900/1380/2570 RPM
plateaus to 65.9 PSI, back to 46.7 PSI at post-ramp idle), then correlate
every byte in the entire capture against it. The top result by raw
correlation (`1A0` record `05` byte 2) turned out to be a false lead --
it's the high byte of the already-confirmed Raw Water Pressure word
(section 8), and its step-to-step increments *decelerate* (18, 14, 12)
while real oil pressure's increments *accelerate* slightly (+3.6, +3.0,
+9.6) -- opposite shapes, so naive correlation was just picking up
"everything rises with RPM in this one test," not a genuine oil match.
The next distinct candidate held up under that same shape check:

**CAN ID**: `170`
**Bytes**: record `00`, byte 3 (a different byte in the same record as
the original candidate below).
**Observed behavior**: an inverse relationship -- raw value *falls* as
real oil pressure rises, and does so cleanly:

| Condition | Real oil (PSI) | Raw (byte 3) | Distinct values in window |
|---|---|---|---|
| Engine off (t=0-66) | 0.5 | ~39 (31-39) | 7 |
| Idle running (t=100-660) | ~49.7 (flat) | ~21 (20-22) | 3 |
| 900 RPM plateau | 53.3 | ~15 (13-19) | 7 |
| 1380 RPM plateau | 56.3 | ~12 (12-13) | 2 |
| 2570 RPM plateau | 65.9 | **11 (constant)** | **1** |
| Post-ramp idle (t=960-1158) | 46.7 | ~21 (20-22) | 3 |

Every plateau here is far cleaner (fewer distinct values, tighter range)
than the original candidate ever manages at any point in the file, and
the 2570 RPM plateau -- where real oil pressure peaks -- is perfectly flat
at raw 11, the single cleanest reading found for *any* candidate in this
section.
**Cross-validated against a second, independent RPM test**: the capture's
final segment (t~1158-1312s, the field sheet's 23:01-23:03 series:
550/990/1400/2000/2500 RPM, no oil PSI logged for this run) shows the
exact same behavior with no fitting involved -- raw falls smoothly as RPM
climbs, bottoms out at the identical raw value (11) at this run's RPM
peak (matching the first test's confirmed 2570 RPM plateau), then returns
to the identical idle baseline (~20-21) once RPM drops back. A real
sender should behave identically across two independent runs of the same
engine; this one does.
**Evidence FOR**: monotonic and inverse at every single anchor point,
including the two hardest tests any candidate in this report has faced --
staying essentially flat during idle despite small real RPM changes
(540-590 RPM), and correctly bottoming out at the true real-world PSI
peak (2570 RPM) with zero noise. Reproduces identically in a second,
independent RPM test never used to build the fit.
**Evidence AGAINST**: the relationship isn't a single straight line -- the
engine-off point implies a PSI/raw-count ratio roughly 3-5x steeper than
the running-regime points do, so this needed an `InterpolatedGuess`, not
a plain `Guess`. That's not unusual for a real sender curve (many
pressure-sender output curves are non-linear, especially near zero), but
it isn't independently confirmed to be that vs. two different underlying
regimes glued together. The specific PSI value implied for any raw
reading between 900 and 1380 RPM (raw 12-15) is interpolated, not
independently anchored.
**Confidence: moderate-to-good** -- see `candidates.py`'s `Guess.note` for
the exact numbers. Comparable in strength to the RPM and Water Pressure
candidates' 2026-08-20 upgrades.
**Best experiment to distinguish it further**: the same sender-disconnect
test proposed for the original candidate below (section 17) would work
here too and is still the sharpest single confirmation available --
briefly disconnect the oil-pressure sender at steady idle and see which
byte snaps to a fixed fault/out-of-range value at the exact disconnect
moment.

### Original leading candidate (superseded above, kept for the record)

**CAN ID**: `170`
**Bytes**: record `00`, byte 1 (and the wider bytes 0-1 LE pairing).
**Observed behavior**: flat at exactly 0 through t=66.7s (key-ON, engine
OFF), then at t=66.84s starts climbing and immediately becomes jagged and
noisy (116, 121, ..., 234, then 82, 155, 103, 143, 171, 80, 239, ...) --
no clean trend, before settling to a noisy oscillation (~50-90) by
t=85-100s. Declines steadily during the extended idle stretch:
~84(t=120) -> ~59(t=360) -> ~48(t=480) -> ~38(t=540) -> ~38(t=600), then
rises again (noisy, up to the 100-220 area) during the RPM-step-shaped
excursion around t~760-850s. Uses the full 0-255 byte range (256 distinct
values across the session).
**Physical observation**: real oil pressure (field sheet) is 0.5 PSI at
key-on, then **remarkably flat, 49.2-50.3 PSI, across the entire
extended-idle stretch** (22:43-22:51), rising to 53.3->56.3->61.6->65.9
PSI during the 22:54 RPM step (+24%), then 46.7 PSI back at idle (22:58).
Per Gary, the RPM steps themselves were not held steady (throttle
repeatedly overshot and corrected -- section 4), so oil pressure being
RPM-driven, these four logged PSI values are approximate snapshots of a
fluctuating condition, not readings from a held plateau -- the true
in-between range was likely wider and bumpier than +24% implies.
**Evidence FOR**: flat at exactly 0 at key-on, matching the real gauge's
near-zero key-on reading; immediate jagged onset at the moment the engine
catches, matching the same rough-transient signature as the RPM
candidate; rises noisily during the RPM-step-shaped excursion, and that
noisiness is now better explained than before -- a real oil-pressure
sender responding to a manually overshot-and-corrected throttle should
look exactly this jagged, not like a clean staircase (section 5);
continuous, high-resolution-looking trace (full byte range used), not a
status flag.
**Evidence AGAINST**: the real gauge holds essentially flat (49.2-50.3
PSI, +/-1 PSI noise) across the same eight-minute idle stretch where this
candidate **declines by ~55%** (84->38) -- a direct, material
contradiction, not a minor discrepancy. A real oil-pressure sender
holding steady for eight minutes should not produce a byte that halves
over the same window.
**Update (2026-08-20, live replay validation)**: two more real anchor
points make this candidate's standing considerably worse, not better.
Gary confirmed the settled 2570 RPM plateau (t~925-953s, the highest
real oil-pressure reading on the whole field sheet: 65.9 PSI) -- at that
exact point, this candidate's raw value (~35.6) is essentially identical
to, if anything slightly *below*, its own raw value at idle (~37.8),
where real oil pressure is only ~50 PSI. **This candidate fails to rise
at all across the full confirmed RPM range** (idle through 2570 RPM),
directly contradicting the single most basic expectation of an oil
pressure signal. Separately, a systematic row-by-row comparison against
every field-sheet reading (not just the anchor points) found this
candidate *overshooting* real oil pressure by ~40% at the 900/1380 RPM
points (guess ~75/~67 PSI vs. real 53.3/56.3 PSI) while simultaneously
undershooting badly at idle (as already documented above) -- there is no
consistent relationship to real oil pressure anywhere in this dataset,
only noise that happens to correlate loosely with engine-catch timing.
**`services/replay`'s candidate tier for this byte was downgraded from
"hypothesis" to "raw" on 2026-08-20** as a direct result -- see
`candidates.py`'s `Guess.note` for the exact numbers.
**Further live confirmation (2026-08-20)**: Gary reported the gauge
reading ~21 PSI at 39.3% into a replay (t~515.6s, 22:49:36 under this
report's time alignment). The field sheet's nearest entry, 22:49, gives a
real, steady 49.2 PSI at 560 RPM -- roughly idle, nothing dynamic
happening. Checked directly against the raw log: this candidate's 20s
window ending at that moment averages 38.1 raw (22.8 PSI under its own
guess, matching what Gary saw), but the *raw* values inside that single
20-second window swing wildly between 11 and 59 (6.6-35.3 PSI) -- large,
fast noise during a period the real gauge should be flat. This is the
same failure mode already documented above (steady-idle contradiction),
now confirmed a second time at a completely different point in the
timeline than the original idle-window finding.
**Confidence: weak**, downgraded further from "moderate". Something real
still happens at key-on/engine-catch timing (that part is unaffected by
this update), but the steady-idle contradiction plus the complete failure
to track RPM across two independently-confirmed step points make this
look decreasingly like oil pressure the more it's tested. The Phase 2
tool still scores it 80% (section 4) purely on RPM-rank correlation
across the five old discrete logs; it structurally cannot see any of
this, since none of it came from that engine. **Update (2026-08-20)**:
superseded as the leading oil-pressure candidate by `170` record `00`
byte 3 above -- a different byte in the same record that tracks real oil
pressure cleanly and inversely, including through a second independent
RPM test this candidate was never tested against this thoroughly.
**Competing hypothesis**: a related-but-different quantity (e.g. oil
pressure convolved with a slow warm-up-coupled term), or something that
only coincidentally moves with RPM/engine-catch events without actually
being oil pressure -- now the more likely reading, given it doesn't
track real oil pressure at any tested RPM.
**Best experiment to distinguish it**: at a brief, steady idle,
**disconnect the oil-pressure sending unit's electrical connector for
~10-15 seconds** (real oil pressure is unaffected -- only the sensor
signal is interrupted), with the disconnect/reconnect moments noted to
the second, then reconnect. Whichever CAN byte snaps to a fixed
fault/out-of-range value at that exact moment and ignores RPM until
reconnection is almost certainly the true oil-pressure field; any
candidate that keeps behaving normally through the disconnect can be
ruled out. This is sharper than logging a gauge at several points because
it breaks the RPM correlation for *only* the true oil-pressure signal,
leaving RPM and every other candidate unaffected -- see the caution about
possible low-oil-pressure alarms/rev-limiting in section 17.

## 8. Raw-water-pressure hypothesis

**CAN ID**: `1A0`
**Bytes**: record `05`, bytes 1-2 (LE) (byte 2 alone also scores).
**Observed behavior**: pegged at exactly `256` for t=0-66s (key-ON,
engine OFF), then begins a rise at **t=68.426s** -- a clean, smooth,
strictly monotonic staircase with no backtracking or oscillation
(`2048 -> 11776 -> 23040 -> 28928 -> 31744 -> 32768 -> 33280 -> 33536 ->
33792 -> 34048`), reaching a stable plateau (~34,300) by t=81s, a
~13-second ramp -- starting ~1.6-2s *after* the RPM/oil-pressure
candidates begin moving, and without their rough, oscillating onset. Only
58 distinct values across the whole 21.9-minute session (coarse
quantization). Stays flat (~33,900-34,500, +1.7% spread) through the
extended idle stretch, then rises to ~36,600-42,200 (+15%) during the
RPM-step-shaped excursion around t~760-850s.
**Physical observation**: real water pressure (field sheet) is 0 PSI at
key-on, 0.6-1.0 PSI through the idle stretch (flat in absolute terms),
then 1.7->2.8->3.6->4.1 PSI during the 22:54 RPM step -- a **+486%**
rise, the largest relative swing of any ground-truth signal in this test.
As with oil pressure (section 7), these four step-test readings are
approximate snapshots taken while the throttle was being manually
overshot and corrected, not held-plateau values (section 4) -- water
pressure, being directly impeller/pump driven, likely tracked those RPM
swings quickly and visibly, not just the four logged numbers.
**Evidence FOR**: onset character *at the initial engine catch*
(t=66-90s, a one-time transient, separate from the RPM-step test) is
exactly what a downstream hydraulic quantity should look like -- smooth,
delayed, monotonic, low-pass-filtered relative to the engine's actual
rough catch, versus the immediate jagged onset of the RPM/oil-pressure
candidates (section 5); qualitatively near-zero-but-not-quite at idle and
rising with engine speed, matching the real gauge's own
near-zero-but-not-quite idle reading; coarse 58-value quantization is
consistent with a lower-resolution pressure sensor channel rather than a
fine RPM count.
**Evidence AGAINST**: the real gauge's **+486%** rise during the RPM step
is far larger than this candidate's observed **+15%** rise in the
corresponding window. Beyond the raw gain shortfall, **this candidate's
smoothness during the RPM-step window itself is now a harder problem for
this hypothesis, not a point in its favor**: if the throttle was being
overshot and corrected by hand (section 4), a real water-pressure sender
-- responding quickly to a bouncing RPM -- should plausibly show some of
that same bumpiness during that specific window, the way the oil-pressure
and RPM candidates do (section 5, 7). This candidate stays comparatively
smooth there instead. (The separate, one-time engine-catch transient
above is a different event and isn't undermined by this -- a single
clean catch-to-idle ramp doesn't imply anything about behavior during a
later, differently-shaped RPM-step maneuver.) Alternatively, its encoding
could simply compress the reportable range heavily, or the true
water-pressure byte is a different, not-yet-identified field, or the
approximate time alignment (section 4) is misplacing the comparison
window -- this report cannot distinguish between these explanations.
**Update (2026-08-20, live replay validation) -- upgraded back to
moderate-to-good.** The +15%/+486% gain mismatch above was measured
against a crude 2-point linear fit; once real anchor points across the
*full* RPM range were available, the picture changed substantially. Gary
confirmed three more real readings during the settled portions of the
first RPM-step test: 900 RPM -> 1.7 PSI, 1380 RPM -> 2.8 PSI, 2570 RPM ->
4.1 PSI (plus the already-known 0 PSI at key-on and ~0.75 PSI at idle).
Fitting this candidate's raw value against those 5 points (not a single
line -- the slope itself accelerates with RPM: 0.000022 -> 0.00020 ->
0.00032 -> 0.00043 PSI/count) shows a curve consistent with a
**centrifugal impeller pump, where output pressure scales roughly with
the square of speed** -- exactly the physical mechanism a raw-water pickup
driven directly off the engine should follow, and exactly the kind of
curve a flat linear guess could never have captured.
**That fit was then cross-validated against a second, independent RPM
step test later in the same capture** (Gary: idle/990/1400/2000/2500 RPM,
~23:01-23:03) that this candidate's fit had never seen. Applying the
first test's curve to the second test's actual measured RPM predicted
this candidate's readings to within 1-11% at all four checked points
(RPM 999/1352/1570/2492 -> predicted 1.93/2.74/3.01/4.02 PSI vs. actual
1.72/2.51/3.01/3.94 PSI; the 1570 RPM point matched almost exactly). A
curve fit from one trial correctly predicting an independent second
trial is meaningfully stronger evidence than either trial alone --
coincidental noise doesn't reproducibly extrapolate like that.
**A specific alternative was also directly ruled out**: Gary asked
whether this candidate might be fuel consumption rate (GPH) instead,
since that also rises with RPM. The field sheet's real GPH during the
second test (0.7/1.1/1.5/1.7/1.9/0.8) is both the wrong absolute scale
and the wrong shape compared to this candidate's actual readings, while
the RPM-pressure curve matched well -- ruled out.
**Confidence: moderate-to-good**, upgraded from "weak". `services/replay`'s
candidate tier was moved back from "raw" to "hypothesis" on 2026-08-20 as
a direct result -- see `candidates.py`'s `Guess.note` for the full
numbers. The remaining concerns below are unaffected by this and still
stand.
**Competing hypothesis**: RPM itself (the original ambiguity -- see
section 5) is weaker now that this candidate's gain profile has been
shown to follow a physically-coherent, cross-validated pressure curve
rather than RPM's own (differently-shaped, still poorly-fit) response.
Oil pressure is no longer a strong competing read either -- section 7's
2026-08-20 update found that candidate fails to track real oil pressure
at all across the same RPM range this candidate tracks well.
**Best experiment to distinguish it**: a capture where boat speed and
engine RPM diverge (underway, not a flush/dockside test) so a true
impeller/water-pump signal and a true crank-speed signal can mechanically
decouple -- on this test rig the two are locked 1:1, which is the root
cause of the remaining ambiguity. More immediately actionable: **the same
sender-disconnect technique proposed for oil pressure (section 7)** --
briefly unplugging the raw-water-pressure sending unit's connector at a
steady idle (real water pressure is unaffected; only the sensor signal
is interrupted) and noting the disconnect/reconnect times to the second.
If this candidate is truly raw water pressure, it should snap to a fixed
fault value at the moment of disconnect and ignore RPM until reconnected
-- the same way the oil-pressure test in section 7 would confirm or rule
out that byte. Doing both sender disconnects (oil, then water) in one
short, otherwise-steady idle capture could resolve sections 7 and 8
together without needing to solve the throttle-control problem at all.
Also useful, if available: an RPM step test with a real, continuous
tachometer log (not hand-read snapshots) held genuinely steady at each
target (a governor/cruise-control-style throttle, or a much more careful
manual hold), so the true in-between RPM/oil/water waveform is known and
this candidate's shape can be checked against it directly rather than
inferred.

**Derived (2026-08-21): using this candidate as an RPM proxy on
drive03.log.** Since real RPM and real water PSI were both logged at the
exact same moments during the RPM step test above, this candidate's raw
value can be mapped directly to RPM instead of PSI using those same
anchors -- Gary's own proposed technique, motivated by the RPM candidate
(section 5) apparently breaking down on `drive03.log`. Applied to that
capture, this proxy tells a much more plausible story: two clear
excursions (raw climbing to ~47872 and ~47104, implying ~3540-3940 and
~2841-3241 RPM) separated by a long, stable low-speed plateau
(raw~31232-34048, implying ~516-563 RPM) -- close to Gary's own account
of "varied several times, peak ~3700, a lot of 550-1000 time moving
slowly." Implemented as "Water-Pressure RPM Proxy candidate" in
`candidates.py` (same raw byte and `CandidateKey` as this candidate,
just a second `Guess`). This is explicitly doubly speculative: it
extrapolates both the RPM-to-PSI relationship (confirmed only to 2570
RPM) and this candidate's own already-extrapolated raw range (drive03
reaches raw~48896, past even this candidate's last confirmed anchor of
45385) on a capture that may not even be the same boat/engine as
master-test01 -- not a confirmed reading, but a substantially better fit
to the described drive than the direct RPM candidate manages on the same
file.

## 9. Fuel hypothesis

**CAN ID**: `170`
**Bytes**: record `00` byte 2; record `01` bytes 1-2 (LE); record `02`
bytes 0-1 (LE) -- three near-constant candidates, all on the same CAN ID.
**Observed behavior**: all three stay essentially flat for the entire
21.9-minute session -- record `00` byte 2 takes only 2 distinct values
(`4`, `5`) across 13,455 samples; record `01` bytes 1-2 (LE) stays within
a `29,440`-`29,695` band (248 distinct values, but a span of only 255 out
of 65,535 possible, <0.4%); record `02` bytes 0-1 (LE) takes only 3
distinct values, `0`-`4,864`.
**Physical observation**: real fuel level (field sheet) is **100%**,
constant, for the entire test.
**Evidence FOR**: near-constant behavior over 21.9 minutes is consistent
with a genuinely unchanging fuel level (no burn large enough to move a
sender meaningfully in this time).
**Evidence AGAINST**: none of the three candidates sit anywhere near
their own maximum representable value -- record `00` byte 2 is at 4-5 out
of 255 (~1.6%), record `01` bytes 1-2 is at ~29,545 out of 65,535 (~45%),
record `02` bytes 0-1 is at ~2,193 out of 65,535 (~3.3%). If fuel really
was ~100% and one of these encoded it as a simple 0-to-max percentage, it
should read at or near its own ceiling -- none of them do. This is a mild
strike against the simplest version of this hypothesis for all three
(though a fuel sender's raw output rarely maps linearly onto a byte's
full range, so it isn't disqualifying).
**Confidence: weak.** Structurally plausible, near-constant as expected,
but the "should be near-max at 100% fuel" check fails for all three
candidates.
**Competing hypothesis**: depth (section 10) -- structurally
indistinguishable from fuel with this dataset, since neither varied
independently during this test. See section 10 for the argument that the
same CAN ID could plausibly carry both.
**Best experiment to distinguish it**: compare two captures at
meaningfully different fuel levels (e.g. before/after a long run, or
deliberately at a lower tank level) -- a real fuel signal should shift
noticeably; a reserved/padding or depth-only byte won't. A faster,
single-session alternative: briefly disconnect the fuel-level sender's
electrical connector (section 17) -- lower risk than the oil/water/
coolant senders, since a disconnected fuel sender has no engine-safety
implication, and whichever byte snaps to a fixed empty/full/fault value
is very likely this signal (and, by elimination, rules that byte out as
depth -- section 10).

## 10. Depth hypothesis

**CAN ID**: `170`
**Bytes**: record `00` byte 2; record `01` bytes 1-2 (LE); record `02`
bytes 0-1 (LE) -- the same three candidates as section 9.
**Observed behavior**: identical to section 9 -- all three near-constant
across the full session.
**Physical observation**: real depth (field sheet) is 8.9ft at key-on,
noted to fluctuate between "8.9 and ~9.1ft" over the course of the test
(a real but very small absolute range).
**Evidence FOR**: near-constant behavior with only small fluctuations
matches a stationary/dockside test's depth reading closely -- more
naturally than it matches a *literal* percentage-of-max reading, since
this report has no independent knowledge of the depth sender's true
scale (unlike fuel, where a 100%-full tank gives a specific value to
check against, and none of these three candidates were near it -- section
9). Depth's own small real fluctuation (8.9->~9.1ft) has no obvious
byte-max analog to fail, so this candidate set isn't disqualified by the
same test that weakened it for fuel.
**Evidence AGAINST**: exactly the same structural problem as fuel --
nothing in this capture varies depth independently (a stationary or
slow-drifting dockside test won't move a depth sender by more than noise),
so this remains indistinguishable from fuel or from a generic
reserved/near-constant byte.
**Confidence: weak**, on par with fuel.
**Competing hypothesis**: fuel (section 9) -- fully indistinguishable
with this dataset.
**On whether the same CAN ID could carry both**: yes, plausibly. All
three candidates live on `170`, which already carries the (candidate)
oil-pressure, RPM, and coolant fields in other records of the same
fragmented message. There's no structural reason fuel and depth couldn't
each occupy one of these three (or another near-constant) slots within
the same logical packet, the same way this one ID already appears to
carry several unrelated engine signals.
**Best experiment to distinguish it**: compare two captures at genuinely
different water depths (e.g. different dock/anchorage) -- a real depth
signal shifts; a fuel-only or reserved byte won't. A faster,
single-session alternative (section 17): briefly disconnect the depth
transducer's electrical connector. Depth is confirmed to be on this CAN
bus -- it's one of the fields the SmartCraft tach gauge itself displays
-- so this candidate should respond the same way the oil/water/coolant
senders do: real depth is unaffected, and whichever byte snaps to a
fixed fault value is very likely this signal, which by elimination also
helps settle fuel (section 9).

## 11. Battery-voltage hypothesis

**CAN ID**: `00000B41`
**Bytes**: leading-byte-grouped candidates around record `81`/`83` (see
the small-sample caveat in section 4) -- e.g. record `81` byte 0, bytes
0-1 (BE), bytes 1-2 (LE).
**Observed behavior**: this ID's steady-state traffic (from t=5.1s
onward) alternates between two 3-byte payloads (`83 07 17` / `83 04 FF`)
on a slow ~15s cadence (section 3); the leading byte's occasional
excursion to `0x81` during the t=0.1-5.1s startup handshake burst is what
produces the specific "record 81" candidates the regenerated Phase 2
report surfaces.
**Physical observation**: real battery voltage (field sheet) is 13.4V at
key-on, rising to 13.8-13.9V during the extended idle, and settling at a
constant 14.0V from the first RPM step test onward through the rest of
the sheet. The sheet also notes **"Shore power on during this test"** --
meaning the boat's charger, not (only) the alternator, was likely
supplying/regulating this voltage, so the classic key-on (~12.5V) ->
alternator-charging (~13.8-14.2V) step this hypothesis was originally
framed around may not cleanly apply to this specific test at all.
**Evidence FOR**: small real fluctuation (13.4->13.8->14.0V, a modest,
monotonic-ish rise) without tracking RPM -- consistent with a regulated
rail; the Phase 2 tool's automated score rose from 45% to 55% specifically
because this capture shows small real movement rather than "literally
zero fluctuation" (section 4).
**Evidence AGAINST**: the record-`81` grouping this evidence is attached
to comes from only a handful of samples in the brief startup burst
(section 4's small-sample caveat), not the thousands of samples backing
the oil-pressure or coolant candidates; and because shore power was
active, this test cannot cleanly exercise the real alternator-driven
voltage step the hypothesis is meant to detect -- a flat-ish 13.4->14.0V
rise here is at least as consistent with a shore-power charger's own
regulation curve as with engine-driven charging. **New, live-validated
finding (2026-08-20)**: replaying this capture through the dashboard
(`services/replay`), Gary watched the record-`83` steady-state field
(the one actually shown continuously, section 3's alternating `83 07 17`
/ `83 04 FF` pattern) square-wave cleanly between two fixed values
(guessed ~10.2V / ~13.8V under a linear fit) on a strict ~15-18s cadence
for the full session -- with shore power connected throughout, per the
field sheet. A shore-powered battery should read stable, not toggle on a
fixed clock like that. This is fairly strong evidence that record `83`'s
field is not a continuously-sampled battery voltage at all, more likely
two different pieces of status/diagnostic data alternating in the same
byte slot as part of the periodic broadcast (see the request/response
framing already suspected for `00000B41`/`0000410B` in section 3).
**Confidence: weak**, and now more firmly so. Directionally plausible at
the level of "which record", but the specific continuously-displayed
field (record `83`) has direct, dated evidence against it behaving like
voltage at all, on top of the original small-sample caveat for record
`81` and the shore-power confound.
**Competing hypothesis**: none specific -- the main risk here is simply
that "shore power on" makes this test unable to distinguish a real
battery-voltage signal from charger-regulation noise, whatever byte
carries it.
**Best experiment to distinguish it**: repeat a capture spanning key-ON
through cranking and into stable idle **with shore power disconnected**,
so the expected ~12.5V (resting battery) -> ~13.8-14.2V (alternator
charging, engine load) step is actually exercised and not masked by a
charger. Note: the sender-disconnect technique proposed elsewhere in this
report (sections 6, 7, 8, 9, 12, 17) doesn't apply here -- battery
voltage has no separate sending unit to unplug; it's read directly off
the electrical system, so the shore-power test above is the closest
equivalent single-variable manipulation available.

## 12. Trim hypothesis

**Update (2026-08-20): a much stronger candidate found.** Gary corrected
this report's assumed trim window -- trim moved *only* starting ~22:59,
then ran through 3 full up/down cycles in one continuous sequence (not
spread across the whole 22:59-23:00 minute as originally assumed from the
sheet's minute-resolution timestamps). That correction motivated a fresh,
systematic search: rank every byte in the entire capture (all IDs, all
records, all offsets) by how concentrated its value transitions are
inside a window around the corrected trim time, versus how quiet it is
everywhere else in the file. One byte stood out sharply above everything
else found, including the original leading candidate below:

**CAN ID**: `170`
**Bytes**: record `03`, byte 2 (a single byte immediately adjacent to the
coolant temperature word, section 6's bytes 0-1 of the same record).
**Observed behavior**: this byte reads exactly `0` for the *entire*
21.9-minute file except for one contiguous span, t=1033.3-1110.1s
(22:58:13-22:59:30 under this report's time alignment -- straddling the
field sheet's "22:59" mark, well within the +/-30-60s alignment tolerance
section 4 already establishes). Within that span, and nowhere else in the
file, it produces **exactly 6 pulses**, each ~8.0-8.6 seconds long,
separated by 2.9-7.75s gaps back at 0, cleanly alternating between raw
value `1` and raw value `2`:

```
pulse   start (s)   end (s)   duration   raw value(s)
1       1033.263    1041.903   8.64 s    1 (mixed briefly with 2 -- see below)
2       1049.648    1058.287   8.64 s    2
3       1062.160    1070.303   8.14 s    1
4       1077.452    1085.595   8.14 s    2
5       1091.156    1099.199   8.04 s    1
6       1102.079    1110.122   8.04 s    2
```

**Evidence FOR**: this is an exact match, in both count and order, to the
field sheet's documented "3 full up/down cycles (6 movements: Up, Down,
Up, Down, Up, Down)" starting from the trim-down position: 6 discrete
events, alternating cleanly between two states, occurring exactly once in
the whole 22-minute file, at a time consistent (within already-established
tolerance) with the corrected trim window. The ~8-second pulse duration is
physically plausible for a single end-to-end (or near-end-to-end) trim ram
stroke. The base rate for this shape appearing by chance -- 6 pulses,
2-valued, strictly alternating, isolated to one ~77s span out of 1312s, and
nowhere else in the file -- is very low; this is now the strongest, most
specific piece of evidence found for any candidate in this section. The
first pulse briefly mixes values 1 and 2 (see raw trace in the report's
working notes) before settling into a clean 1/2/1/2/1/2 alternation for
pulses 2-6 -- plausibly some initial switch bounce on the very first
movement, or the true state during the transition instant, not something
that undermines the rest of the pattern.
**Evidence AGAINST**: this byte only ever takes 3 distinct values (0, 1,
2) -- it is a discrete status flag, not a continuous position sender
(confirmed directly, 2026-08-20: during each ~8s pulse the raw value
holds flat rather than stepping through intermediates -- see the
"searched and not found" note below), so it cannot answer "what trim
angle" the way a real position candidate would; it only answers "was trim
being commanded, and in roughly which of two states." Which raw value
corresponds to physically "Up" vs "Down" is inferred purely from matching
the sheet's stated order (1=first movement=Up, 2=second=Down, ...), not
independently confirmed -- an isolated single-direction trim test (see
section 17) would confirm or refute this assignment directly.
**Gary's own interpretation (2026-08-20)**, having operated the trim
switch himself during this test: this is most likely a **trim Up/Down
button indicator** -- reflecting the operator's switch position -- rather
than raw motor-movement telemetry. That's physically consistent with the
~8s pulse length (a plausible duration to hold a trim button per stroke)
and is treated as the leading interpretation here, though the specific
switch-position-vs-motor-movement distinction hasn't been independently
tested.
**Confidence: moderate-to-good** for "this byte reflects the trim
Up/Down control being engaged," clearly stronger than the original
candidate below; still unconfirmed for the specific 1=Up/2=Down
assignment. Not one of the formal Phase 2 tool's 6 named hypotheses (trim
was never one), so carries an unscored (-1) confidence in replay rather
than a percentage -- see `docs/replay.md`.
**Best experiment to distinguish it further**: an isolated single-movement
trim test (just one Up, or just one Down, at a known clock time, engine
otherwise idle) would confirm both the direction assignment and rule out
any remaining chance that this byte's alternation is coincidental rather
than direction-encoding.

**Searched and not found (2026-08-20): a continuous trim position
signal.** Gary confirmed the direction candidate fires at the right time,
but expected a real position sender to look different -- a gradual,
multi-step stream (e.g. 0/10, 1/10, 2/10... as the ram physically travels
from full down to full up), not a byte that snaps straight between two
states. That's a fair expectation, and checking it directly against the
raw data confirms the byte above does NOT do this -- during each ~8s
pulse it holds flat at a single raw value (1 or 2) the whole time, never
stepping through intermediates, reinforcing that it's a discrete
direction/active flag rather than a position sender. A systematic search
for a genuine multi-step candidate (any byte taking many distinct values
specifically inside the confirmed t=1033-1110s window, while staying
comparatively quiet outside it) turned up one superficially promising
lead, `1FFD4041` byte 2, but it didn't hold up: checked in detail, it's
just cycling through the same small set of values (`0`/`60`/`127`/`232`/
`255`) it also cycles through everywhere else in the file, in a
repeating multiplexed rotation unrelated to trim timing -- the same kind
of false lead the oil-pressure search hit before finding its real
candidate (section 7), except this one didn't pan out. **No continuous
trim position candidate was found in this capture.** This bus may only
expose trim as a discrete motor-run/direction status here, or a position
sender exists but wasn't distinguishable from noise/multiplexing using
this method -- an isolated single-movement test (the same experiment
proposed above) would show a real position sender much more clearly,
embedded in far less competing signal traffic than this capture has.

**Searched and not found (2026-08-20): an independent min/max limit
switch.** Gary asked whether trim likely has a min/max end-of-travel
indicator -- a reasonable question, since many real trim systems report
limit-switch state rather than (or alongside) continuous position, and a
clean limit signal would also let the duration-based position estimate
below be calibrated/validated against real endpoint timing instead of
just the pulse-duration assumption. Searched systematically: looked for
any byte that reads one consistent value while trim is known to be
resting at full-down (the whole pre-test idle period, plus the dwell
after each Down-ending pulse) and a *different* consistent value while
resting at full-up (the dwell after each Up-ending pulse). No clean
candidate was found -- the one byte that showed any separation (`170`
record `03` byte 0) is almost certainly just contamination from the
original coolant candidate's own low byte (the same word, changing for
unrelated reasons during that period), not a real trim signal. **No
min/max limit-switch candidate was found in this capture.**

**Derived estimate (2026-08-20): dead-reckoned position from pulse
duration.** Gary's own proposed technique, following naturally from the
~8s full-stroke observation above: if a full stroke takes ~8.3s, then N
seconds of a commanded Up/Down pulse should move trim roughly N/8.3 of
the way across its range (e.g. "2 up clicks at 1s each" =~ 24%). This
isn't a new CAN candidate -- there's no byte to read -- so it's
implemented as a genuinely *computed* signal: `services/replay/app/
derived.py`'s `TrimPositionEstimator` integrates the Trim Direction
candidate's raw value over elapsed capture time, frame by frame, moving
100%/8.275s while a direction is commanded (8.275s = the mean of the 6
measured pulse durations, 8.04-8.64s) and clamping at 0/100. It starts at
0% (full down), matching the field sheet's key-on trim position, and is
published on the dashboard as "Trim Estimated Position (DERIVED)".
**This is explicitly an illustrative estimate, not a decode or even a
CAN-derived hypothesis** -- it inherits every caveat of the pulse-based
full-stroke assumption above, and has never been checked against a real
intermediate trim-position reading (this capture's field sheet only
documents the full-down/full-up endpoints). The min/max limit-switch
search above was specifically an attempt to find independent evidence to
validate this assumption against, and came up empty -- so this estimate
remains uncalibrated beyond the pulse-duration reasoning itself. Treated
as `hypothesis` tier but unscored (-1) in replay, the same convention
used for every new structural/derived finding that isn't one of the
formal tool's 6 named hypotheses.

### Original leading candidate (superseded above, kept for the record)

**CAN ID**: `1A0`
**Bytes**: record `0B`, bytes 0, 3, and 6 (low-cardinality, correlated
burst timing).
**Observed behavior**: a scan for low-cardinality, step-and-hold bytes on
`170`/`1A0` found `1A0` record `0B` byte 3 taking values
`{0, 239, 240, 241, 242, 243, 244}` with 29 transitions clustered into
short bursts (a handful of transitions within a few seconds) at multiple
distinct points across the session -- roughly t=55-57s, 317-323s,
423-425s, 524-529s, 697-699s, 826-828s, and 1066-1073s/1131-1136s. Bytes
0 and 6 of the same record show a subset of these same clusters (fewer,
binary/3-valued transitions at t=55-57s, 423-425s, 826-828s,
1066-1073s/1131-1136s). **Refined via live replay (2026-08-20, Gary
watching `services/replay`'s dashboard)**: three of these clusters
(t=423.9-424.6s, t=826.0-826.8s, t=1070.3-1071.1s) turn out to be a very
specific, identical shape -- the raw byte drops to *exactly* 0 for 4
consecutive samples (~0.7s), from its otherwise rock-steady ~239-244
baseline, then snaps straight back. Not a gradual change or noise -- a
clean, brief, repeatable dropout. The three occurrences aren't evenly
spaced (402s and 244s apart), so not an obvious fixed-interval heartbeat
either.
**Physical observation**: the field sheet, confirmed directly by Gary,
shows trim starting fully down (position 0) at key-on (22:41), then --
during 22:59-23:00 -- cycled through **three full up/down cycles (6
movements: Up, Down, Up, Down, Up, Down)** from that starting position;
the sheet's own first "Down" entry at 22:59 restates the already-current
position rather than logging a new move. That 6-movement window maps to
approximately `t~1080-1140s` under this report's time alignment (section
4).
**Evidence FOR**: two of this candidate's seven observed burst clusters
(t=1066-1073s and t=1131-1136s) fall right at the edge of / inside that
approximate `t~1080-1140s` trim window -- a real, if not exact, timing
match given only minute-resolution hand timestamps. The burst shape
itself (several rapid transitions within a few seconds, then quiet) is
consistent with a relay/pulse-counter response to a handful of quick trim
button taps, and the order of magnitude is right: three full up/down
cycles is 6 discrete relay actuations, and each of the two matching
clusters shows several rapid transitions, not just one.
**Evidence AGAINST**: this candidate has *five more* burst clusters
(t=55-57s, 317-323s, 423-425s, 524-529s, 697-699s) at times with no
documented trim activity at all (they fall inside the extended-idle
stretch, 22:43-22:51-ish, well before any trim event on the sheet). Those
clusters are entirely unexplained -- either trim was informally exercised
without being logged, or this byte responds to something else that just
happens to burst periodically (a status ping, a diagnostic poll), and the
two clusters that do land near the documented trim window are
coincidental. The two matching clusters are also ~65 seconds apart, while
the field sheet describes all 6 movements happening within one
continuous ~1-minute window -- that gap doesn't obviously match "six
movements done in quick succession," so even the two "matching" clusters
don't cleanly resolve into a single coherent trim-test signature the way
the RPM candidates cleanly resolved into a single sharp engine-start
transition (section 5). The refined t=423.9-424.6s/826.0-826.8s bursts
confirmed live are both well outside the documented trim window and share
an identical, clean "drop to exactly 0 for ~0.7s" shape -- more consistent
with a brief status/fault flag or a periodic self-check pulse than with a
human pressing a trim button at an arbitrary, unlogged moment.
**Confidence: very weak / exploratory.** A real lead worth checking, not
evidence. Not scored by the formal Phase 2 engine (trim remains "not yet
testable" there -- section 4). **Update (2026-08-20)**: now superseded by
the much stronger `170` record `03` byte 2 candidate above -- with a
clean, exactly-6-pulse, correctly-ordered alternating signal now
identified and isolated to a single ~77s span in the whole file, this
candidate's five unexplained clusters look even more clearly like
coincidental noise (an unrelated periodic status/diagnostic byte) rather
than a partial or fragmented view of the same trim event.
**Competing hypothesis**: an unrelated periodic status/diagnostic message
on the same record that happens to correlate with the trim window by
chance, given five of its seven total clusters fall outside any
documented trim activity.
**Best experiment to distinguish it**: an isolated trim-cycle capture,
otherwise steady (engine at idle, nothing else changing), with each
individual Down/Up movement's clock time noted by hand -- so this
candidate's cluster timing can be checked against real trim events one
at a time instead of against a single ~1-minute window covering 6 moves
at once. A complementary, lower-effort test (section 17): briefly
disconnect the trim ram's position-feedback sender (a separate,
purely-electrical sensor, distinct from actually moving the trim) at a
fixed trim position -- this tests the candidate's *identity* without
needing to cycle trim at all, the same way the sender-disconnect tests
work for oil/water pressure and coolant.

## 13. Tach / network participant analysis

**Frame-rate/dropout check**: across the entire 21.9-minute capture, no
CAN ID shows any gap larger than its own normal periodic cadence -- `170`
never gaps more than 0.09s, `1A0` more than 0.25s, `1FFD4041` more than
0.30s, and the ~15s-cadence `00000B41`/`0000410B` pair never gaps more
than ~15.05s (i.e. never misses a single expected cycle). **There is no
detectable interruption anywhere in this file on any ID.**

**Correction (this section originally misstated the tach's connection
state and has been corrected)**: the tachometer **was physically
connected for the entire `master-test01` capture** -- confirmed directly
by Gary, who ran the test. What the recovered field sheet (section 4)
actually shows is that no "Tach Experiment" rows were filled in, meaning
the *deliberate connect -> disconnect -> reconnect A/B toggle* described
in the blank protocol template was not performed during this run. That is
a distinct fact from the tach's connection state, and an earlier draft of
this report conflated the two -- "the toggle experiment wasn't run" does
**not** mean "the tach was disconnected." With the tach connected
throughout and no toggle performed, the absence of any traffic
disruption in this file (below) is exactly what would be expected either
way, and this capture on its own still can't test whether toggling the
tach *would* disrupt traffic -- see the ranked explanations and the "Best
next experiment" below.

**"The tach" is a multi-parameter SmartCraft gauge, not a single-purpose
RPM display**: per Gary, it also shows depth alongside other parameters
(section 10). That matters for interpreting a future tach-disconnect
experiment (section 17) -- if disconnecting it changes bus traffic, that
result would reflect the loss of a display/consumer node that touches
several of this report's signals (RPM, depth, and whatever else it
shows), not necessarily something specific to RPM. Whether the gauge only
*displays* values sourced from other senders/the ECM, or itself
originates and broadcasts any of them (e.g. if it has its own depth
transducer input), is not something this report can determine from the
data alone -- that distinction should be checked against the gauge's own
documentation or wiring before drawing conclusions from the A/B test's
results.

**What this capture *can* say about "richer traffic now vs. stuck traffic
before"**: the previously-documented earlier session (`key-cycle.log`,
`rpm-steps.log`, `trim-cycles.log`, `smartcrafttest.log`) is no longer
present on disk to re-examine directly -- those four files were never
committed to the repo and are gone from the machine they were captured
on, so this comparison relies on the description already recorded in
`docs/ReverseEngineering.md`/`docs/HypothesisReport.md`: each of those
four files was a single CAN frame (record `00` of ID `170`) retransmitted
100,000+ times with no other content, "consistent with a Listen-Only
capture against a bus with no other node available to ACK it."

**The capture-history correlation, stated plainly**: the earlier, unusable
session was captured with the tach **disconnected**; `master-test01` (this
healthy capture) was captured with the tach **connected**. That is a real,
useful correlation and this report treats it as exactly that -- a
correlation worth testing directly -- **not** as proof that the tach's
presence causes the difference. Two captures, each with a different
confound (see below), is not enough to establish causation. Given the
documented old-session symptom, ranked explanations for why this capture
looks so different:

1. **(Most consistent with the documented symptom) No other node was
   ACKing the bus in the old captures, and the CAN protocol itself causes
   this exact failure mode**: a transmitting node whose frame never gets
   ACKed (no receiver pulls the ACK slot dominant) will retry the *same*
   frame indefinitely, which is precisely "single frame retransmitted
   100,000+ times." A pure Listen-Only sniffer never ACKs by design, so if
   the tach (or any other real bus node) was disconnected and nothing else
   was listening, the transmitting ECU could plausibly get stuck retrying
   forever. This is a coherent, protocol-level mechanism, not just a
   correlation -- and it's the one this task's framing points at
   (tach disconnected -> old captures; tach connected -> this one). This
   report cannot independently verify it against raw data anymore (the old
   files are gone), so it remains the leading *documented* explanation
   rather than one newly confirmed here.
2. **The engine may simply not have been running in the old captures.**
   If the ECU itself wasn't producing real telemetry (key-off, or
   engine-off with only static/idle-state broadcasts), a single repeated
   frame is exactly what a healthy-but-idle bus would also produce,
   independent of the tach. This capture's clean key-on -> crank -> idle
   transition (section 5) shows what a genuinely running engine's traffic
   looks like, and it's categorically richer -- but that richness could be
   "the engine was actually running" rather than "the tach was connected."
3. **Different capture setup (wiring, termination, bus segment, interface
   config)** between the two sessions cannot be ruled out either, and
   would be indistinguishable from (1) or (2) using only the data
   available now.

This report cannot rank these three definitively -- the raw evidence
needed to (the old logs' actual frame arbitration/error behavior) no
longer exists on disk, and the tach-connected/tach-disconnected
correlation currently rests on exactly two captures that also differ in
every other way (different sessions, ~18 hours apart, engine state
unknown for the old one, different capture setup) -- nowhere near enough
to call it causal. **This makes a controlled tach-connected vs.
tach-disconnected A/B comparison the single highest-value next
experiment** (see section 17): repeat the connect/disconnect/reconnect
step as its own short, dedicated capture (engine running, otherwise
steady idle, only the tach's connector toggled, both states logged to the
second), so the specific effect (if any) on `00000B41`/`0000410B`/
`1FFD4041` traffic can finally be isolated from every other variable that
currently confounds the two-capture comparison above.

## 14. Comparison with previous captures

| | Five short sample logs (`idle`/`1000rpm`/`1650rpm`/`1900rpm`/`idle2`) | `master-test01` |
|---|---|---|
| Total duration | ~8.4 minutes across 5 separate files | 21.9 minutes, one continuous file |
| Capture structure | Five independent steady-state snapshots | One continuous session incl. key-on, crank, idle, RPM steps, trim cycles |
| CAN IDs seen | `170`, `1A0`, `1E0`, `1F0`, `00000B41`, `0000410B` | Same six, plus `1FFD4041`, `0E3790F3`, and 3 singleton IDs |
| `00000B41`/`0000410B` structure | Appeared as fixed-length, constant/near-constant atomic messages | Revealed to be a multi-shape handshake + steady periodic pair (section 3) |
| Key-on/engine-off phase captured? | No | Yes (first ~66s) |
| Warm-up window captured? | No | Yes, up to the last logged RPM point (~22:58/23:03-equivalent) |
| Ground-truth gauge log available? | No | Yes -- field sheet, section 4 |
| Stuck/retry traffic | None | None |

The now-unrecoverable earlier session (`key-cycle.log` etc.) is described
only qualitatively above (section 13) since the raw files no longer exist
on disk to re-run through this repo's tools.

**What actually changed between the five short logs and this capture**:
mainly *scope*, not *quality* -- the five short logs were already clean,
real telemetry (per the existing Data Quality note in
`docs/HypothesisReport.md`), just narrow in time and missing any
transient/startup/warm-up window. This capture doesn't contradict that
data; it extends it, and in doing so exposes structure (the `00000B41`/
`0000410B` handshake, the coolant candidate's real warm-up trend, the
oil-pressure candidate's real-gauge contradiction, the RPM/water-pressure
ambiguity's sharper but still-unresolved shape) that a handful of
90-second steady-state snapshots never could.

## 15. Current confidence table

| Signal | Leading candidate | This report | Phase 2 tool (post-update) |
|---|---|---|---|
| Coolant Temperature | `1A0` rec `07` byte 1 (new leading candidate, 2026-08-20) | **Moderate-to-good** -- near-noise-free warm-up curve matching every field-sheet anchor, and (unlike the original candidate) stays in a physically sensible warm band through the entire rest of the file instead of collapsing | not one of the tool's byte positions tested (65%, this report's own score) |
| Coolant Temperature (original candidate) | `170` rec `03` bytes 0-1 (LE) | **Moderate-to-good**, superseded above -- real early-rise/plateau shape and timing match the field sheet, but drops well below 152°F near the end of the test (confirmed live, 2026-08-20), which real coolant does not do | 55% |
| Oil Pressure | `170` rec `00` byte 3 (new leading candidate, 2026-08-20) | **Moderate-to-good** -- inversely tracks real oil PSI at every idle/900/1380/2570 anchor, cleaner (fewer distinct values) than any prior candidate, cross-validated against a second independent RPM test at the end of the file (identical raw minimum at RPM peak, identical baseline on return to idle) | not one of the tool's byte positions tested (60%, this report's own score) |
| Oil Pressure (original candidate) | `170` rec `00` byte 1 / bytes 0-1 (LE) | **Weak**, superseded above -- contradicts the field sheet's flat-idle reading AND fails to rise at all at a confirmed 2570 RPM / 65.9 PSI peak; no consistent relationship to real oil pressure found anywhere. Replay tier moved hypothesis->raw | 80% (tool doesn't see any of this) |
| RPM | `170` rec `01` bytes 4-5 (BE) | **Moderate-to-good below ~2570 RPM** (2026-08-20); **weak above it** (downgraded 2026-08-21) -- confirmed idle-through-2570-RPM shape/anchors hold up, but never implies more than ~890 RPM anywhere in a second capture (drive03.log) Gary describes reaching ~3700 RPM -- extrapolation past the confirmed range appears unreliable | 65% (top candidate) |
| Raw Water Pressure | `1A0` rec `05` bytes 1-2 (LE) | **Moderate-to-good** (upgraded, 2026-08-20) -- a 5-point piecewise fit (physically consistent with a centrifugal-pump pressure curve) was cross-validated against an independent second RPM test to within 1-11%; fuel-consumption-rate was proposed as an alternative and directly ruled out. Replay tier moved raw->hypothesis. Same byte reused as an RPM proxy (2026-08-21, section 8) -- fits drive03.log's described RPM shape much better than the RPM candidate itself does on that file, though doubly extrapolated and unconfirmed | 65% (RPM top-3) / 60% (RWP top-3, tool score unchanged -- doesn't see any of this either) |
| Fuel | `170` rec `00` byte 2, rec `01` bytes 1-2, rec `02` bytes 0-1 | **Weak** -- near-constant as expected, but none read near their own max despite fuel actually being ~100% | 40% each |
| Depth | Same three as Fuel | **Weak**, indistinguishable from Fuel | 40% each |
| Battery Voltage | `00000B41` rec `81`/`83` area | **Weak** -- small-sample caveat, shore power confounds the expected alternator step, and live replay validation (2026-08-20) caught record `83` cleanly square-waving between two fixed values on a strict clock, which a shore-powered battery shouldn't do (section 11) | 55% |
| Trim Direction (likely Up/Down button indicator, per Gary) | `170` rec `03` byte 2 (new leading candidate, 2026-08-20) | **Moderate-to-good** -- exactly 6 alternating pulses, matching the field sheet's 6-movement count and Up/Down/Up/Down/Up/Down order exactly, isolated to one ~77s span with zero occurrences anywhere else in the 22-minute file; discrete flag, not a continuous position (confirmed) | not one of the 6 named hypotheses (unscored) |
| Trim (original candidate) | `1A0` rec `0B` bytes 0, 3, 6 | **Very weak / exploratory**, superseded above -- 2 of 7 burst clusters land near the documented trim window, 5 don't | not yet testable (unscored) |
| Engine/mode status flag | `1A0` rec `00` bytes 1-2 (not one of the named hypotheses) | Steps at the same 5 timestamps as the RPM/pressure segment boundaries -- a corroborating structural signal, not a physical-value candidate | n/a |
| Engine Hours/Minutes | `1A0` rec `02` byte 3 (new, 2026-08-20, not one of the named hypotheses) | **Strong structural evidence** -- wall-clock-paced counter (59.576s mean interval, stdev 0.006s across 21 ticks), categorically unlike every frame-driven counter elsewhere in this capture | not yet run through the formal 6-hypothesis tool (unscored) |

## 16. Remaining unknowns

- No independent, second-by-second gauge/tachometer log exists -- the
  field sheet gives real values but at minute resolution with
  "approximate" timestamps, so exact numeric correlation at the level of
  a single RPM step is not reliable (section 4). Compounding this: the
  RPM steps themselves were not held steady (the throttle was manually
  overshot and corrected -- section 4), so even the logged step values are
  approximate snapshots of a moving target, not clean plateau readings --
  the true instantaneous RPM/oil/water waveform during the step test is
  unknown, only inferred.
- RPM and raw water pressure remain mechanically coupled 1:1 on this test
  rig (no independent boat-speed variation), so a boat-speed-diverging
  capture (section 8's "best experiment") still hasn't happened -- though
  the 2026-08-20 cross-validation between two independent RPM step tests
  is a real, different kind of evidence than response character/magnitude
  alone, and now favors treating this candidate as water pressure over
  RPM.
- The original oil-pressure candidate's steady-idle decline directly
  contradicts the field sheet's flat real reading over the same window,
  and fails to rise at all across the full confirmed RPM range up to a
  real 65.9 PSI peak (section 7) -- neither is explained; this candidate
  is looking less and less like oil pressure the more it's tested. A much
  stronger replacement candidate (`170` rec `00` byte 3) was found on
  2026-08-20 and is now the leading oil-pressure candidate -- see section
  7. It still isn't fully confirmed: the non-linear engine-off-to-idle
  jump implies either a genuinely non-linear sender curve or two
  different regimes glued together, and the sender-disconnect experiment
  (section 17) hasn't been run against it yet.
- The original coolant candidate's late-session instability is
  unexplained, and confirmed to start earlier than previously thought:
  even during the RPM-step window (t~925-953s), the same real 152°F
  reading corresponded to a raw value ~24% different from the one seen
  for that same 152°F reading at t=600s (section 6) -- there is real,
  unexplained drift in this candidate between its two fitted anchors, not
  just after them. A much stronger replacement candidate (`1A0` rec `07`
  byte 1) was found on 2026-08-20 and is now the leading coolant
  candidate -- see section 6. It isn't fully confirmed either: no
  field-sheet reading exists past 22:58 to verify its claimed post-test
  warm plateau, and its scale isn't perfectly linear across all segments.
- No continuous trim position signal was found in this capture, despite a
  systematic search prompted by Gary's expectation of a gradual
  multi-step data stream during each trim movement (section 12,
  2026-08-20) -- the trim direction candidate holds flat during each
  pulse rather than ramping, and the one superficially promising
  alternative found turned out to be an unrelated multiplexed rotation.
  No independent min/max limit-switch signal was found either (section
  12, 2026-08-20), so the derived, dead-reckoned position estimate built
  from pulse duration (also section 12) has no independent evidence to
  validate its full-stroke-duration assumption against -- it rests only
  on the pulse-duration reasoning itself.
- The trim direction candidate (`170` rec `03` byte 2, 2026-08-20) is
  strong on timing/count/order but still doesn't confirm which raw value
  (1 or 2) is physically Up vs Down -- that assignment is inferred from
  matching the sheet's stated order, not independently tested (section
  12). The original, much weaker trim candidate (`1A0` rec `0B` bytes 0,
  3, 6) is still not confirmed either -- 5 of its 7 burst clusters fall at
  times with no documented trim activity, now looking more clearly like
  unrelated noise given the stronger candidate found above.
- The tach was connected throughout `master-test01`, but the deliberate
  connect/disconnect/reconnect A/B toggle was not performed during this
  specific test (confirmed by the field sheet); the "is the tach an
  active network participant" question is still open (section 13).
- `00000B41`/`0000410B`'s true framing convention (address-claim /
  request-response handshake) is inferred from timing and shape, not
  confirmed against any protocol spec.
- Battery voltage cannot be cleanly tested in this capture because shore
  power was active throughout (section 11).
- Whether the earlier, ~18-hour-prior "stuck" session (tach disconnected)
  vs. `master-test01` (tach connected) was really caused by the tach's
  connection state, rather than the other confounds between those two
  sessions (engine-off vs. running, capture-rig differences), cannot be
  re-tested now that the old session's raw files no longer exist on disk
  (section 13). This is a real, noted correlation, not a demonstrated
  cause -- see section 17.
- Speed, fault/overheat codes, and a second (oil) temperature signal were
  all searched for on 2026-08-20 in response to Gary's question and none
  were found in this capture (section 3) -- speed because 292 byte
  positions are equally-plausible frozen-zero candidates with the pitot
  unhooked, fault codes because the only known status bytes only reflect
  the RPM-regime transitions already documented and no overheat condition
  is indicated as occurring during this specific test, and oil temperature
  because no second monotonic warm-up-shaped byte exists in the
  less-examined IDs. These are honest negative results, not exhaustively
  proven absences -- a differently-designed capture (pitot connected;
  underway; or one taken during an actual overheat event) could still
  surface any of the three.

## 17. Best next experiment

The field sheet template has been updated with a dedicated
"Sender-Disconnect Experiment" section covering experiment B below --
see
[docs/SmartCraft-Controlled-Capture-Data-Sheet.md](SmartCraft-Controlled-Capture-Data-Sheet.md).

Two experiments now share top priority, since they answer different
questions and neither depends on the other:

**A. A short, isolated, controlled tach-connected vs. tach-disconnected
comparison**, engine running and otherwise held steady at idle, with the
data sheet's "Tach Experiment" section actually filled in
(disconnect/reconnect timestamps noted by the clock, ideally to the
second). The capture history so far shows a real correlation -- the
earlier unusable session had the tach disconnected, `master-test01` had
it connected and was healthy -- but with only two captures that also
differ in every other way, that correlation is not evidence of causation
on its own (section 13). A capture that toggles *only* the tach's
connection, with everything else held constant, is what would finally let
this question be tested cleanly.

**B. A sender-disconnect sweep** (sections 6, 7, 8, 9, 10, 12): at a
steady idle, briefly unplug each accessible sending unit's electrical
connector one at a time -- oil pressure, raw water pressure, coolant
temperature, fuel level, depth, and trim position are all separate,
discrete senders that this technique should work on -- ~10-15 seconds
each, with a short settled pause between senders so the traces don't
overlap, each disconnect/reconnect timestamped to the second. Real
oil/water pressure, coolant temperature, fuel level, depth, and trim
position are all unaffected by unplugging their sender (only the signal
is interrupted), so whichever CAN byte snaps to a fixed fault/
out-of-range value at each specific disconnect -- and ignores everything
else until reconnection -- is very likely that physical signal. This is a
much sharper, single-variable identity test than correlating against
RPM, and it doesn't depend on ever getting a clean, steady RPM hold.
Done as one sweep, it could resolve most of this report's remaining open
candidate identities (sections 6, 7, 8, 9, 10, 12) in a single short
session.

**Depth is confirmed to be on this CAN bus** (corrected from an earlier
draft of this report, which treated that as uncertain): per Gary, depth
is one of the fields the SmartCraft tach gauge itself displays, alongside
other parameters -- since the gauge only shows values it receives over
SmartCraft, depth must already be broadcast on this bus, not sourced from
a separate, unrelated NMEA device. This also means "the tach" in
experiment A above is a multi-parameter display, not a single-purpose
RPM gauge -- worth keeping in mind when interpreting that test's results
(section 13): if disconnecting it changes bus behavior, that could
reflect the loss of a display/consumer node that touches several of this
report's signals, not something specific to RPM.

**This does not generalize to every signal**, and accessibility should be
checked case by case:
- **RPM** can't be tested this way -- it comes from the crank/cam
  position sensor(s), which the ECM needs for ignition/injection timing.
  Disconnecting that on a running engine risks a stall or bad misfire,
  not a clean test.
- **Battery voltage** has no separate sender to unplug -- it's a direct
  electrical measurement. The shore-power-disconnect experiment below
  is the closer equivalent for that signal.
- **Oil pressure specifically** carries an extra caution: the ECM may
  read "no signal" as critically low pressure and trigger an alarm or,
  on some SmartCraft-integrated ECMs, a protective rev-limit/
  reduced-power response. Keep every disconnect brief, at idle only,
  never at elevated RPM, with someone ready to reconnect immediately.

Both A and B can plausibly be combined into one otherwise-steady-idle
session if convenient. Close behind, roughly in priority order:

1. **A capture with shore power disconnected**, so the battery-voltage
   hypothesis (section 11) can actually be tested against the real
   key-on -> alternator-charging step instead of a shore-charger-confounded
   reading.
2. **An isolated trim-cycle capture** with each individual Down/Up
   movement's clock time noted by hand, to test the `1A0` record `0B`
   lead against real events one at a time instead of a single multi-move
   window.
3. **A capture with second-resolution (not minute-resolution) ground
   truth** during the RPM-step portion specifically, ideally each target
   RPM actually held steady rather than approached by overshoot and
   correction (a governor, cruise-control-style throttle, or a much more
   careful manual hold), so the still-unresolved RPM/oil-pressure/
   water-pressure three-way gain comparison (sections 5, 7, 8) can be
   checked against a known, clean waveform instead of an approximate,
   possibly-bumpy snapshot.
