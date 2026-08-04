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

## Project Status

OpenCraft Gateway is an open-source SmartCraft protocol research and
gateway project.

Current milestone:

- ✅ Raspberry Pi CAN capture operational
- ✅ SmartCraft traffic successfully captured
- ✅ Generic SmartCraft packet reconstruction framework complete
- ✅ Automated regression tests
- ✅ Protocol analysis toolkit

Protocol decoding is currently in progress — see
[docs/ReverseEngineering.md](docs/ReverseEngineering.md). No SmartCraft
byte has been decoded/labeled yet (no RPM, temperature, trim, etc.); the
dashboard/Grafana experience runs against simulated data until real
decoded signals replace it.

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
- [x] M2 — Capture live SmartCraft CAN traffic (SmartCraft extension cable + candump)
- [x] SmartCraft protocol analysis tool — reconstruction, compare, heat map (`tools/smartcraft_decoder.py`, see [docs/ReverseEngineering.md](docs/ReverseEngineering.md))
- [ ] Decode RPM
- [ ] Decode Engine Temp
- [ ] Decode Trim
- [ ] Publish MQTT
- [ ] Signal K Integration
- [ ] NMEA 2000 Gateway
- [ ] Implement Maintenance Manager (data store + service — design TBD, see ADR 0005)
