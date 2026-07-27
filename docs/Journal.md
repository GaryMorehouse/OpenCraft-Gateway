## 2026-07-14

- Created GitHub repository.
- Installed Git.
- Cloned repository.
- Planned hardware.
- Selected Raspberry Pi Zero 2 W.
- Selected MCP2515 CAN interface.
- Created first commit, pushed to GitHub.

## 2026-07-17

### Project Initialization

- Installed Raspberry Pi OS.
- Configured SSH and Git.
- Created project directory structure.
- Added initial project documentation: README, Project Vision, Architecture, Hardware BOM.

## 2026-07-23 — OC-000 kickoff, OC-001 dashboard prototype

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
- Discovered the local clone was stale relative to `origin/main` (a week
  of prior setup work — hardware BOM, Pi setup, initial README/Architecture
  docs — had been pushed but never pulled here). Merged and reconciled
  README.md, Architecture.md, and this Journal rather than overwriting
  either side.

## 2026-07-23 — OC-002: Engine Overview redesign, GPS speed

- Added `navigation.speedOverGround` to the simulator, driven by RPM (not
  throttle) via a piecewise curve through the exact control points in the
  OC-002 spec (idle/slow-cruise/plane/cruise/WOT), plus a mild trim
  correlation. Switched Fuel Economy/Estimated Range from nm/knots to
  MPG/statute miles to match.
- Redesigned Engine Overview: a slim color-coded status bar instead of a
  permanent banner, RPM (gauge) + Speed (large digital readout) as twin
  hero instruments, a tightened secondary panel grid, and a validated
  marine color palette (status colors + two brand accents) in place of
  Grafana's defaults.
- Found a real Grafana platform bug while verifying in-browser: any panel
  with `repeat` set renders at full row width in this Grafana version
  regardless of authored width, even with a single repeated instance. This
  had been silently broken in OC-001's Engine Overview, Performance, and
  Fuel dashboards too — scrolled screenshots never showed two repeat
  panels in the same view, so it went unnoticed. Fixed by switching to a
  single-select `$engine` dropdown and dropping `repeat` everywhere — see
  ADR 0004.
- Built the stretch-goal Helm Mode dashboard: fewer, much larger panels
  (RPM, Speed, Depth, Fuel Flow, Engine Temp, Active Alarms status) for
  underway/sunlight readability.
- Two things OC-002 asked for aren't achievable from Grafana dashboard
  JSON alone in this version — rounded panel corners (theme-level, not
  panel-level) and a status bar that physically grows only when an alarm
  is active (no panel in core Grafana resizes based on query results).
  Documented rather than faked; see Software.md.
- All of the above verified end-to-end: rebuilt the simulator, confirmed
  the new speed curve hits the spec's exact values, and visually confirmed
  every redesigned/new dashboard in a live browser against real data.

## 2026-07-24 — M1: Hardware bring-up complete

- Raspberry Pi Zero 2 W configured; SSH operational; SPI enabled.
- Waveshare 2-Channel CAN HAT installed; both MCP2515 controllers detected.
- `can0` and `can1` both verified operational at 250000 bit/s.
- CAN utilities installed and working; development environment prepared
  for SmartCraft testing.
- This is documentation/hardware work only — no application code or
  architecture changed. See docs/Hardware.md for details.
- Next: M2 — capture live SmartCraft CAN traffic via a SmartCraft
  extension cable and `candump`.

## 2026-07-27 — Repository reconciliation, OC-003 (Maintenance Manager docs)

- Reconciled the Pi's stale git clone (6 commits behind) with `origin/main`
  and resolved a real filename bug: `docs/ProjectVison.md` (typo, missing
  the "i") had been an empty 0-byte placeholder since the project's very
  first commit, while the actual Project Vision content had been written
  to a correctly-spelled `docs/ProjectVision.md` that was never committed
  — sitting untracked on the Pi since 2026-07-17. Verified by MD5 before
  and after every transfer, backed up before any destructive step, only
  removed the empty file after confirming zero data loss. Pi, local clone,
  and `origin/main` now all match.
- OC-003: documented the Intelligent Maintenance Manager as a first-class
  OpenCraft module — design philosophy (never assume the owner is a
  mechanic; every reminder answers what/why/what's-next), core features,
  Boat Health, guided maintenance, and operational checklists (explicitly
  separate from maintenance; the trailer gets a checklist reminder line,
  not a maintained-subsystem entry). See ADR 0005.
- Introduced `docs/FEATURES.md` as the master capability list/product spec
  (Helm Display, SmartCraft Gateway, Signal K, Maintenance Manager, AI
  Assistant, Checklists, Notifications, Remote Monitoring, Analytics),
  each tagged with an honest current status. README now stays a short
  introduction and links there instead of accumulating feature detail.
- Flagged in Architecture.md, not decided: Maintenance Manager's
  "persists until acknowledged" state doesn't fit the current read-mostly
  Grafana/InfluxDB pipeline, and its data (schedules, logs, checklists) is
  relational, not time-series — likely needs its own service and a
  different datastore (SQLite is the probable default). Documentation and
  architecture scoping only, per OC-003 — no code changed.
