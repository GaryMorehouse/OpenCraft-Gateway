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

### Dashboards (OC-001, complete)

- **Engine Overview** — RPM, Engine Temperature, Oil Pressure, Fuel Flow,
  Engine Hours, Trim Position (all repeat per `$engine`), Battery Voltage,
  Depth, Alarm Banner (vessel-wide, not per-engine).
- **Performance** — historical trend charts (time series, not current-value
  stats) for RPM, Engine Temperature, Oil Pressure, Fuel Flow (repeat per
  `$engine`), and Battery Voltage (vessel-wide).
- **Fuel** — Fuel Flow, Fuel Economy, Fuel Used, Estimated Range (all
  repeat per `$engine`). Economy and range required adding a simulated
  `navigation.speedOverGround` signal and an assumed fuel tank capacity
  (`TANK_CAPACITY_L` in `engine.py`) — see the `signalk.py` module
  docstring for why these two fields are computed in the simulator rather
  than via a Grafana Flux join.
- **Diagnostics** — Active Alarms (real data: a table of every current
  notification path/state/severity/message, not just the worst-case banner
  summary), Data Source Status (real: seconds since the last telemetry
  point was received), ECU Status and Gateway Status (honest placeholders
  — no physical hardware exists yet to report on).

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
- Dashboard visuals currently use stock Grafana panel styling. The
  "distinctly OpenCraft, not generic IT dashboard" visual identity goal
  (see project design principles) is only partially addressed so far (dark
  theme, restrained use of color/backgrounds to avoid a "wall of green
  boxes" look) — deeper theming is follow-up work.
- Grafana's default Stat/Gauge threshold config colors values red above
  80 if no explicit `thresholds` are set on a panel — every stat/gauge
  panel in this project's dashboards sets an explicit threshold list for
  exactly this reason. Keep that in mind when adding new panels.
