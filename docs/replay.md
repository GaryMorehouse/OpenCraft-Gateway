# Replaying a captured SmartCraft log through the dashboard

`services/replay` feeds a real, already-captured CAN log (`candump -L`
format, e.g. `master-test01.log`) through the **same** telemetry pipeline
the simulator/future gateway publisher uses -- InfluxDB -> Grafana -- so a
real capture can be watched moving through the dashboard for human
validation, without deciding in advance whether any given CAN field is
"really" RPM, oil pressure, etc.

**This is not a decoder.** It republishes exactly the candidate
byte/word values already scored by `tools/smartcraft_toolkit`'s Phase 2
hypothesis engine and documented in
[`docs/master-test01-analysis.md`](master-test01-analysis.md) -- nothing
here invents a new CAN meaning, and the raw value stored for every
candidate is never unit-converted, because none of those candidates have
a confirmed scale factor, only an identified byte location.

A separate, explicitly-labeled **guess** layer sits on top of that raw
value for the gauge panels (added at Gary's request, after a first pass
showing only raw numbers turned out to be hard to eyeball for
plausibility) -- see "Guessed calibration (gauges)" below. It's kept
completely apart from the raw value and from anything
`docs/master-test01-analysis.md` treats as evidence.

## Why a separate path from the simulator's data

The simulator publishes *calibrated* Signal K measurements --
`propulsion.<instance>.temperature` in Kelvin, `.oilPressure` in Pascal,
`.revolutions` in Hz -- and the Engine Overview / Helm Mode dashboards
apply unit-conversion math on top of those exact fields (Kelvin -> °F,
Pascal -> PSI, Hz -> RPM). Writing an unconfirmed, uncalibrated CAN byte
into one of those fields would make Grafana apply that conversion math to
a meaningless number and *display it as if it were a real, calibrated
reading* -- exactly what this project's task instructions say not to do.

So replay writes to two new, clearly separate InfluxDB measurements
instead, and a new "REPLAY MODE" section was added to the existing
**Diagnostics** dashboard (`grafana/dashboards/diagnostics.json`) to show
them -- that dashboard already had "ECU Status" / "Gateway Status"
placeholder panels literally captioned "Not yet available... once
SmartCraft CAN decoding is implemented," which is exactly what this is a
first, provisional step toward. No new dashboard was created, and no
existing panel (Engine Overview, Helm Mode, Fuel, Performance) was
touched.

## Data path

```
tools/samples/logs/master-test01.txt         (raw candump -L capture, read-only)
        |
        v
smartcraft_toolkit.parser.parse_file          (existing Phase 1 code -- reused, not duplicated)
        |
        v
services/replay/app/reader.py                 matches frames against candidates.py's
                                                published byte/word locations, reads them
                                                with smartcraft_toolkit.signals.read_value
        |
        v
services/replay/app/main.py                   paces playback by the frames' own timestamps
                                                (scaled by --speed), handles pause/restart/stop
        |
        v
services/replay/app/publisher.py               writes to InfluxDB:
                                                   can_replay      (tags: capture, hypothesis, tier, unit;
                                                                    fields: value, confidence_pct,
                                                                    guess_value if candidates.py defines one)
                                                   replay_status   (tags: capture;
                                                                    fields: state, position_s,
                                                                    duration_s, pct_complete, speed)
        |
        v
grafana/dashboards/diagnostics.json            "REPLAY MODE" banner, "Replay Status" table,
                                                "Candidate Signals (Replay)" table (raw values),
                                                10 "(GUESS)" gauge panels (guess_value, per-candidate units)
```

## `candidates.py`: what gets shown, and how

`services/replay/app/candidates.py` is a small, explicitly-cited table --
each entry names a CAN ID/record/byte-offset/width/endianness (a
`CandidateKey`, the exact type `smartcraft_toolkit` itself uses for
candidate generation) plus a `tier` and the section of
`docs/master-test01-analysis.md` that scored it:

- **`"hypothesis"`** -- the analysis report calls this candidate at least
  *moderate* confidence. Shown labeled with its hypothesis name and
  confidence percentage, but still explicitly as an unconfirmed
  candidate.
- **`"raw"`** -- the report calls it *weak*, or it isn't scored by the
  formal engine at all (e.g. Trim). Shown as a plain raw CAN field, not
  tied to a named physical signal, per the instruction that an
  insufficiently-supported candidate should show its raw value rather
  than an invented one.

Both tiers publish the exact same kind of number -- the raw integer
`smartcraft_toolkit.signals.read_value` reads from that byte/word, never
converted to any physical unit. The only difference is the label and the
`confidence_pct` tag Grafana displays alongside it.

**A third case**: a candidate can also be `"hypothesis"` tier with
`confidence_pct == -1` -- reserved for a new structural finding that isn't
one of the formal Phase 2 tool's 6 named hypotheses at all (so it was
never run through that tool's scorer), as opposed to having been run
through it and scored below 50%. Engine Hours/Minutes (added 2026-08-20,
`1A0` record `02` byte 3 -- a wall-clock-paced counter, see
`docs/master-test01-analysis.md` section 3) is the first candidate in this
category. `-1` is otherwise reserved for exactly this "unscored, not
scored-and-weak" case and the test suite enforces that it's never used to
sneak a low-confidence named hypothesis into `hypothesis` tier.

**To replay a different capture**: that capture likely has its own set of
candidate byte locations (a different ECU, a different capture session,
etc. isn't guaranteed to share master-test01's exact layout). Add a new
list to `candidates.py` (or a new module) with that capture's own
evidence-scored candidates, cited the same way, rather than editing the
`MASTER_TEST01_CANDIDATES` entries in place. Everything else in this
pipeline -- `reader.py`, `pacing.py`, `main.py`, `publisher.py`, the
Grafana panels -- is capture-agnostic and needs no changes.

## Guessed calibration (gauges)

A raw integer (`4714`, `44549`, ...) is hard to eyeball for plausibility.
Each `ReplayCandidate` in `candidates.py` can carry an optional `Guess`
(`scale`, `offset`, `unit`, and a `basis`):

- **`FITTED`** -- scale/offset solved from >=1 real field-sheet reading
  cited in `docs/master-test01-analysis.md` (e.g. RPM: raw~4270-4590 during
  the field sheet's real 540-590 RPM idle window). Still not a confirmed
  decode -- just an estimate anchored to one real data point (or two, for
  candidates with an early and a later reading to fit a line through), on
  a candidate this report itself may already flag as a poor fit at other
  points (e.g. RPM's compressed dynamic range at higher speeds).
- **`UNANCHORED`** -- a placeholder assumption with nothing behind it at
  all (typically "this byte's/word's full numeric range = 0-100%" or a
  plausible-looking min/max), for a candidate with no real reading to fit
  against yet. None of `candidates.py`'s current entries are `UNANCHORED`
  any more (see below) -- it's kept as a category for whatever gets added
  next without a ground-truth reading behind it yet.

Fuel, Depth, Battery Voltage, and Trim started out `UNANCHORED` and got
refitted to `FITTED` on 2026-08-19 using Gary's live observation, watching
a real-time replay: 25% into the file (t~328s), he reported Fuel~100%,
Depth~9.1ft, Battery~13.8V, Trim~0%. That's the same kind of anchor as a
field-sheet reading -- a real value observed at a known moment -- just
captured live during replay instead of written down beforehand.
`candidates.py`'s `Guess.note` for each cites this explicitly, including
where a fit still doesn't fully hold up (e.g. Battery Voltage's *other*
raw state maps to ~10.2V under the same fit, which a real battery
shouldn't do while running -- still evidence against a clean, continuous
voltage signal, even with one state now reading correctly). Oil Pressure
and Coolant Temperature were also confirmed plausible but visibly noisy
frame-to-frame -- both gauge panels were changed to a rolling mean instead
of the latest single sample (Coolant: 10s; Oil Pressure: 20s, widened
further after it was still fluctuating at 10s).

**RPM needed a different fix.** Gary watched two more real points during
the first RPM-step test (2026-08-19): raw~5960 at a real 900 RPM, raw~6730
at a real 1380 RPM. Combined with the idle anchor, that's 3 confirmed
points, and they're not collinear -- the slope roughly triples from the
idle segment to the 900-1380 segment. A single `Guess` scale/offset can't
represent that honestly (fitting the upper two points alone put idle at a
nonsensical *negative* RPM). `candidates.py` adds an `InterpolatedGuess`
for exactly this case: a tuple of confirmed `(raw, real_value)` points,
linearly interpolated between neighbors and linearly extrapolated beyond
the endpoints using the nearest segment's slope. RPM is the only
candidate using it so far -- everything else still fits a single line
well enough. Extrapolated territory (past the last confirmed anchor,
raw>6730 for RPM) is explicitly the shakiest part of any `InterpolatedGuess`
and is called out as such in its `note`.

`publisher.py` computes `guess.apply(raw_value)` and writes it as a
*separate* `guess_value` field (never overwriting `value`, the raw
number), tagged with the guess's `unit` -- `apply()` works the same way
for both `Guess` and `InterpolatedGuess`, so nothing downstream needed to
change. Ten gauge panels in `diagnostics.json` (titled `"<Name>
(GUESS)"`) read `guess_value`, styled like Engine Overview's real gauges
but in a single neutral blue rather than green/amber/red -- that
traffic-light palette implies validated alarm severity these guesses
haven't earned, so it's deliberately not reused here.

**Engine Hours/Minutes** (added 2026-08-20) uses a plain `Guess`
(`scale=1.0, offset=-23.0, unit="min"`), not an `InterpolatedGuess` -- a
single linear count doesn't need piecewise fitting. Its anchor isn't a
real-world reading like the others; it's structural (raw 23 = the first
observed value = t~3s into the capture), so the gauge reads "minutes
elapsed since this capture started," not any claimed absolute engine-hours
value.

**Trim Direction** (added 2026-08-20, `170` record `03` byte 2) uses an
`InterpolatedGuess` with exact-integer anchors `(0,0), (1,1), (2,-1)` --
not because the underlying relationship is a continuous curve (raw only
ever takes these 3 values), but because it's the simplest existing
mechanism for a non-linear raw-to-display mapping (a plain `Guess` can't
send raw 1 up and raw 2 down). This candidate replaces Trim as the
leading trim-related finding: a systematic search across every byte in
the capture, prompted by Gary correcting the trim timing to "moved only
starting ~22:59, then 3 full cycles in a row," found this byte idle at 0
everywhere in the file except for exactly 6 pulses in one ~77s window,
alternating cleanly between two raw values in an order matching the field
sheet's Up/Down/Up/Down/Up/Down sequence exactly. See
`docs/master-test01-analysis.md` section 12 for the full pulse-by-pulse
breakdown. The original "Trim (GUESS)" position gauge (`1A0` record `0B`
byte 3) is kept as a separate, still-weak candidate -- it estimates a
continuous 0-100% position, which this new candidate cannot do (it's a
discrete direction/activity flag, not a position sender).

**A guess reading "wrong" is itself useful evidence, not a failure.** An
`UNANCHORED` (or a poorly-`FITTED`) guess reading implausibly isn't this
replay tool malfunctioning -- it's the underlying raw candidate byte (or
the specific scale/offset guessed for it) failing the same plausibility
check a human glancing at the gauge would apply. That's exactly the
"human validation" this whole mechanism exists for -- as demonstrated by
Gary's 2026-08-19 pass, which is what fixed 4 of these 8 gauges.

## Running it

### 1. Start InfluxDB and Grafana

```sh
docker compose --profile dev up -d influxdb grafana
```

(You don't need to start the `simulator` service for this -- replay
writes to different measurements and doesn't depend on it. It's fine if
it's also running; it won't collide.)

Open Grafana at <http://localhost:3000> (or whatever `GRAFANA_PORT` is
set to in `.env`) and go to **OpenCraft Gateway -> Diagnostics**. The new
"⚠ REPLAY MODE" section is empty until replay starts publishing.

### 2. Run the replay tool

From the repo root, with Python 3.12+ and `services/replay/requirements.txt`
installed (`pip install -r services/replay/requirements.txt`):

```sh
cd services/replay
INFLUXDB_ORG=opencraft INFLUXDB_BUCKET=telemetry INFLUXDB_TOKEN=<your .env token> \
  python -m app.main --speed 1
```

`INFLUXDB_URL` defaults to `http://localhost:8086`, matching the port
`docker-compose.yml` publishes to the host -- override it if you changed
`INFLUXDB_PORT`. The three `INFLUXDB_*` values must match your `.env`
file (`INFLUXDB_INIT_ORG`, `INFLUXDB_INIT_BUCKET`,
`INFLUXDB_INIT_ADMIN_TOKEN` there -- same values, different variable
names, matching the simulator's own convention).

With no `--log`, it replays `tools/samples/logs/master-test01.txt` by
default. To replay a different capture: `--log path/to/other.txt`.

**Alternative: Docker.** `docker compose run --rm replay --speed 1` builds
and runs the same tool in a container (build context is the repo root, so
the image also bundles `tools/smartcraft_toolkit` and `tools/samples` --
see `services/replay/Dockerfile`). Use `run`, not `up`, since this is a
one-off interactive tool, not a background service, and it isn't in any
compose profile for that reason. `stdin_open`/`tty` are set so the p/r/q
controls below work the same as running it locally.

### 3. Speed and controls

```sh
python -m app.main --speed 1     # real time (default)
python -m app.main --speed 5     # 5x real time
python -m app.main --speed 10    # 10x real time
python -m app.main --speed max   # as fast as possible, no pacing delay
```

Speed only affects the *pacing* between frames (computed from the
capture's own timestamps, scaled by the speed multiplier -- see
`app/pacing.py`); the values published are identical at every speed.

While it's running, type a command and press Enter in that terminal:

| Command | Effect |
|---|---|
| `p` | Pause / resume (toggle) |
| `r` | Restart from the beginning of the capture |
| `q` | Stop and exit |

Ctrl+C also stops cleanly. There's no separate "Start" command -- running
`python -m app.main` *is* start.

### 4. Watch it

Refresh the Diagnostics dashboard (it auto-refreshes every 5s). The
**Replay Status** table shows which capture is playing, its state
(`playing`/`paused`\*/`finished`/`stopped`), playback speed, and position;
the **Candidate Signals (Replay)** table shows every candidate's current
raw value, its tier (`hypothesis`/`raw`), and confidence; the 8 gauge
panels below that show the same candidates' guessed-calibration estimates
(see "Guessed calibration" above) -- hover a gauge's description for its
specific basis.

\* `paused` isn't currently published as its own `replay_status` state --
while paused, the last `"playing"` status simply stops updating (position
freezes). If you want `state` to explicitly say `"paused"`, that's a
small, easy follow-up to `main.py`'s pause-wait loop, not implemented
yet.

## Known limitations / follow-ups

- `--publish-interval` defaults to 1 real second between InfluxDB writes,
  independent of playback speed -- at `--speed max`, this means the
  dashboard updates roughly once per second of *wall-clock* time, showing
  whatever the most recently seen values are at that moment, not every
  single CAN frame. This is deliberate (198,784 frames written
  individually would hammer InfluxDB for no benefit at this stage), but
  worth knowing if a specific fast transient doesn't visibly register.
- Explicit `"paused"` status, noted above.
- Docker usage (`docker compose run --rm replay`) is implemented but has
  not actually been run end-to-end (only the local `python -m app.main`
  path has, against a live InfluxDB/Grafana stack -- see "Verified live"
  below) -- worth a smoke test before relying on it.
- No IPC to control an already-running replay process from outside its
  own terminal (the p/r/q controls only work if you have that terminal).
  To restart or stop it from elsewhere, find and kill the Python process
  and launch a new one. Don't run two instances against the same
  `--capture-name` at once -- both will publish concurrently with nothing
  to detect or prevent it.

## Verified live

Run end-to-end against a real `docker compose --profile dev` InfluxDB +
Grafana stack: replay parsed and played the full `master-test01.txt`
capture (198,784 frames) at 1x, 5x, and 10x speed; `can_replay` and
`replay_status` points were confirmed landing correctly via direct
InfluxDB queries; the Diagnostics dashboard was confirmed provisioned
with all 16 panels via Grafana's API; the p/r/q controls and a full
stop/restart were exercised manually. Gary then watched a live replay and
validated the gauges directly (2026-08-19): RPM, Coolant, Oil Pressure,
and Raw Water Pressure all looked plausible on first pass (Oil Pressure
noted as jumpy -- fixed with a 10s rolling mean, see above); Fuel, Depth,
Battery Voltage, and Trim initially read implausibly (an `UNANCHORED`
guess doing exactly its job -- flagging those candidates/assumptions as
suspect) and were refitted using his live 25%-in observation as a new
ground-truth anchor, same as the field sheet.

## Tests

```sh
python -m unittest discover -s services/replay/tests -t services/replay
```

Covers `pacing.py` (speed math), `candidates.py` (table sanity -- unique
labels, valid tiers, every candidate cited, "hypothesis" tier reserved
for >=50% confidence, every `Guess`/`InterpolatedGuess` has a valid
basis/unit/note, `Guess`'s scale/offset math, `InterpolatedGuess`'s
interpolation/extrapolation math including that RPM's own confirmed
anchor points round-trip exactly), `reader.py` (frame matching/extraction, including
against a real committed sample log), `config.py` (CLI parsing),
`publisher.py` (the `can_replay` point built correctly with/without a
guess attached, via a recording stand-in that never touches a real
InfluxDB connection), and `main.py` (the Controls pause/restart/stop
state machine and the full playback loop, driven end-to-end with a fake
publisher and fake clock).
