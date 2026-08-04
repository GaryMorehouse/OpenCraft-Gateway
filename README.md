# OpenCraft Gateway

An open-source SmartCraft gateway for MerCruiser engines that goes beyond
monitoring — it helps owners maintain their boats, not just watch gauges.
Bridges SmartCraft engine data to modern marine systems including:

- Signal K
- MQTT
- Grafana
- Future NMEA 2000 support

Full capability list, including the Intelligent Maintenance Manager:
[docs/FEATURES.md](docs/FEATURES.md).

## Hardware

- Raspberry Pi Zero 2 W — SmartCraft/CAN capture and prototyping only, see
  [deployment profiles](docs/adr/0003-deployment-profiles.md)
- Waveshare 2-Channel Isolated CAN HAT (dual MCP2515 controllers)
- Raspberry Pi 4/5 — "Standard Vessel" profile, runs the full stack
- MerCruiser SmartCraft network (not yet connected — see Status)

Full parts list: [hardware/bom/BOM.md](hardware/bom/BOM.md)

### Hardware Bring-up Status — M1 (complete)

- [x] Raspberry Pi Zero 2 W configured
- [x] SSH operational
- [x] SPI enabled
- [x] Waveshare 2-Channel CAN HAT installed
- [x] Both MCP2515 controllers detected
- [x] can0 verified operational at 250000 bit/s
- [x] can1 verified operational at 250000 bit/s
- [x] CAN utilities installed and working
- [x] Development environment prepared for SmartCraft testing

Details: [docs/Hardware.md](docs/Hardware.md)

## Quick start (Development profile)

```sh
cp .env.example .env
docker compose --profile dev up -d --build
```

Grafana: http://localhost:3000 — see [docs/Software.md](docs/Software.md) for details.

## Project Status

🚧 Early Development — M1 (hardware bring-up) complete: dual CAN interfaces
verified operational on the Pi Zero 2 W. Dashboard prototype (OC-001/OC-002)
also in place against simulated engine data. No SmartCraft decoding or MQTT
application code yet — that's M2.

## Documentation

- [Features](docs/FEATURES.md) — the full capability list/product spec
- [Project Vision](docs/ProjectVision.md)
- [Architecture](docs/Architecture.md)
- [Software](docs/Software.md)
- [Reverse Engineering](docs/ReverseEngineering.md) — SmartCraft protocol analysis workflow
- [Milestones](docs/Milestones.md)
- [Architecture Decision Records](docs/adr/)

## Roadmap

- [x] Repository, Raspberry Pi, and project structure set up
- [x] Dashboard prototype against simulated telemetry (OC-001)
- [x] Premium Helm Display redesign + GPS speed (OC-002)
- [x] M1 — Hardware bring-up: dual CAN interfaces verified operational
- [x] OC-003 — Maintenance Manager & Boat Health documented as a core module (see docs/FEATURES.md)
- [ ] M2 — Capture live SmartCraft CAN traffic (SmartCraft extension cable + candump)
- [x] SmartCraft protocol analysis tool — reconstruction, compare, heat map (`tools/smartcraft_decoder.py`, see [docs/ReverseEngineering.md](docs/ReverseEngineering.md))
- [ ] Decode RPM
- [ ] Decode Engine Temp
- [ ] Decode Trim
- [ ] Publish MQTT
- [ ] Signal K Integration
- [ ] NMEA 2000 Gateway
- [ ] Implement Maintenance Manager (data store + service — design TBD, see ADR 0005)
