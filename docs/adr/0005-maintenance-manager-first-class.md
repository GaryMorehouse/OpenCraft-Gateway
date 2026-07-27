# ADR 0005: Maintenance Manager as a first-class OpenCraft module

## Status

Accepted (OC-003) — documentation/architecture only, not yet implemented.

## Context

OpenCraft's mission has been framed around telemetry: read SmartCraft data,
decode it, display it. That's also what every proprietary marine gateway
already does — it's not a differentiator on its own.

OC-003 identified a gap: proprietary systems monitor a boat, but they don't
help an owner *take care of* it, and they generally assume the owner (or
their mechanic) already knows what needs doing and when. OpenCraft's
existing design principles already commit to being "well documented" and
built for a range of owners, not just experienced mechanics — a maintenance
feature that assumes mechanical fluency would contradict that.

## Decision

Maintenance management (engine-hour and calendar-based intervals, Boat
Health status, guided maintenance instructions, operational checklists) is
adopted as a **core OpenCraft module**, documented alongside the Helm
Display and SmartCraft Gateway in [FEATURES.md](../FEATURES.md) — not
filed away as a "someday" plugin idea.

The non-negotiable design rule, carried from OC-003 into
[ProjectVision.md](../ProjectVision.md): **OpenCraft should never assume
the owner is a mechanic.** Every maintenance reminder must answer three
questions — what needs attention, why it matters, what to do next. A
reminder that only says "change oil" without the why and the next step
fails this bar.

Checklists (Departure, Launch, Winterization, etc.) are explicitly a
**separate concept from maintenance** — situational/recurring rather than
interval-driven — including an optional "have you checked the trailer?"
reminder line. The trailer is deliberately **not** a maintained subsystem;
it never appears in Boat Health or gets its own maintenance schedule. This
boundary is called out here because it would be an easy, unnecessary scope
expansion to get wrong later.

## Consequences

- **Data model implication (not yet decided):** maintenance items,
  schedules, logs, and checklist completions are relational/document data
  with write-heavy interactive state (acknowledgement, completion), not
  time-series telemetry. InfluxDB (ADR 0002) is very unlikely to be the
  right store for this — a lightweight relational store (SQLite is the
  natural default for a Pi-class device) is the probable direction. Not
  decided now; deferred to the implementation milestone.
- **Service model implication (not yet decided):** "persist until
  acknowledged" and guided, stateful checklists imply an interactive
  component with write access, not just read-only Grafana panels — Grafana
  is fundamentally a visualization layer over data someone else owns, not
  an interaction/state-management tool. Maintenance Manager likely needs
  its own small service and UI. Not decided now; deferred to the
  implementation milestone.
- FEATURES.md becomes the canonical location for this and future capability
  specs; README stays a short project introduction and points there instead
  of accumulating feature detail itself.
- No code, schema, or deployment-profile changes happen as part of this
  ADR — see the "Consequences" items above for what remains genuinely
  undecided.
