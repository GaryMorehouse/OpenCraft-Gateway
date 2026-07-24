# Hardware

## Milestone M1 — Hardware Bring-up (complete)

Target device: Raspberry Pi Zero 2 W with a Waveshare 2-Channel Isolated
CAN HAT (dual MCP2515 controllers). See [hardware/bom/BOM.md](../hardware/bom/BOM.md)
for the full parts list.

Completed:

- Raspberry Pi Zero 2 W configured.
- SSH operational.
- SPI enabled.
- Waveshare 2-Channel CAN HAT installed.
- Both MCP2515 controllers detected.
- `can0` verified operational at 250000 bit/s.
- `can1` verified operational at 250000 bit/s.
- CAN utilities (`can-utils`) installed and working.
- Development environment prepared for SmartCraft testing.

This confirms the Pi Zero 2 W can see and talk to both CAN channels at the
bitrate SmartCraft is expected to use. No SmartCraft-specific traffic has
been captured or decoded yet — that starts at M2.

## Next — Milestone M2

Capture live SmartCraft CAN traffic using a SmartCraft extension cable and
`candump`. This is the first point real MerCruiser data enters the
project; everything built so far (Grafana dashboards, the InfluxDB data
model, the simulator) has been built against simulated data in
anticipation of this milestone — see
[docs/adr/0001-signal-k-canonical-data-model.md](adr/0001-signal-k-canonical-data-model.md).
