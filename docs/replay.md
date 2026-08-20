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
                                                8 "(GUESS)" gauge panels (guess_value, per-candidate units)
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
  plausible-looking min/max). Used for candidates where no real reading
  exists to fit against (Fuel, Depth, Battery Voltage here).

`publisher.py` computes `guess.apply(raw_value)` and writes it as a
*separate* `guess_value` field (never overwriting `value`, the raw
number), tagged with the guess's `unit`. Eight gauge panels in
`diagnostics.json` (titled `"<Name> (GUESS)"`) read `guess_value`, styled
like Engine Overview's real gauges but in a single neutral blue rather
than green/amber/red -- that traffic-light palette implies validated
alarm severity these guesses haven't earned, so it's deliberately not
reused here.

**A guess reading "wrong" is itself useful evidence, not a failure.** Fuel
reading ~2% when the field sheet says the tank was ~100% the whole test
isn't this replay tool malfunctioning -- it's the `UNANCHORED` guess
(plus, more importantly, the underlying raw candidate byte) failing the
same plausibility check a human glancing at the gauge would apply. That's
exactly the "human validation" this whole mechanism exists for.

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
InfluxDB queries; all 9 candidates' `guess_value`s matched the ranges
expected from `docs/master-test01-analysis.md` (including the
`Fuel`/`Depth`/`Battery Voltage` guesses visibly *not* matching their
real field-sheet values, as documented above); the Diagnostics dashboard
was confirmed provisioned with all 16 panels via Grafana's API. The p/r/q
controls and a full stop/restart were exercised manually.

## Tests

```sh
python -m unittest discover -s services/replay/tests -t services/replay
```

Covers `pacing.py` (speed math), `candidates.py` (table sanity -- unique
labels, valid tiers, every candidate cited, "hypothesis" tier reserved
for >=50% confidence, every `Guess` has a valid basis/unit/note, `Guess`'s
own scale/offset math), `reader.py` (frame matching/extraction, including
against a real committed sample log), `config.py` (CLI parsing),
`publisher.py` (the `can_replay` point built correctly with/without a
guess attached, via a recording stand-in that never touches a real
InfluxDB connection), and `main.py` (the Controls pause/restart/stop
state machine and the full playback loop, driven end-to-end with a fake
publisher and fake clock).
