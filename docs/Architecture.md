# Architecture

## Overview

```
 ┌─────────────┐      Signal K-shaped points      ┌───────────┐      Flux queries      ┌─────────┐
 │  Telemetry  │ ───────────────────────────────> │ InfluxDB  │ ─────────────────────> │ Grafana │
 │  publisher  │      (line protocol / HTTP)       │  (2.x)    │                        │  (11.x) │
 └─────────────┘                                   └───────────┘                        └─────────┘
       ▲
       │ today: services/simulator (OC-001)
       │ future: SmartCraft/CAN driver, same interface
```

The telemetry publisher is a replaceable role, not a fixed component. Today
it's the simulator (`services/simulator`); a future milestone will replace
it with a driver that decodes real SmartCraft CAN traffic. Both produce the
same shape of data — Signal K paths and SI units — and publish to InfluxDB
the same way, so nothing downstream (InfluxDB, Grafana, dashboards) needs
to change when that swap happens.

See the ADRs for the reasoning behind each major decision:

- [ADR 0001](adr/0001-signal-k-canonical-data-model.md) — Signal K as the canonical data model, and the InfluxDB schema mapping.
- [ADR 0002](adr/0002-influxdb-datastore.md) — why InfluxDB.
- [ADR 0003](adr/0003-deployment-profiles.md) — deployment profiles and why no service may assume co-location.

## Repository layout

```
docker-compose.yml          service composition, profiles: dev / standard / gateway
.env.example                 all configuration; copy to .env
services/simulator/          telemetry publisher (Signal K data model, see ADR 0001)
grafana/
  provisioning/               datasource + dashboard provisioning config
  dashboards/                  dashboard JSON, version-controlled
docs/
  adr/                         architecture decision records
```

## Multi-engine

The architecture supports multiple propulsion engine instances (Signal K
`port`/`starboard`/`center` naming) from the start, even though OC-001 only
simulates and displays one. Adding a second engine is a configuration
change (`SIMULATOR_ENGINES=port,starboard` in `.env`), not a redesign:

- The simulator instantiates one `EngineSimulator` per configured instance.
- Dashboards select engines via a Grafana template variable (`$engine`)
  populated by querying InfluxDB for distinct `instance` tag values, with
  engine-specific panels repeating per selected value.

Known current limitation: the house battery in `services/simulator` is
modeled once per process, not independently of any one engine's
alternator. This is a simplification appropriate to OC-001's single-engine
scope, not a schema limitation — see `services/simulator/app/signalk.py`.

## Data flow detail

1. `services/simulator` advances a physically-motivated engine model every
   tick (default 1s) — see `services/simulator/app/engine.py` for the
   model, and its docstring for why values ease toward targets rather than
   jumping randomly.
2. Engine state is mapped to Signal K paths and written to InfluxDB via the
   `influxdb-client` Python library (`services/simulator/app/signalk.py`,
   `publisher.py`).
3. Alongside raw telemetry, threshold-derived `notifications.*` points are
   written (over-temperature, low oil pressure, low voltage), each with a
   `state` (normal/warn/alarm) and numeric `severity` (0/1/2).
4. Grafana queries InfluxDB directly via Flux (no intermediate API layer).
   The Alarm Banner panel takes `max()` of `severity` across all
   notification paths to summarize vessel-wide alarm state in one number.
