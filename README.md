# OpenCraft Gateway

An open-source SmartCraft gateway for MerCruiser engines.
The goal is to bridge SmartCraft engine data to modern marine systems including:

- Signal K
- MQTT
- Grafana
- Future NMEA 2000 support

## Hardware

- Raspberry Pi Zero 2 W — SmartCraft/CAN capture and prototyping only, see
  [deployment profiles](docs/adr/0003-deployment-profiles.md)
- Waveshare 2-Channel Isolated CAN HAT (dual MCP2515 controllers)
- Raspberry Pi 4/5 — "Standard Vessel" profile, runs the full stack
- MerCruiser SmartCraft network (not yet connected — see Status)

Full parts list: [hardware/bom/BOM.md](hardware/bom/BOM.md)

## Quick start (Development profile)

```sh
cp .env.example .env
docker compose --profile dev up -d --build
```

Grafana: http://localhost:3000 — see [docs/Software.md](docs/Software.md) for details.

## Project Status

🚧 Early Development — OC-001 (Grafana dashboard prototype against simulated
engine data) in progress. No SmartCraft/CAN/MQTT code yet.

## Documentation

- [Architecture](docs/Architecture.md)
- [Software](docs/Software.md)
- [Architecture Decision Records](docs/adr/)

## Roadmap

- [x] Repository, Raspberry Pi, and project structure set up
- [x] Dashboard prototype against simulated telemetry (OC-001)
- [ ] Capture SmartCraft traffic
- [ ] Decode RPM
- [ ] Decode Engine Temp
- [ ] Decode Trim
- [ ] Publish MQTT
- [ ] Signal K Integration
- [ ] NMEA 2000 Gateway
