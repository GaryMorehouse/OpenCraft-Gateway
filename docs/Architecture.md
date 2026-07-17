
# OpenCraft Gateway Architecture

## Overview
OpenCraft Gateway is a bridge between the Mercury SmartCraft network and modern marine and IoT systems.

The gateway listens to SmartCraft CAN traffic, decodes engine and vessel data, and republishes that information in standard formats.

---

## System Architecture

```text
                   +----------------------+
                   |   MerCruiser Engine  |
                   +----------+-----------+
                              |
                     SmartCraft CAN Bus
                              |
                              |
                +-------------+-------------+
                | Waveshare 2-Channel CAN   |
                | HAT (MCP2515 x2)          |
                +-------------+-------------+
                              |
                      SPI Interface
                              |
                    Raspberry Pi Zero 2 W
                              |
      +-----------+-----------+-----------+-----------+
      |           |           |           |           |
      |           |           |           |           |
   Signal K      MQTT      REST API    Data Log    Diagnostics
      |                                       |
      +-------------------+-------------------+
                          |
                       Grafana

                  (Future)
                       |
                 NMEA 2000 Gateway
```

---

## Major Components

### Hardware

- Raspberry Pi Zero 2 W
- Waveshare 2-Channel Isolated CAN HAT
- SmartCraft CAN connection
- Power supply

---

### Software

- Raspberry Pi OS Lite
- SocketCAN
- can-utils
- OpenCraft Gateway
- Signal K
- MQTT Broker

---

## Data Flow

1. SmartCraft broadcasts CAN messages.
2. MCP2515 controllers receive the messages.
3. SocketCAN presents them as Linux CAN interfaces.
4. OpenCraft Gateway decodes SmartCraft messages.
5. Decoded data is published to:
   - Signal K
   - MQTT
   - Local log files
   - Future NMEA 2000 bridge

---

## Design Goals

- Modular
- Open source
- Low cost
- Reliable
- Easy to reproduce
- Well documented
- Extensible

---

## Future Enhancements

- Automatic device discovery
- Multi-engine support
- Alarm monitoring
- Fuel management
- Tank monitoring
- Web configuration interface
- Plugin system
