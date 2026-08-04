# Reverse Engineering SmartCraft

We do not have Mercury's SmartCraft protocol specification. Everything about
the CAN traffic captured off the 2006 Sea Ray 240 Sundancer / MerCruiser 5.0
MPI (ECM555) has to be established from evidence in real captures, not
assumed.

**Rule: no byte gets a name (RPM, trim, oil pressure, ...) until it's been
correlated against a known ground truth** (a gauge reading, a commanded trim
position, a logged RPM from another source, etc.) at the moment the frame
was captured. Until then, bytes are referred to only by `(CAN ID, record,
byte index)`.

## Tooling

[`tools/smartcraft_decoder.py`](../tools/smartcraft_decoder.py) (usage:
[tools/README.md](../tools/README.md)) reconstructs fragmented CAN messages
from `candump -L` logs and reports which bytes changed and which didn't. It
is the first step for any new capture: reconstruct, then look for bytes
whose value tracks something you changed on the boat (throttle, trim, key
position) between two captures.

Workflow:

1. Capture two logs that differ in exactly one condition you can name (e.g.
   `idle.log` vs `1900rpm.log`, or before/after a trim change).
2. `smartcraft_decoder.py compare log_a log_b --report diff.md` — bytes
   marked `changed` (disjoint value ranges between the two logs) are the
   candidates for whatever you varied.
3. `smartcraft_decoder.py heatmap log.log --report heatmap.md` — within a
   single log, a byte that's "never changed" is very unlikely to be a live
   engine signal (more likely a checksum, a constant, or padding); a byte
   that changes on nearly every frame is a strong live-signal candidate.
4. Cross-reference (2) and (3) across multiple RPM/trim points before naming
   anything. A byte can be `changed` between two logs for reasons unrelated
   to the condition you varied (e.g. incidental voltage drift).

## Capture setup

- Raspberry Pi Zero 2 W + MCP2515 (8 MHz) via SocketCAN
- `candump -L`, 250000 baud, Listen Only mode

## Structural findings so far

These describe frame *structure*, not meaning — see the rule above.

| CAN ID | Frame type | Records observed | Notes |
|---|---|---|---|
| `170` | fragmented | `00`-`06`, `FF` | |
| `1A0` | fragmented | `00`-`0C`, `FF` | |
| `1FFD4041` | fragmented | extended (29-bit) ID | |
| `1E0` | fragmented | `00`-`17`, `FF` | |
| `1F0` | fragmented | `00`, `01`, `FF` | |
| `00000B41` | atomic (single-frame) | — | first byte constant in samples so far |
| `0000410B` | atomic (single-frame) | — | first byte constant in samples so far |
| `0E3792F3` | atomic (single-frame) | — | seen only in `smartcrafttest.log`, not in the small committed samples; payload constant in that capture |

"Fragmented" here means `smartcraft_decoder.py` detected the record-number /
`0xFF`-terminator convention from the frames actually seen (see
`tools/smartcraft_toolkit/reconstruct.py::classify_ids`) — it isn't
hardcoded per ID.

## Sample data

Five short real captures (idle and three RPM points) are committed under
[tools/samples/logs/](../tools/samples/logs/) as test fixtures / usage
examples. The larger captures (`key-cycle`, `rpm-steps`, `smartcrafttest`,
`trim-cycles`, 5-10MB each) are kept locally rather than committed to the
repo.
