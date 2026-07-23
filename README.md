# OpenCraft Gateway

An open-source SmartCraft gateway for MerCruiser engines.

## Features

- SmartCraft CAN decoding
- Signal K
- MQTT
- REST API
- Grafana
- Future NMEA 2000 support

## Hardware

- Raspberry Pi Zero 2 W — SmartCraft/CAN capture and prototyping only, see
  [deployment profiles](docs/adr/0003-deployment-profiles.md)
- MCP2515 CAN Interface
- Raspberry Pi 4/5 — "Standard Vessel" profile, runs the full stack

## Quick start (Development profile)

```sh
cp .env.example .env
docker compose --profile dev up -d --build
```

Grafana: http://localhost:3000 — see [docs/Software.md](docs/Software.md) for details.

## Status

🚧 Early Development — OC-001 (Grafana dashboard prototype against simulated
engine data) in progress. No SmartCraft/CAN/MQTT code yet.

## Documentation

- [Architecture](docs/Architecture.md)
- [Software](docs/Software.md)
- [Architecture Decision Records](docs/adr/)

## Roadmap

- [x] Dashboard prototype against simulated telemetry (OC-001)
- [ ] Capture SmartCraft traffic
- [ ] Decode RPM
- [ ] Decode Engine Temp
- [ ] Decode Trim
- [ ] Publish MQTT
- [ ] Signal K Integration
- [ ] NMEA 2000 Gateway