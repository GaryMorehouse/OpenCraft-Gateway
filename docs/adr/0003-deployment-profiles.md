# ADR 0003: Deployment profiles and no-colocation architecture

## Status

Accepted (OC-001)

## Context

The project's existing README lists a Raspberry Pi Zero 2 W as project
hardware. During OC-001 this raised a real conflict: InfluxDB (ADR 0002) is
uncomfortable on 512MB of RAM, and OC-001 is precisely the milestone where
the datastore choice gets baked into every dashboard query.

Gary clarified the actual intent: the Pi Zero 2 W is the initial hardware
for SmartCraft development, CAN capture, and prototyping — not the intended
platform for the complete OpenCraft stack. The real requirement is that
services must be deployable independently, so a small CAN-facing device and
a more capable device running the data/visualization stack can be separate
physical machines when needed.

## Decision

Four deployment profiles, none of which are hardcoded into any service —
every service reads where its dependencies live from environment variables
only (see `.env.example`):

- **Development** — Windows/macOS/Linux, full stack via Docker Compose.
- **Gateway Only** — Raspberry Pi Zero 2 W, runs only the SmartCraft
  gateway and telemetry publisher (currently the simulator standing in for
  it), pointed at InfluxDB running elsewhere via `INFLUXDB_URL`.
- **Standard Vessel** — Raspberry Pi 4/5, full stack colocated.
- **Advanced** — services distributed across multiple devices as desired;
  no dedicated compose file, since every service already supports this by
  configuration.

Implemented as Docker Compose `profiles:` within a single `docker-compose.yml`
(`dev`, `standard`, `gateway`) rather than separate compose files per
profile, so service definitions cannot drift apart between profiles.

The simulator (`services/simulator`) is written to this same contract
deliberately: it is today's stand-in for the future SmartCraft telemetry
publisher, and it connects to InfluxDB the same way that driver eventually
will — lazily, with retries, never assuming InfluxDB is on `localhost`.
When the real driver replaces it, no downstream service should need to
change.

## Consequences

- No service may hardcode `localhost` or a Docker Compose service name as a
  dependency address; all such addresses come from environment variables.
- Adding a new deployment topology is a `.env` change, not a code change.
- The "Gateway Only" profile currently runs the simulator rather than real
  hardware — this is intentional and temporary; OC-001 explicitly excludes
  SmartCraft/CAN/MQTT implementation.
