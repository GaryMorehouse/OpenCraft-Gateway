# ADR 0001: Signal K as the canonical internal data model

## Status

Accepted (OC-000 kickoff)

## Context

Grafana has no storage of its own — every dashboard is built against whatever
schema sits behind it. Whatever internal data model OC-001 picks, every
dashboard and query written against it becomes expensive to change later.

Signal K integration is a stated goal of this project (see README). Signal K
already defines a complete vocabulary for marine engine and vessel data —
paths like `propulsion.port.revolutions`, `propulsion.port.oilPressure`,
`electrical.batteries.house.voltage` — including multi-engine instance
naming (`port`/`starboard`/`center`).

## Decision

All telemetry, from the OC-001 simulator today through the eventual
SmartCraft/CAN driver, is modeled and stored using Signal K paths and SI
units (Kelvin, Pascal, Hz, m³/s, ratio 0..1), rather than a bespoke schema
translated to Signal K later.

InfluxDB mapping convention used throughout this project:

| Signal K path | InfluxDB |
|---|---|
| `propulsion.<instance>.<field>` | measurement=`propulsion`, tag `instance=<instance>`, field=`<field>` |
| `electrical.batteries.<id>.<field>` | measurement=`electrical.batteries`, tag `id=<id>`, field=`<field>` |
| `environment.<path>` | measurement=`environment`, field=`<path>` |
| `notifications.<path>` | measurement=`notifications`, tag `path=<path>`, fields `state`/`severity`/`message` |

Unit conversion to display units (PSI, °F, GPH, feet) happens in Grafana
queries, not in stored data — the stored values stay standards-compliant SI
so any other Signal K-aware consumer gets correct data without needing to
know this project's display conventions.

## Consequences

- A future real Signal K server integration is a transport change, not a
  data-model migration.
- Dashboards written against `propulsion.<instance>.*` work unmodified when
  a second engine instance appears (see ADR 0003 on the deployment/scope
  side, and `grafana/dashboards/engine-overview.json`'s `$engine` template
  variable on the dashboard side).
- Anyone extending the simulator or the future SmartCraft driver must map
  decoded values onto existing or newly-defined Signal K paths, not invent
  ad hoc field names.
