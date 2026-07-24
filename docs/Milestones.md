# Milestones

Tracks readiness and completion status for each project milestone. Each
entry records what was checked, the result, and any open items — not just
a checkbox. See [Journal.md](Journal.md) for the day-by-day log this is
distilled from.

---

## M1 — Hardware Bring-up

**Status: ✅ Complete** (2026-07-24)

- [x] Raspberry Pi Zero 2 W configured
- [x] SSH operational
- [x] SPI enabled
- [x] Waveshare 2-Channel CAN HAT installed
- [x] Both MCP2515 controllers detected
- [x] `can0` verified operational at 250000 bit/s
- [x] `can1` verified operational at 250000 bit/s
- [x] CAN utilities installed and working
- [x] Development environment prepared for SmartCraft testing

Details: [Hardware.md](Hardware.md).

---

## M2 — Capture Live SmartCraft CAN Traffic

**Status: 🟡 Ready to start — ✅ environment PASS, two non-blocking items open**

Goal: capture live SmartCraft CAN traffic using a SmartCraft extension
cable and `candump`. First milestone where real MerCruiser data enters the
project.

### Environment readiness (validated 2026-07-24, live on `opencraft-pi`)

| Check | Result |
|---|---|
| OS (Debian 13 trixie, RPi kernel) | ✅ PASS |
| Hardware (Pi Zero 2 W, no throttling) | ✅ PASS |
| SPI configuration | ✅ PASS |
| MCP2515 controllers (both detected at boot) | ✅ PASS |
| `can0` / `can1` (UP, 250000 bit/s, zero errors) | ✅ PASS |
| Installed software (`can-utils`, git, python3) | ✅ PASS |
| Python environment (3.13.5) | ✅ PASS |
| Network connectivity | ✅ PASS |
| Git repository status | ⚠️ see below |
| Disk & memory | ✅ PASS |

**Overall: PASS.** Nothing blocks connecting the SmartCraft extension cable
and starting `candump` capture.

### Open items (non-blocking for M2, worth resolving)

1. **Pi's git clone is behind `origin/main`** (was 5 commits behind as of
   the last check — `git fetch` was run to confirm, `git pull` was not,
   pending your go-ahead). Doesn't block CAN capture, but should be synced
   before any code from this repo is expected to run correctly on the Pi.
2. **`docs/ProjectVision.md` exists on the Pi but was never committed** —
   real content, sitting untracked since 2026-07-17, while the repo
   tracks an empty, typo-named `docs/ProjectVison.md` instead. Needs a
   decision (commit the real file, retire the empty typo'd one) before
   it's lost to a disk failure or a careless `git clean`.
3. **Docker/docker-compose not installed on the Pi.** Not required for M2
   (`candump` needs neither) — becomes relevant when the Pi takes on the
   "Gateway Only" telemetry-publisher role (ADR 0003), which is a later
   milestone. Listed here so it isn't forgotten, not because it blocks M2.

### M2 exit criteria (not yet met — this is the milestone's actual goal)

- [ ] SmartCraft extension cable connected to the engine's SmartCraft network
- [ ] Live CAN frames observed via `candump` on the correct channel
- [ ] Sample capture saved for offline analysis (candump log or similar)
- [ ] Initial read on frame IDs/patterns present, to inform decode work in M3
