# SmartCraft Phase 2 -- Signal Hypotheses

Theories, not conclusions. Every candidate below is scored purely from the evidence in the experiments currently registered in `tools/smartcraft_toolkit/experiments.py`; nothing is hardcoded to a specific CAN ID or byte. Re-run `tools/smartcraft_decoder.py hypotheses` after adding more captures to update every confidence value.

The same byte can legitimately show up as a top candidate for more than one hypothesis below (e.g. something that scales with RPM fits both RPM and Raw Water Pressure, since both plausibly increase together). That is not a bug -- it means the current experiments don't yet distinguish those two theories, and is exactly the kind of gap the suggested experiments are meant to close.

## Data Quality

Two capture sessions exist on disk. The session analyzed here -- idle, 1000rpm, 1650rpm, 1900rpm, idle2, in that order, ~8.4 minutes total -- is clean: every consecutive frame is genuinely distinct. A separate, ~18-hours-earlier session (key-cycle.log, rpm-steps.log, trim-cycles.log, smartcrafttest.log) was also captured, but every one of those four files turned out to contain a single CAN frame (record 00 of ID 170) retransmitted 100,000+ times with no other content -- consistent with a Listen-Only capture against a bus with no other node available to ACK it, not real telemetry. They are excluded from this analysis. Re-capturing a real trim cycle, key cycle, and RPM step test remains open follow-up work.

## Battery Voltage

### Candidate #1

**00000B41**, (whole payload, no record byte), byte 0

Possible Battery Voltage

**Confidence: 45%**

Evidence for:

- stays essentially flat across idle/1000/1650/1900 RPM AND occupies only a narrow slice of this byte's range, consistent with a regulated voltage rail
- no session-long drift

Evidence against:

- shows literally zero fluctuation -- can't rule out a dead/reserved byte rather than a real regulated signal
- the single most distinguishing test for this hypothesis -- the ~12.5V (engine off) -> ~13.8-14.2V (alternator charging) step -- is untestable yet: current captures are five steady-state snapshots (idle, idle again, 1000/1650/1900 RPM) taken ~30-40s apart within one ~8.4-minute session -- there is no key-ON/engine-OFF phase and no long warm-up window in this dataset yet.

Suggested experiment:

Capture a log spanning key-ON (engine off) through cranking and into a stable idle, to directly capture the expected voltage step.

### Candidate #2

**0000410B**, (whole payload, no record byte), byte 0

Possible Battery Voltage

**Confidence: 45%**

Evidence for:

- stays essentially flat across idle/1000/1650/1900 RPM AND occupies only a narrow slice of this byte's range, consistent with a regulated voltage rail
- no session-long drift

Evidence against:

- shows literally zero fluctuation -- can't rule out a dead/reserved byte rather than a real regulated signal
- the single most distinguishing test for this hypothesis -- the ~12.5V (engine off) -> ~13.8-14.2V (alternator charging) step -- is untestable yet: current captures are five steady-state snapshots (idle, idle again, 1000/1650/1900 RPM) taken ~30-40s apart within one ~8.4-minute session -- there is no key-ON/engine-OFF phase and no long warm-up window in this dataset yet.

Suggested experiment:

Capture a log spanning key-ON (engine off) through cranking and into a stable idle, to directly capture the expected voltage step.

### Candidate #3

**170**, record 00, byte 2

Possible Battery Voltage

**Confidence: 45%**

Evidence for:

- stays essentially flat across idle/1000/1650/1900 RPM AND occupies only a narrow slice of this byte's range, consistent with a regulated voltage rail
- no session-long drift

Evidence against:

- shows literally zero fluctuation -- can't rule out a dead/reserved byte rather than a real regulated signal
- the single most distinguishing test for this hypothesis -- the ~12.5V (engine off) -> ~13.8-14.2V (alternator charging) step -- is untestable yet: current captures are five steady-state snapshots (idle, idle again, 1000/1650/1900 RPM) taken ~30-40s apart within one ~8.4-minute session -- there is no key-ON/engine-OFF phase and no long warm-up window in this dataset yet.

Suggested experiment:

Capture a log spanning key-ON (engine off) through cranking and into a stable idle, to directly capture the expected voltage step.

## Coolant Temperature

### Candidate #1

**1E0**, record 03, bytes 2-3 (LE)

Possible Coolant Temperature

**Confidence: 40%**

Evidence for:

- trends upward across the session (idle -> ... -> idle2), consistent with continued warm-up
- higher at idle2 (end of session) than at idle (start of session)
- steady within each short capture, as expected for a slow-changing analog reading

Evidence against:

- shows essentially no movement in this data -- either already at thermostat plateau, or this isn't the right byte; indistinguishable from fuel/depth/reserved with current data
- warm-up curve untestable directly yet: current captures are five steady-state snapshots (idle, idle again, 1000/1650/1900 RPM) taken ~30-40s apart within one ~8.4-minute session -- there is no key-ON/engine-OFF phase and no long warm-up window in this dataset yet.

Suggested experiment:

Capture continuously from a cold start (~72°F ambient) through at least 10-15 minutes of idle to observe the full warm-up curve and confirm it plateaus near thermostat temperature.

### Candidate #2

**1E0**, record 03, bytes 2-3 (BE)

Possible Coolant Temperature

**Confidence: 40%**

Evidence for:

- trends upward across the session (idle -> ... -> idle2), consistent with continued warm-up
- higher at idle2 (end of session) than at idle (start of session)
- steady within each short capture, as expected for a slow-changing analog reading

Evidence against:

- shows essentially no movement in this data -- either already at thermostat plateau, or this isn't the right byte; indistinguishable from fuel/depth/reserved with current data
- warm-up curve untestable directly yet: current captures are five steady-state snapshots (idle, idle again, 1000/1650/1900 RPM) taken ~30-40s apart within one ~8.4-minute session -- there is no key-ON/engine-OFF phase and no long warm-up window in this dataset yet.

Suggested experiment:

Capture continuously from a cold start (~72°F ambient) through at least 10-15 minutes of idle to observe the full warm-up curve and confirm it plateaus near thermostat temperature.

### Candidate #3

**1E0**, record 03, byte 3

Possible Coolant Temperature

**Confidence: 40%**

Evidence for:

- trends upward across the session (idle -> ... -> idle2), consistent with continued warm-up
- higher at idle2 (end of session) than at idle (start of session)
- steady within each short capture, as expected for a slow-changing analog reading

Evidence against:

- shows essentially no movement in this data -- either already at thermostat plateau, or this isn't the right byte; indistinguishable from fuel/depth/reserved with current data
- warm-up curve untestable directly yet: current captures are five steady-state snapshots (idle, idle again, 1000/1650/1900 RPM) taken ~30-40s apart within one ~8.4-minute session -- there is no key-ON/engine-OFF phase and no long warm-up window in this dataset yet.

Suggested experiment:

Capture continuously from a cold start (~72°F ambient) through at least 10-15 minutes of idle to observe the full warm-up curve and confirm it plateaus near thermostat temperature.

## Fuel Level / Depth (indistinguishable)

### Candidate #1

**170**, record 01, bytes 1-2 (LE)

Possible Fuel Level / Depth (indistinguishable)

**Confidence: 40%**

Evidence for:

- nearly constant with only small fluctuations, matching both the fuel (~48%, constant) and depth (~8-9ft, constant) ground truth

Evidence against:

- fuel and depth are indistinguishable from each other (and from a generic reserved/constant byte) with only RPM/idle experiments -- neither ground truth value depends on RPM, so this dataset structurally cannot tell them apart yet

Suggested experiment:

Fuel: compare two captures at meaningfully different fuel levels (e.g. before/after a long run). Depth: compare two captures at different water depths (e.g. different dock/anchorage). A real signal shifts; reserved/padding bytes won't.

### Candidate #2

**170**, record 03, bytes 1-2 (LE)

Possible Fuel Level / Depth (indistinguishable)

**Confidence: 40%**

Evidence for:

- nearly constant with only small fluctuations, matching both the fuel (~48%, constant) and depth (~8-9ft, constant) ground truth

Evidence against:

- fuel and depth are indistinguishable from each other (and from a generic reserved/constant byte) with only RPM/idle experiments -- neither ground truth value depends on RPM, so this dataset structurally cannot tell them apart yet

Suggested experiment:

Fuel: compare two captures at meaningfully different fuel levels (e.g. before/after a long run). Depth: compare two captures at different water depths (e.g. different dock/anchorage). A real signal shifts; reserved/padding bytes won't.

### Candidate #3

**1A0**, record 04, byte 0

Possible Fuel Level / Depth (indistinguishable)

**Confidence: 40%**

Evidence for:

- nearly constant with only small fluctuations, matching both the fuel (~48%, constant) and depth (~8-9ft, constant) ground truth

Evidence against:

- fuel and depth are indistinguishable from each other (and from a generic reserved/constant byte) with only RPM/idle experiments -- neither ground truth value depends on RPM, so this dataset structurally cannot tell them apart yet

Suggested experiment:

Fuel: compare two captures at meaningfully different fuel levels (e.g. before/after a long run). Depth: compare two captures at different water depths (e.g. different dock/anchorage). A real signal shifts; reserved/padding bytes won't.

## Oil Pressure

### Candidate #1

**170**, record 00, bytes 0-1 (LE)

Possible Oil Pressure

**Confidence: 80%**

Evidence for:

- increases with RPM (rank correlation 0.80)
- lower at idle2 (after the RPM run) than at idle (start of session) -- consistent with pressure easing as the engine warms
- stable within each individual capture

Evidence against:

- (none)

Suggested experiment:

Log a mechanical oil pressure gauge reading at cold idle and again after ~10 minutes of idle to directly confirm the expected drop, then compare timestamps against this byte.

### Candidate #2

**170**, record 00, byte 1

Possible Oil Pressure

**Confidence: 80%**

Evidence for:

- increases with RPM (rank correlation 0.80)
- lower at idle2 (after the RPM run) than at idle (start of session) -- consistent with pressure easing as the engine warms
- stable within each individual capture

Evidence against:

- (none)

Suggested experiment:

Log a mechanical oil pressure gauge reading at cold idle and again after ~10 minutes of idle to directly confirm the expected drop, then compare timestamps against this byte.

### Candidate #3

**170**, record 00, bytes 1-2 (BE)

Possible Oil Pressure

**Confidence: 80%**

Evidence for:

- increases with RPM (rank correlation 0.80)
- lower at idle2 (after the RPM run) than at idle (start of session) -- consistent with pressure easing as the engine warms
- stable within each individual capture

Evidence against:

- (none)

Suggested experiment:

Log a mechanical oil pressure gauge reading at cold idle and again after ~10 minutes of idle to directly confirm the expected drop, then compare timestamps against this byte.

## RPM

### Candidate #1

**1A0**, record 05, bytes 1-2 (LE)

Possible RPM

**Confidence: 70%**

Evidence for:

- increases monotonically with RPM across idle -> 1000 -> 1650 -> 1900
- stable within each individual steady-RPM capture
- clear gap between idle and RPM-running values

Evidence against:

- (none)

Suggested experiment:

Hold a single RPM (e.g. 2500) steady for 30+ seconds and confirm the value stays flat; then log a tachometer reading alongside a capture to establish the scaling factor.

### Candidate #2

**1A0**, record 05, byte 2

Possible RPM

**Confidence: 70%**

Evidence for:

- increases monotonically with RPM across idle -> 1000 -> 1650 -> 1900
- stable within each individual steady-RPM capture
- clear gap between idle and RPM-running values

Evidence against:

- (none)

Suggested experiment:

Hold a single RPM (e.g. 2500) steady for 30+ seconds and confirm the value stays flat; then log a tachometer reading alongside a capture to establish the scaling factor.

### Candidate #3

**170**, record 01, bytes 4-5 (LE)

Possible RPM

**Confidence: 55%**

Evidence for:

- increases monotonically with RPM across idle -> 1000 -> 1650 -> 1900
- stable within each individual steady-RPM capture

Evidence against:

- (none)

Suggested experiment:

Hold a single RPM (e.g. 2500) steady for 30+ seconds and confirm the value stays flat; then log a tachometer reading alongside a capture to establish the scaling factor.

## Raw Water Pressure

### Candidate #1

**1A0**, record 05, bytes 1-2 (LE)

Possible Raw Water Pressure

**Confidence: 80%**

Evidence for:

- increases with RPM (rank correlation 1.00)
- lowest at idle among the four RPM conditions, consistent with an impeller-driven pressure
- stable low value at idle rather than noisy

Evidence against:

- the '0 psi with key ON / engine OFF' half of this hypothesis is untestable yet: current captures are five steady-state snapshots (idle, idle again, 1000/1650/1900 RPM) taken ~30-40s apart within one ~8.4-minute session -- there is no key-ON/engine-OFF phase and no long warm-up window in this dataset yet.

Suggested experiment:

Capture a log starting with the key ON and the engine OFF for at least 10 seconds before cranking, to directly test the expected 0 psi floor before the impeller turns.

### Candidate #2

**1A0**, record 05, byte 2

Possible Raw Water Pressure

**Confidence: 80%**

Evidence for:

- increases with RPM (rank correlation 1.00)
- lowest at idle among the four RPM conditions, consistent with an impeller-driven pressure
- stable low value at idle rather than noisy

Evidence against:

- the '0 psi with key ON / engine OFF' half of this hypothesis is untestable yet: current captures are five steady-state snapshots (idle, idle again, 1000/1650/1900 RPM) taken ~30-40s apart within one ~8.4-minute session -- there is no key-ON/engine-OFF phase and no long warm-up window in this dataset yet.

Suggested experiment:

Capture a log starting with the key ON and the engine OFF for at least 10 seconds before cranking, to directly test the expected 0 psi floor before the impeller turns.

### Candidate #3

**170**, record 00, byte 0

Possible Raw Water Pressure

**Confidence: 60%**

Evidence for:

- increases with RPM (rank correlation 1.00)
- lowest at idle among the four RPM conditions, consistent with an impeller-driven pressure
- stable low value at idle rather than noisy

Evidence against:

- no measurable change across the dataset
- the '0 psi with key ON / engine OFF' half of this hypothesis is untestable yet: current captures are five steady-state snapshots (idle, idle again, 1000/1650/1900 RPM) taken ~30-40s apart within one ~8.4-minute session -- there is no key-ON/engine-OFF phase and no long warm-up window in this dataset yet.

Suggested experiment:

Capture a log starting with the key ON and the engine OFF for at least 10 seconds before cranking, to directly test the expected 0 psi floor before the impeller turns.

## Trim

Trim cannot be scored yet: the only capture meant to exercise trim (trim-cycles.log) turned out to contain no real signal -- see Data Quality below. No candidates are reported for this hypothesis; that is an honest 'not yet testable', not a 0% confidence finding.

# Current Protocol Map

Two capture sessions exist on disk. The session analyzed here -- idle, 1000rpm, 1650rpm, 1900rpm, idle2, in that order, ~8.4 minutes total -- is clean: every consecutive frame is genuinely distinct. A separate, ~18-hours-earlier session (key-cycle.log, rpm-steps.log, trim-cycles.log, smartcrafttest.log) was also captured, but every one of those four files turned out to contain a single CAN frame (record 00 of ID 170) retransmitted 100,000+ times with no other content -- consistent with a Listen-Only capture against a bus with no other node available to ACK it, not real telemetry. They are excluded from this analysis. Re-capturing a real trim cycle, key cycle, and RPM step test remains open follow-up work.

## 00000B41

| record | byte | category | detail |
|---|---|---|---|
| (none) | 0 | Likely padding/reserved | constant at 0x83 across every experiment |
| (none) | 1 | Likely status bits | only 2 distinct values observed |
| (none) | 2 | Likely status bits | only 2 distinct values observed |

## 0000410B

| record | byte | category | detail |
|---|---|---|---|
| (none) | 0 | Likely padding/reserved | constant at 0x01 across every experiment |

## 170

| record | byte | category | detail |
|---|---|---|---|
| 00 | 0 | Likely counters | 100% of consecutive samples are non-decreasing |
| 00 | 1 | Likely Oil Pressure | confidence 80% |
| 00 | 2 | Likely padding/reserved | constant at 0x04 across every experiment |
| 00 | 3 | Likely counters | 99% of consecutive samples are non-decreasing |
| 00 | 4 | Likely Oil Pressure | confidence 45% |
| 00 | 5 | Likely padding/reserved | constant at 0xFF across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 00 | 6 | Likely padding/reserved | constant at 0xFF across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 0 | Likely counters | 100% of consecutive samples are non-decreasing |
| 01 | 1 | Likely Oil Pressure | confidence 45% |
| 01 | 2 | Likely padding/reserved | constant at 0x73 across every experiment |
| 01 | 3 | Likely padding/reserved | constant at 0xA0 across every experiment |
| 01 | 4 | Likely counters | 99% of consecutive samples are non-decreasing |
| 01 | 5 | Likely RPM | confidence 55% |
| 01 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 1 | Likely padding/reserved | constant at 0x09 across every experiment |
| 02 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 0 | Likely counters | 91% of consecutive samples are non-decreasing |
| 03 | 1 | Likely Coolant Temperature | confidence 20% |
| 03 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 5 | Likely padding/reserved | constant at 0xFF across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 6 | Likely padding/reserved | constant at 0xFF across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |

## 1A0

| record | byte | category | detail |
|---|---|---|---|
| 00 | 0 | Likely padding/reserved | constant at 0x03 across every experiment |
| 00 | 1 | Likely counters | 100% of consecutive samples are non-decreasing |
| 00 | 2 | Likely counters | 100% of consecutive samples are non-decreasing |
| 00 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 00 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 00 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 00 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 0 | Likely padding/reserved | constant at 0x80 across every experiment |
| 01 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 2 | Likely counters | 100% of consecutive samples are non-decreasing |
| 02 | 3 | Likely counters | 100% of consecutive samples are non-decreasing |
| 02 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 0 | Likely counters | 94% of consecutive samples are non-decreasing |
| 04 | 1 | Unknown | 23 distinct values, no hypothesis scored >= 20% |
| 04 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 2 | Likely counters | 96% of consecutive samples are non-decreasing |
| 05 | 3 | Likely Oil Pressure | confidence 30% |
| 05 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 07 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 07 | 1 | Likely counters | 100% of consecutive samples are non-decreasing |
| 07 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 07 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 07 | 4 | Likely counters | 100% of consecutive samples are non-decreasing |
| 07 | 5 | Likely RPM | confidence 25% |
| 07 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 08 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 08 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 08 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 08 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 08 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 08 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 08 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 09 | 0 | Likely padding/reserved | constant at 0x27 across every experiment |
| 09 | 1 | Likely padding/reserved | constant at 0x0F across every experiment |
| 09 | 2 | Likely counters | 100% of consecutive samples are non-decreasing |
| 09 | 3 | Likely counters | 97% of consecutive samples are non-decreasing |
| 09 | 4 | Likely Oil Pressure | confidence 30% |
| 09 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 09 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0A | 0 | Likely padding/reserved | constant at 0x50 across every experiment |
| 0A | 1 | Likely padding/reserved | constant at 0x32 across every experiment |
| 0A | 2 | Likely padding/reserved | constant at 0x27 across every experiment |
| 0A | 3 | Likely padding/reserved | constant at 0x10 across every experiment |
| 0A | 4 | Likely padding/reserved | constant at 0x14 across every experiment |
| 0A | 5 | Likely padding/reserved | constant at 0x82 across every experiment |
| 0A | 6 | Likely padding/reserved | constant at 0x06 across every experiment |
| 0B | 0 | Likely counters | 99% of consecutive samples are non-decreasing |
| 0B | 1 | Likely Coolant Temperature | confidence 20% |
| 0B | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0B | 3 | Likely counters | 100% of consecutive samples are non-decreasing |
| 0B | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0B | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0B | 6 | Likely padding/reserved | constant at 0x0B across every experiment |
| 0C | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |

## 1E0

| record | byte | category | detail |
|---|---|---|---|
| 00 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 00 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 00 | 2 | Likely counters | 100% of consecutive samples are non-decreasing |
| 00 | 3 | Likely Oil Pressure | confidence 45% |
| 00 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 00 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 00 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 2 | Likely padding/reserved | constant at 0x1F across every experiment |
| 01 | 3 | Likely counters | 100% of consecutive samples are non-decreasing |
| 01 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 2 | Likely padding/reserved | constant at 0x2B across every experiment |
| 02 | 3 | Likely counters | 100% of consecutive samples are non-decreasing |
| 02 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 5 | Likely padding/reserved | constant at 0x0F across every experiment |
| 02 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 2 | Likely padding/reserved | constant at 0x3B across every experiment |
| 03 | 3 | Likely counters | 100% of consecutive samples are non-decreasing |
| 03 | 4 | Likely padding/reserved | constant at 0x0F across every experiment |
| 03 | 5 | Likely padding/reserved | constant at 0x1E across every experiment |
| 03 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 2 | Likely padding/reserved | constant at 0x07 across every experiment |
| 04 | 3 | Likely padding/reserved | constant at 0x36 across every experiment |
| 04 | 4 | Likely padding/reserved | constant at 0x1E across every experiment |
| 04 | 5 | Likely padding/reserved | constant at 0x3C across every experiment |
| 04 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 2 | Likely padding/reserved | constant at 0x04 across every experiment |
| 05 | 3 | Likely padding/reserved | constant at 0x6F across every experiment |
| 05 | 4 | Likely padding/reserved | constant at 0x3C across every experiment |
| 05 | 5 | Likely padding/reserved | constant at 0x46 across every experiment |
| 05 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 3 | Likely padding/reserved | constant at 0xFF across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 06 | 4 | Likely padding/reserved | constant at 0x46 across every experiment |
| 06 | 5 | Likely padding/reserved | constant at 0x50 across every experiment |
| 06 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 07 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 07 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 07 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 07 | 3 | Likely padding/reserved | constant at 0x3D across every experiment |
| 07 | 4 | Likely padding/reserved | constant at 0x50 across every experiment |
| 07 | 5 | Likely padding/reserved | constant at 0x5A across every experiment |
| 07 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 08 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 08 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 08 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 08 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 08 | 4 | Likely padding/reserved | constant at 0x5A across every experiment |
| 08 | 5 | Likely padding/reserved | constant at 0x64 across every experiment |
| 08 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 09 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 09 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 09 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 09 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 09 | 4 | Likely padding/reserved | constant at 0x6E across every experiment |
| 09 | 5 | Likely padding/reserved | constant at 0xFF across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 09 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0A | 0 | Likely padding/reserved | constant at 0x01 across every experiment |
| 0A | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0A | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0A | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0A | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0A | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0A | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0B | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0B | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0B | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0B | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0B | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0B | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0B | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0C | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0D | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0D | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0D | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0D | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0D | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0D | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0D | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0E | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0E | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0E | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0E | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0E | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0E | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0E | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0F | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0F | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0F | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0F | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0F | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0F | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 0F | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 10 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 10 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 10 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 10 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 10 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 10 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 10 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 11 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 11 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 11 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 11 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 11 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 11 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 11 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 12 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 12 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 12 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 12 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 12 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 12 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 12 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 13 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 13 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 13 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 13 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 13 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 13 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 13 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 14 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 14 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 14 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 14 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 14 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 14 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 14 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 15 | 0 | Likely padding/reserved | constant at 0x40 across every experiment |
| 15 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 15 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 15 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 15 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 15 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 15 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 16 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 16 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 16 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 16 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 16 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 16 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 16 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 17 | 0 | Likely padding/reserved | constant at 0x29 across every experiment |
| 17 | 1 | Likely padding/reserved | constant at 0x01 across every experiment |
| 17 | 2 | Likely padding/reserved | constant at 0x0A across every experiment |
| 17 | 3 | Likely padding/reserved | constant at 0x09 across every experiment |
| 17 | 4 | Likely padding/reserved | constant at 0x0B across every experiment |
| 17 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 17 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |

## 1F0

| record | byte | category | detail |
|---|---|---|---|
| 00 | 0 | Likely padding/reserved | constant at 0x17 across every experiment |
| 00 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 00 | 2 | Likely padding/reserved | constant at 0x02 across every experiment |
| 00 | 3 | Likely padding/reserved | constant at 0x03 across every experiment |
| 00 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 00 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 00 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 0 | Likely padding/reserved | constant at 0x77 across every experiment |
| 01 | 1 | Likely padding/reserved | constant at 0x01 across every experiment |
| 01 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 01 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 0 | Likely padding/reserved | constant at 0x17 across every experiment |
| FF | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 3 | Likely padding/reserved | constant at 0x03 across every experiment |
| FF | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| FF | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |

## 1FFD4041

| record | byte | category | detail |
|---|---|---|---|
| 02 | 0 | Likely padding/reserved | constant at 0x01 across every experiment |
| 02 | 1 | Likely counters | 95% of consecutive samples are non-decreasing |
| 02 | 2 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 4 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 02 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 2 | Likely padding/reserved | constant at 0xFF across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 3 | Likely padding/reserved | constant at 0xFF across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 4 | Likely padding/reserved | constant at 0xFF across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 5 | Likely padding/reserved | constant at 0xFF across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 03 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 1 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 2 | Likely padding/reserved | constant at 0x02 across every experiment |
| 04 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 4 | Likely padding/reserved | constant at 0x01 across every experiment |
| 04 | 5 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 04 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 0 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 1 | Likely padding/reserved | constant at 0x3C across every experiment |
| 05 | 2 | Likely padding/reserved | constant at 0x01 across every experiment |
| 05 | 3 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
| 05 | 4 | Likely padding/reserved | constant at 0x02 across every experiment |
| 05 | 5 | Likely padding/reserved | constant at 0x02 across every experiment |
| 05 | 6 | Likely padding/reserved | constant at 0x00 across every experiment (0x00/0xFF is a conventional padding/sentinel value) |
