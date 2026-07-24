# ADR 0004: Don't use Grafana panel `repeat` on multi-panel dashboard rows

## Status

Accepted (OC-002)

## Context

OC-001's dashboards (Engine Overview, Performance, Fuel) used Grafana's
panel-repeat-by-variable feature (`repeat: "engine"`, `repeatDirection: "h"`)
so that adding a second engine instance would be a `.env` change, not a
dashboard redesign (ADR 0001, ADR 0003).

While redesigning Engine Overview for OC-002, panels stopped laying out
side-by-side and instead stacked full-width, one per row, breaking the
intended grid. Investigation (comparing actual rendered DOM widths via
browser devtools against the dashboard JSON's `gridPos.w`) showed the
cause precisely: **in this Grafana version (11.1.0), any panel with
`repeat` set renders at full row width regardless of its authored `w`**,
even when there is only one repeated instance. Non-repeating panels in the
same dashboard respected their authored width correctly. This was a
pre-existing bug in the OC-001 dashboards too (Performance, Fuel) — it had
gone unnoticed because scrolled, one-panel-at-a-time screenshots didn't
reveal that neighboring repeat panels weren't actually side by side.

## Decision

Dashboard pages that need per-engine panels use a **single-select**
`$engine` template variable (`multi: false, includeAll: false`) instead of
panel `repeat`. Every panel queries `r.instance == "${engine}"` directly, no
panel has `repeat` set, and all panels respect their authored `gridPos`
correctly. The operator switches which engine's data is shown via the
dropdown, rather than seeing all engines' instances of a panel
simultaneously.

Applied to Engine Overview, Performance, Fuel, and Helm Mode. Diagnostics
doesn't filter by engine and was unaffected.

## Consequences

- Adding a second engine is still a `.env` change (`SIMULATOR_ENGINES=port,starboard`)
  — the dropdown will simply offer both, satisfying ADR 0001's multi-engine
  intent. What's no longer true is "see both engines' gauges at once on one
  page" — that would need a deliberate side-by-side layout designed for a
  known engine count, not automatic repeat.
- Any *future* dashboard panel must not use `repeat` if it needs to sit
  beside other panels in a row. If a future milestone genuinely needs
  simultaneous multi-engine display (e.g. a dedicated "twin engine" page
  once a second engine exists), design it as an explicit fixed layout for
  the known engine count, or re-test this Grafana version's repeat behavior
  in case a Grafana upgrade changes it — don't assume repeat is safe.
