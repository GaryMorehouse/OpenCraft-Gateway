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
here invents a new CAN meaning, and no value is ever unit-converted (no
fake °F, PSI, or RPM), because none of those candidates have a confirmed
scale factor yet, only an identified byte location.

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
                                                   can_replay      (tags: capture, hypothesis, tier;
                                                                    fields: value, confidence_pct)
                                                   replay_status   (tags: capture;
                                                                    fields: state, position_s,
                                                                    duration_s, pct_complete, speed)
        |
        v
grafana/dashboards/diagnostics.json            "⚠ REPLAY MODE" banner, "Replay Status" table,
                                                "Candidate Signals (Replay)" table
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
raw value, its tier (`hypothesis`/`raw`), and confidence.

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
- Docker usage (`docker compose run --rm replay`) is implemented but has
  not been run end-to-end in this environment (Docker Desktop wasn't
  running when this was built) -- the local `python -m app.main` path
  has been verified against the real `master-test01.txt` capture
  end-to-end except for the final InfluxDB write itself (also not
  verified live, same reason). Worth a real smoke test before relying on
  either path.
- `explicit "paused" status`, above.

## Tests

```sh
python -m unittest discover -s services/replay/tests -t services/replay
```

Covers `pacing.py` (speed math), `candidates.py` (table sanity -- unique
labels, valid tiers, every candidate cited, "hypothesis" tier reserved
for >=50% confidence), `reader.py` (frame matching/extraction, including
against a real committed sample log), `config.py` (CLI parsing), and
`main.py` (the Controls pause/restart/stop state machine and the full
playback loop, driven end-to-end with a fake publisher and fake clock so
no real InfluxDB or wall-clock waiting is needed).
