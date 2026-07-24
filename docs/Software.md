# Software

## Running locally (Development profile)

```sh
cp .env.example .env
docker compose --profile dev up -d --build
```

- Grafana: http://localhost:3000 (`GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` from `.env`)
- InfluxDB: http://localhost:8086

The `OpenCraft Gateway` folder in Grafana contains the provisioned
dashboards, starting with **Engine Overview**. Data should appear within a
few seconds of the simulator starting.

```sh
docker compose --profile dev down          # stop
docker compose --profile dev down -v       # stop and wipe InfluxDB/Grafana volumes
```

## Simulator (`services/simulator`)

Pure-Python, stdlib + `influxdb-client` only. Structure:

- `engine.py` — the physical model (`EngineSimulator`, `VesselEnvironment`, `ThrottleProfile`). No I/O.
- `signalk.py` — maps engine state to Signal K paths/points and derives notification states from thresholds. No I/O.
- `publisher.py` — the only module that talks to InfluxDB.
- `config.py` — all configuration from environment variables, no defaults that assume co-location.
- `main.py` — wires the above into a tick loop.

This separation matters for the eventual SmartCraft driver: it will
replace `engine.py`'s role (produce engine state) while `signalk.py` and
`publisher.py` are reusable as-is, or very nearly so.

## Dashboards

Dashboard JSON lives in `grafana/dashboards/` and is provisioned
automatically (`grafana/provisioning/dashboards/dashboards.yml`) — edits
made in the Grafana UI are NOT persisted; edit the JSON files and redeploy
(`docker compose --profile dev up -d` picks up changes within
`updateIntervalSeconds`, currently 30s).

### Dashboards

- **Engine Overview** (redesigned OC-002) — a slim, color-coded status bar
  (green/amber/red, "SYSTEMS NORMAL" → "WARNING" → "ALARM"); RPM (gauge) and
  Speed (large digital readout) as the two dominant hero instruments,
  side by side; a secondary grid below (Engine Temperature, Oil Pressure,
  Battery Voltage, Fuel Flow, Trim Position, Depth, Engine Hours). Selects
  one engine at a time via the `$engine` dropdown (ADR 0004).
- **Helm Mode** (OC-002 stretch goal) — a large-widget, high-contrast page
  for use while underway: RPM, Speed, Depth, Fuel Flow, Engine Temperature,
  and a big Active Alarms status readout. Fewer panels than Engine
  Overview, each much larger, for at-a-glance/sunlight readability.
- **Performance** — historical trend charts (time series) for RPM, Engine
  Temperature, Oil Pressure, Fuel Flow, and Battery Voltage (vessel-wide).
- **Fuel** — Fuel Flow, Fuel Economy (MPG), Fuel Used, Estimated Range
  (statute miles). Economy and range required adding a simulated
  `navigation.speedOverGround` signal and an assumed fuel tank capacity
  (`TANK_CAPACITY_L` in `engine.py`) — see the `signalk.py` module
  docstring for why these two fields are computed in the simulator rather
  than via a Grafana Flux join. Statute units (not nm/knots) to match
  OC-002's speed spec, which was given in mph.
- **Diagnostics** — Active Alarms (real data: a table of every current
  notification path/state/severity/message, not just the worst-case banner
  summary), Data Source Status (real: seconds since the last telemetry
  point was received), ECU Status and Gateway Status (honest placeholders
  — no physical hardware exists yet to report on).

### Color system

Engine Overview and Helm Mode use a validated, colorblind-checked palette
rather than Grafana's default named colors:

| Role | Hex | Used for |
|---|---|---|
| Good | `#0ca30c` | Normal-range thresholds, status bar "SYSTEMS NORMAL" |
| Warning | `#fab219` | Mid-range thresholds, status bar "WARNING" |
| Critical | `#d03b3b` | Danger-range thresholds, status bar "ALARM" |
| Brand blue | `#3987e5` | Performance/consumption info (Speed, Fuel Flow, Engine Hours) |
| Brand teal | `#199e70` | Positional/environmental info (Trim, Depth) |

This gives the dashboard a considered hierarchy — status colors mean
something consistent everywhere, and the two non-status accent colors group
"how the boat is performing" separately from "where things stand
physically" — rather than every panel being an arbitrary color.

### Known Grafana platform constraints (not fixable from dashboard JSON)

Two things OC-002 asked for aren't achievable purely through Grafana
dashboard JSON in this version, and weren't faked:

- **Rounded panel corners.** Panel chrome (corner radius, border) is
  controlled by Grafana's own theme CSS, not exposed as a per-panel or
  per-dashboard JSON option. Achieving this would need a custom Grafana
  theme build or white-label — a real option eventually, but a separate,
  larger decision than a dashboard redesign.
- **Alarm banner that physically grows only when active.** Grafana panels
  have a fixed pixel size from `gridPos`; nothing in core Grafana resizes a
  panel based on query results. The status bar instead stays a fixed slim
  height and gets *visually* louder — full-saturation color and bold text
  vs. a quiet green line — which is the closest honest equivalent without a
  custom panel plugin.

If either of these matters enough to invest in, the real fix is a custom
Grafana theme/plugin or, eventually, a purpose-built frontend reading the
same InfluxDB data — worth a deliberate future decision, not something to
bolt onto a dashboard-JSON milestone.

## Known gaps / deliberate simplifications

- No fault injection in the simulator — notification thresholds are real
  and wired end-to-end, but normal simulated operation rarely crosses
  them, so the Alarm Banner and Active Alarms table will usually read
  "normal". Adding deliberate fault scenarios for demo/testing purposes is
  a reasonable follow-up, intentionally left out of OC-001 to avoid scope
  creep.
- House battery voltage and fuel tank capacity are both modeled once per
  engine/simulator process, not independently at the vessel level — fine
  for OC-001's single-engine scope, but a real multi-engine vessel shares
  one house bank and (often) one tank across engines. Follow-up work, not
  a schema limitation (see Architecture.md).
- Visual identity work so far covers Engine Overview and Helm Mode (the
  two OC-002 targets) — Performance, Fuel, and Diagnostics still use
  Grafana's default panel styling aside from the ADR 0004 layout fix.
  Extending the marine color system/typography to those pages is a
  reasonable follow-up, not done here to stay within OC-002's stated scope
  ("Redesign the OpenCraft Engine Overview dashboard").
- Grafana's default Stat/Gauge threshold config colors values red above
  80 if no explicit `thresholds` are set on a panel — every stat/gauge
  panel in this project's dashboards sets an explicit threshold list for
  exactly this reason. Keep that in mind when adding new panels.
- Panels with `repeat` set render at full row width in this Grafana
  version regardless of authored `w` — see ADR 0004. No dashboard in this
  project uses panel `repeat` anymore; use a single-select `$engine`
  variable instead.
