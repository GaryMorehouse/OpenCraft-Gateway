# Architecture

## Overview

OpenCraft Gateway is a bridge between the Mercury SmartCraft network and
modern marine and IoT systems. The eventual gateway listens to SmartCraft
CAN traffic, decodes engine and vessel data, and republishes it in standard
formats (Signal K, MQTT, Grafana dashboards, and later NMEA 2000).

As of OC-001, no SmartCraft/CAN code exists yet — the project is
deliberately building the software platform (data model, datastore,
dashboards) against simulated data first, so the helm interface is
designed before real hardware is wired in. See below for both the
long-term hardware vision and what's actually implemented today.

## Full system vision (hardware, future)

```text
                   +----------------------+
                   |   MerCruiser Engine  |
                   +----------+-----------+
                              |
                     SmartCraft CAN Bus
                              |
                              |
                +-------------+-------------+
                | Waveshare 2-Channel CAN   |
                | HAT (MCP2515 x2)          |
                +-------------+-------------+
                              |
                      SPI Interface
                              |
                    Raspberry Pi Zero 2 W
                              |
      +-----------+-----------+-----------+-----------+
      |           |           |           |           |
      |           |           |           |           |
   Signal K      MQTT      InfluxDB    Data Log    Diagnostics
      |                       |
      +-----------+-----------+
                  |
               Grafana

                  (Future)
                       |
                 NMEA 2000 Gateway
```

Note: this diagram is updated from the original to route through InfluxDB
(ADR 0002) rather than straight to Grafana — Grafana has no storage of its
own, so something has to sit behind it. Everything else here is still the
target hardware topology: the Pi Zero 2 W does SmartCraft/CAN capture (see
ADR 0003 on why it isn't expected to run the full data stack itself), and
downstream consumers (Signal K, MQTT, Grafana) receive decoded data from
it.

### Hardware

- Raspberry Pi Zero 2 W — SmartCraft/CAN capture
- Waveshare 2-Channel Isolated CAN HAT (dual MCP2515 controllers)
- Raspberry Pi 4/5 — "Standard Vessel" profile, runs the full data stack (ADR 0003)
- SmartCraft CAN connection
- Power supply

Full parts list: [hardware/bom/BOM.md](../hardware/bom/BOM.md)

### Software (target)

- Raspberry Pi OS Lite
- SocketCAN, can-utils
- OpenCraft Gateway (SmartCraft decoder + telemetry publisher)
- Signal K
- MQTT Broker
- InfluxDB, Grafana

### Data flow (target)

1. SmartCraft broadcasts CAN messages.
2. MCP2515 controllers receive the messages.
3. SocketCAN presents them as Linux CAN interfaces.
4. OpenCraft Gateway decodes SmartCraft messages into Signal K paths (ADR 0001).
5. Decoded data is published to InfluxDB, MQTT, Signal K, and (later) an NMEA 2000 bridge.

## Current implementation (OC-001)

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
it with a driver that decodes real SmartCraft CAN traffic (the "Full system
vision" above). Both produce the same shape of data — Signal K paths and SI
units — and publish to InfluxDB the same way, so nothing downstream
(InfluxDB, Grafana, dashboards) needs to change when that swap happens.

See the ADRs for the reasoning behind each major decision:

- [ADR 0001](adr/0001-signal-k-canonical-data-model.md) — Signal K as the canonical data model, and the InfluxDB schema mapping.
- [ADR 0002](adr/0002-influxdb-datastore.md) — why InfluxDB.
- [ADR 0003](adr/0003-deployment-profiles.md) — deployment profiles and why no service may assume co-location.

### Repository layout

```
docker-compose.yml          service composition, profiles: dev / standard / gateway
.env.example                 all configuration; copy to .env
services/simulator/          telemetry publisher (Signal K data model, see ADR 0001)
grafana/
  provisioning/               datasource + dashboard provisioning config
  dashboards/                  dashboard JSON, version-controlled
docs/
  adr/                         architecture decision records
hardware/bom/                  bill of materials
```

### Multi-engine

The architecture supports multiple propulsion engine instances (Signal K
`port`/`starboard`/`center` naming) from the start, even though OC-001 only
simulates and displays one. Adding a second engine is a configuration
change (`SIMULATOR_ENGINES=port,starboard` in `.env`), not a redesign:

- The simulator instantiates one `EngineSimulator` per configured instance.
- Dashboards select engines via a Grafana template variable (`$engine`)
  populated by querying InfluxDB for distinct `instance` tag values, with
  engine-specific panels repeating per selected value.

Known current limitation: the house battery and fuel tank capacity in
`services/simulator` are modeled once per process, not independently of
any one engine. This is a simplification appropriate to OC-001's
single-engine scope, not a schema limitation — see
`services/simulator/app/signalk.py` and `docs/Software.md`.

### Data flow detail

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

## Maintenance Manager (planned, OC-003)

Full feature spec: [FEATURES.md](FEATURES.md). Rationale for treating it as
a core module rather than an add-on: [ADR 0005](adr/0005-maintenance-manager-first-class.md).

This section exists to flag the architectural shape of the problem before
implementation starts — nothing here is a locked decision.

**It doesn't fit the current telemetry pipeline as-is.** Everything built
so far (simulator/gateway → InfluxDB → Grafana) is a one-directional,
mostly-read pipeline: data flows in, Grafana renders it. Maintenance
Manager needs the opposite of that in places — a startup reminder that
"persists until acknowledged" is interactive state that something has to
own and mutate, and Grafana is a visualization layer, not an
interaction/state-management tool. This points toward Maintenance Manager
needing its own small service and UI, not just more Grafana panels — but
that's a design question for the implementation milestone, not decided
here.

**It probably needs a different datastore.** InfluxDB (ADR 0002) is
built for time-series telemetry. Maintenance items, schedules, logs, and
checklist completions are relational/document data — closer to a handful
of tables than a time series. A lightweight relational store (SQLite is
the obvious default for a Pi-class device, consistent with ADR 0003's
resource constraints) is the likely direction, but this is explicitly
**not decided** — OC-003 is documentation/architecture scoping only.

**One integration point already exists.** Engine-hour maintenance
intervals can be sourced directly from `propulsion.<instance>.runTime`,
which is already flowing through InfluxDB today (ADR 0001) — no new
telemetry is needed for that part. Calendar-based intervals need no
telemetry integration at all, just date math against whatever store holds
the maintenance schedule.

## Design goals

- Modular
- Open source
- Low cost
- Reliable
- Easy to reproduce
- Well documented
- Extensible

## Future enhancements

- Automatic device discovery
- Alarm monitoring beyond the current threshold model
- Web configuration interface
- Plugin system
