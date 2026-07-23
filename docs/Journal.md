2026-07-14

- Created GitHub repository.
- Installed Git.
- Cloned repository.
- Planned hardware.
- Selected Raspberry Pi Zero 2 W.
- Selected MCP2515 CAN interface.

2026-07-23 — OC-000 kickoff, OC-001 dashboard prototype

- OC-000: agreed canonical data model (Signal K), datastore (InfluxDB),
  license (MIT), and general deployment target (embedded on-vessel).
- OC-001: while implementing, found the README's Raspberry Pi Zero 2 W
  hardware target conflicted with InfluxDB's resource needs. Resolved:
  Pi Zero 2 W is for SmartCraft/CAN development and prototyping only, not
  the full stack. Introduced explicit deployment profiles (Development,
  Gateway Only, Standard Vessel, Advanced) so no service assumes
  co-location — see ADR 0003.
- Built and verified end-to-end: `docker compose --profile dev up` brings
  up InfluxDB + Grafana + a Python simulator publishing realistic,
  physically-modeled single-engine telemetry (Signal K paths/SI units).
  Confirmed via live browser check that the Engine Overview dashboard
  renders correctly against real data (all panels, template variable,
  threshold coloring, alarm banner).
- Completed remaining OC-001 dashboard pages: Performance (historical
  charts), Fuel (added simulated vessel speed and a cumulative fuel-used
  counter to support Fuel Economy/Estimated Range), Diagnostics (Active
  Alarms table and Data Source Status are real/functional; ECU Status and
  Gateway Status are honest placeholders pending real hardware).
- Found and fixed a real bug while verifying: Grafana's default Stat/Gauge
  threshold config colors values red above 80 when a panel doesn't set its
  own thresholds. Several current-value panels (Fuel Flow, Engine Hours,
  Depth, and all four Fuel-page stats) inherited this and could
  misleadingly flash red at normal values (e.g. Estimated Range at 221nm).
  Fixed by giving every stat/gauge panel an explicit threshold list.
  Caught this by actually loading the dashboards in a browser against live
  data, not just by reading the JSON.
- OC-001 dashboard requirements are now fully built and verified end-to-end
  (containers built, data flow confirmed in InfluxDB, every panel query
  tested through Grafana's API, dashboards visually confirmed in-browser).