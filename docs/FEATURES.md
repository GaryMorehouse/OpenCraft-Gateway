# Features

The master list of OpenCraft Gateway capabilities — implemented, in progress,
and planned. `README.md` stays a short introduction to the project; this file
is where the product spec actually lives and grows as OpenCraft grows. When a
feature area gets substantial enough to need its own detailed doc, split it
out and link it from here rather than letting this file sprawl indefinitely.

Status legend: ✅ Implemented · 🚧 In Progress · 📋 Planned · 💡 Future Concept

---

## Helm Display

**Status: ✅ Implemented** (against simulated data — see SmartCraft Gateway below)

Grafana dashboards designed to feel like a marine multifunction display, not
a generic IT dashboard: Engine Overview (RPM + Speed as twin hero
instruments, secondary gauges, color-coded status bar), Helm Mode
(large-widget, sunlight-readable layout for underway use), Performance
(historical trends), Fuel (economy/range), Diagnostics.

Details: [Software.md](Software.md).

## SmartCraft Gateway

**Status: 🚧 In Progress**

Reads the Mercury SmartCraft CAN network and decodes it into the project's
canonical Signal K data model. Hardware bring-up (M1) is complete — dual CAN
interfaces verified operational on the Pi Zero 2 W. Capturing live SmartCraft
traffic (M2) is the current milestone; decoding is not yet implemented.

Details: [Hardware.md](Hardware.md), [Milestones.md](Milestones.md).

## Signal K

**Status: 🚧 In Progress**

Signal K paths and SI units are already the canonical internal data model
(ADR 0001) — every telemetry value in the system, real or simulated, is
shaped this way. What's not built yet is publishing to an actual Signal K
server; today the data goes simulator/gateway → InfluxDB → Grafana directly.

Details: [Architecture.md](Architecture.md), [ADR 0001](adr/0001-signal-k-canonical-data-model.md).

## Maintenance Manager

**Status: 📋 Planned** (documented in OC-003; not yet implemented — see [ADR 0005](adr/0005-maintenance-manager-first-class.md))

### Design philosophy

OpenCraft should never assume the owner is a mechanic. Every maintenance
reminder must answer three questions:

1. **What** needs attention?
2. **Why** does it matter?
3. **What should I do next?**

A reminder that fails to answer all three isn't finished.

### Core features

- Engine-hour based maintenance intervals (sourced from existing
  `propulsion.<instance>.runTime` telemetry already flowing through the
  system — see ADR 0001).
- Calendar-based maintenance intervals.
- Startup reminders that persist until acknowledged.
- Due Soon / Due Now / Overdue status.
- Digital maintenance log.
- Boat Health summary (see below).
- Configurable maintenance schedules.

### Guided maintenance

Each maintenance item is intended to eventually carry:

- Description
- Why it matters
- Estimated time
- Difficulty
- DIY vs. professional recommendation
- Typical parts required
- Link to the relevant service manual section

### Boat Health

A dashboard-level summary across vessel systems, each with its own
maintenance status roll-up:

- Engine
- Drive
- Fuel System
- Cooling
- Electrical
- Fresh Water
- Waste
- Safety Equipment

### Future enhancements

- Predictive maintenance
- Printable service reports
- PDF exports
- Multi-device synchronization
- AI maintenance advisor (see AI Assistant, below)

## Checklists

**Status: 📋 Planned**

Deliberately separate from maintenance: checklists are situational and
recurring, not interval-driven. Examples:

- Departure
- Launch
- Return to Dock
- Spring Commissioning
- Winterization

Checklists may include an optional reminder line unrelated to any tracked
system — e.g. *"Have you checked the trailer?"* on a Departure or Return to
Dock checklist. **The trailer is explicitly not a maintained subsystem**
within OpenCraft (no trailer entry in Boat Health, no trailer maintenance
schedule) — it only ever appears as a checklist reminder line.

## AI Assistant

**Status: 💡 Future Concept**

Not yet scoped beyond the "AI maintenance advisor" idea listed under
Maintenance Manager's future enhancements — answering maintenance questions
in plain language, and potentially helping interpret telemetry/diagnostics
for an owner who isn't a mechanic (consistent with the Maintenance Manager's
design philosophy). No architecture or interface decisions made yet.

## Notifications

**Status: 🚧 In Progress**

The Engine Overview status bar and Diagnostics' Active Alarms table
(threshold-derived, real-time, Signal K `notifications.*` — see Architecture)
are implemented today. The broader notification concept — startup reminders
that persist until acknowledged, maintenance due-date alerts — is part of
Maintenance Manager and not yet built.

## Remote Monitoring

**Status: 💡 Future Concept**

Accessing boat status away from the vessel. Not yet designed; likely related
to the "multi-device synchronization" idea under Maintenance Manager's
future enhancements, but broader in scope (telemetry, not just maintenance
state). No decisions made.

## Analytics

**Status: 🚧 In Progress**

The Performance dashboard (historical RPM/temperature/oil pressure/fuel
flow/voltage trends) is implemented. Deeper analysis — predictive
maintenance, trend-based alerts beyond simple thresholds — is a future
concept, not yet scoped.
