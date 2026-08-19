# OpenCraft — SmartCraft Controlled Capture Data Sheet

Print this and fill it out by hand during the capture. Approximate
readings and times are fine -- do not alter readings to match expected
values; record what the gauges actually show. This version adds a
**Sender-Disconnect Experiment** section (near the end) developed from
the analysis of `master-test01`; everything else reproduces the original
data sheet unchanged.

**Test #:** _____
**Date:** _____
**Capture filename:** _____

**Engine:** MerCruiser 5.0 MPI
**Boat:** 2006 Sea Ray 240 Sundancer

## Starting Conditions

**Outside temperature:** _____ °F
**Fuel:** _____ %
**Depth:** _____ ft
**Battery voltage, key OFF:** _____ V
**Battery voltage, key ON:** _____ V
**Trim position:** _____

## Test Timeline

Record the actual time from the clock. Approximate readings are fine.

| Time | Event / RPM | Coolant °F | Oil PSI | Water PSI | Voltage | Fuel % | Depth ft | Trim |
|---|---|---|---|---|---|---|---|---|
| _____ | Key ON / engine OFF | | | | | | | |
| _____ | Engine START | | | | | | | |
| _____ | Idle | | | | | | | |
| _____ | Idle | | | | | | | |
| _____ | Idle | | | | | | | |
| _____ | Idle | | | | | | | |
| _____ | 1000 RPM | | | | | | | |
| _____ | 1500 RPM | | | | | | | |
| _____ | 2000 RPM | | | | | | | |
| _____ | 2500 RPM | | | | | | | |
| _____ | Return to idle | | | | | | | |
| _____ | Trim DOWN | | | | | | | |
| _____ | Trim UP | | | | | | | |
| _____ | Trim DOWN | | | | | | | |
| _____ | Trim UP | | | | | | | |
| _____ | Trim DOWN | | | | | | | |
| _____ | Tach CONNECTED | | | | | | | |
| _____ | Tach DISCONNECTED | | | | | | | |
| _____ | Tach RECONNECTED | | | | | | | |
| _____ | Engine STOPPED | | | | | | | |
| _____ | Key OFF | | | | | | | |

## Warm-Up Notes

| Time | RPM | Coolant °F | Oil PSI | Water PSI | Voltage |
|---|---|---|---|---|---|
| _____ | | | | | |
| _____ | | | | | |
| _____ | | | | | |
| _____ | | | | | |
| _____ | | | | | |
| _____ | | | | | |
| _____ | | | | | |
| _____ | | | | | |

## RPM Test

| Target RPM | Actual RPM | Oil PSI | Water PSI | Voltage | Notes |
|---|---|---|---|---|---|
| Idle | | | | | |
| 1000 | | | | | |
| 1500 | | | | | |
| 2000 | | | | | |
| 2500 | | | | | |
| Idle | | | | | |

## Tach Experiment

**Tach connected:** _____
**Time disconnected:** _____
**Traffic immediately after disconnect:** _____

**Time reconnected:** _____
**Traffic immediately after reconnect:** _____

## Sender-Disconnect Experiment

*(New section -- added from the `master-test01` analysis.)* At a steady
idle, briefly unplug each accessible sending unit's electrical connector
**one at a time**, ~10-15 seconds each, with a short settled pause
between senders before moving to the next one. Real oil pressure, water
pressure, coolant temperature, fuel level, depth, and trim position are
all unaffected by unplugging their sender -- only the sensor *signal* is
interrupted -- so this test is meant to reveal which CAN byte goes to a
fixed fault/out-of-range value at each specific disconnect, then returns
to normal on reconnect.

**Caution (oil pressure specifically):** the ECM may read "no signal" as
critically low pressure and trigger an alarm or, on some
SmartCraft-integrated ECMs, a protective rev-limit/reduced-power
response. Keep every disconnect brief, do this at idle only, never at
elevated RPM, and have someone ready to reconnect immediately.

**Does not apply to:** RPM (comes from the crank/cam position sensor,
needed for ignition/injection -- do not disconnect on a running engine)
or battery voltage (no separate sender to unplug -- it's a direct
electrical measurement).

| Sender | Time disconnected | Time reconnected | Notes |
|---|---|---|---|
| Oil pressure | _____ | _____ | |
| Raw water pressure | _____ | _____ | |
| Coolant temperature | _____ | _____ | |
| Fuel level | _____ | _____ | |
| Depth | _____ | _____ | |
| Trim position | _____ | _____ | |

## Other Observations

_____________________________________________________________

_____________________________________________________________

_____________________________________________________________

## Fuel Consumption (Gal/Hr)

| Idle | 1000 | 1500 | 2000 | 2500 | Idle |
|---|---|---|---|---|---|
| | | | | | |

## Expected Approximate Values

- Fuel: ~48%
- Depth: ~8-9 ft
- Coolant: ~72°F cold → ~160°F operating
- Oil pressure: ~50 PSI cold idle; expected to decrease as oil warms and increase with RPM
- Raw water pressure: 0 PSI key-on/engine-off → ~1.6 PSI idle → increases with RPM

**Do not alter readings to match expected values. Record what the gauges actually show.**
