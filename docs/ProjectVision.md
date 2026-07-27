# Project Vision

## Mission

Build an open-source SmartCraft gateway for MerCruiser engines that integrates with modern marine systems.

## Objectives

- Read SmartCraft CAN bus data.
- Decode engine and vessel information.
- Publish data to Signal K.
- Publish data to MQTT.
- Support dashboards with Grafana.
- Bridge selected data to NMEA 2000.
- Provide a low-cost, open-source alternative to proprietary gateways.
- Help owners maintain their boats, not just monitor them — see
  Intelligent Maintenance Manager below.

## Design Principles

- Open source
- Well documented
- Easy to build
- Modular architecture
- Reliable in a marine environment
- Raspberry Pi Zero 2 W compatible
- Community driven
- **OpenCraft should never assume the owner is a mechanic.** Every
  maintenance reminder answers three questions: what needs attention, why
  it matters, and what to do next. See
  [ADR 0005](adr/0005-maintenance-manager-first-class.md).

## Core Capabilities

Telemetry (SmartCraft decoding, Helm Display, Signal K/MQTT/NMEA 2000
integration) and the **Intelligent Maintenance Manager** are both
first-class parts of OpenCraft, not a core product plus a bolted-on
extra. Monitoring a boat and taking care of it are treated as one
problem. Full spec: [FEATURES.md](FEATURES.md).

## Long-Term Goals

- Auto-discover SmartCraft devices
- Multiple engine support
- Alarm monitoring
- Fuel management
- Tank level monitoring
- Data logging
- Web configuration interface
- Plugin architecture
- Guided maintenance and Boat Health tracking (Engine, Drive, Fuel
  System, Cooling, Electrical, Fresh Water, Waste, Safety Equipment)
- Operational checklists (Departure, Launch, Return to Dock, Spring
  Commissioning, Winterization)
- Predictive maintenance and an AI maintenance advisor
