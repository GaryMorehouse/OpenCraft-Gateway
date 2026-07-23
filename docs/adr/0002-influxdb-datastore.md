# ADR 0002: InfluxDB as the time-series datastore

## Status

Accepted (OC-000 kickoff, reaffirmed OC-001 after resolving the hardware
question below)

## Context

Considered alternatives: Prometheus (pull-based, a poor fit for
event-driven marine sensor data) and TimescaleDB/Postgres (general SQL,
more operational surface than needed here). InfluxDB is common in the
Signal K/marine OSS ecosystem and has an existing track record running
alongside Signal K server on embedded hardware.

A question arose during OC-001 implementation: the repository's existing
README lists a Raspberry Pi Zero 2 W (512MB RAM) as project hardware, which
is tight for InfluxDB + Grafana + a broker running together. This was
resolved by clarifying scope (see ADR 0003): the Pi Zero 2 W is for
SmartCraft/CAN development and prototyping, not for running the full stack.
InfluxDB's actual deployment targets are a desktop development machine and
a Raspberry Pi 4/5 ("Standard Vessel" profile), both of which have ample
headroom for it.

## Decision

InfluxDB 2.x is the canonical time-series datastore, queried via Flux.
Every service that talks to it does so purely through environment
variables (`INFLUXDB_URL`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET`,
`INFLUXDB_TOKEN`) — no service assumes it is co-located with InfluxDB. See
ADR 0003.

## Consequences

- Dashboards are written in Flux against InfluxDB's schema (see ADR 0001
  for the path-to-schema mapping).
- If a future deployment profile targets hardware lighter than a Pi 4
  (e.g. a Pi Zero-class device expected to run the full stack, not just the
  gateway), this decision should be revisited — InfluxDB is not free on
  512MB-class hardware.
