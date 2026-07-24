"""Maps simulator engine state onto Signal K paths and derives notifications.

Signal K path -> InfluxDB mapping used throughout this project:
    propulsion.<instance>.<field>   -> measurement="propulsion", tag instance=<instance>, field=<field>
    electrical.batteries.<id>.<f>   -> measurement="electrical.batteries", tag id=<id>, field=<f>
    environment.<path>.<field>      -> measurement="environment", field=<field>
    navigation.<field>              -> measurement="navigation", field=<field>
    notifications.<path>            -> measurement="notifications", tag path=<path>, fields state/severity/message

This keeps the on-disk schema a direct, traceable encoding of the Signal K
path it represents, so a future real Signal K server integration is a
transport change, not a data-model change.

`propulsion.<instance>.fuel.economy` and `.fuel.range` are the one
deliberate exception to "store SI, convert in Grafana" (see ADR 0001):
they're composite metrics (speed combined with fuel rate) with no single
raw sensor behind them and no standard Signal K path, computed once here
from values already in scope in the same simulator tick rather than via a
fragile cross-measurement time-alignment join in Grafana. They're stored
directly in MPG/statute miles (not SI) for the same reason: derived
display-oriented convenience fields, not raw sensor data.
"""

from .engine import TANK_CAPACITY_L, EngineSimulator, VesselEnvironment

# Notification severities follow the Signal K alarm states, collapsed to the
# three that matter for a helm display. Numeric code lets Grafana take a
# max() across paths to drive a single alarm banner.
NORMAL, WARN, ALARM = "normal", "warn", "alarm"
SEVERITY_CODE = {NORMAL: 0, WARN: 1, ALARM: 2}

_OVER_TEMP_WARN_C = 90.0
_OVER_TEMP_ALARM_C = 98.0
_LOW_OIL_WARN_KPA = 140.0
_LOW_OIL_ALARM_KPA = 100.0
_LOW_VOLTAGE_WARN = 12.0
_LOW_VOLTAGE_ALARM = 11.5


def _threshold_state(value: float, warn_at: float, alarm_at: float, higher_is_worse: bool) -> tuple[str, str]:
    if higher_is_worse:
        if value >= alarm_at:
            return ALARM, f"value {value:.1f} at/above alarm threshold {alarm_at:.1f}"
        if value >= warn_at:
            return WARN, f"value {value:.1f} at/above warning threshold {warn_at:.1f}"
    else:
        if value <= alarm_at:
            return ALARM, f"value {value:.1f} at/below alarm threshold {alarm_at:.1f}"
        if value <= warn_at:
            return WARN, f"value {value:.1f} at/below warning threshold {warn_at:.1f}"
    return NORMAL, "within normal range"


def engine_points(engine: EngineSimulator) -> list[dict]:
    """Propulsion + notification points for one engine instance."""
    points = [
        {
            "measurement": "propulsion",
            "tags": {"instance": engine.instance},
            "fields": {
                "revolutions": engine.revolutions_hz,
                "temperature": engine.temperature_kelvin,
                "oilPressure": engine.oil_pressure_pascal,
                "trim": engine.trim_ratio,
                "runTime": engine.runtime_s,
                "fuel.rate": engine.fuel_rate_m3s,
                "fuel.used": engine.fuel_used_m3,
            },
        }
    ]

    checks = [
        (
            f"propulsion.{engine.instance}.overTemperature",
            engine.temp_c,
            _OVER_TEMP_WARN_C,
            _OVER_TEMP_ALARM_C,
            True,
        ),
        (
            f"propulsion.{engine.instance}.lowOilPressure",
            engine.oil_pressure_kpa_value,
            _LOW_OIL_WARN_KPA,
            _LOW_OIL_ALARM_KPA,
            False,
        ),
    ]
    for path, value, warn_at, alarm_at, higher_is_worse in checks:
        state, message = _threshold_state(value, warn_at, alarm_at, higher_is_worse)
        points.append(_notification_point(path, state, message))

    return points


def electrical_points(engine: EngineSimulator) -> list[dict]:
    """House battery + its notification, keyed off engine alternator state.

    Modeled once per engine for OC-001's single-engine scope; a real
    installation would model the house bank independently of any one
    engine's alternator, which is a natural follow-up rather than a
    redesign.
    """
    state, message = _threshold_state(
        engine.voltage, _LOW_VOLTAGE_WARN, _LOW_VOLTAGE_ALARM, higher_is_worse=False
    )
    return [
        {
            "measurement": "electrical.batteries",
            "tags": {"id": "house"},
            "fields": {"voltage": engine.voltage},
        },
        _notification_point("electrical.batteries.house.voltage", state, message),
    ]


def environment_points(env: VesselEnvironment) -> list[dict]:
    return [
        {
            "measurement": "environment",
            "tags": {},
            "fields": {"depth.belowTransducer": env.depth_m},
        }
    ]


def navigation_points(env: VesselEnvironment) -> list[dict]:
    return [
        {
            "measurement": "navigation",
            "tags": {},
            "fields": {"speedOverGround": env.speed_over_ground_ms},
        }
    ]


def fuel_estimate_points(engine: EngineSimulator, env: VesselEnvironment) -> list[dict]:
    """Fuel economy (MPG, statute) and estimated range (statute miles) — see
    module docstring for why these are computed here instead of in a Grafana
    Flux join. Statute miles/MPG rather than nm/gal to match OC-002's
    speedOverGround spec, which is given in mph."""
    gph = engine.fuel_rate_lph_value / 3.785411784
    mpg = env.speed_mph / gph if gph > 0.05 else 0.0

    remaining_l = max(0.0, TANK_CAPACITY_L - engine.fuel_used_l)
    remaining_gal = remaining_l / 3.785411784
    range_mi = remaining_gal * mpg

    return [
        {
            "measurement": "propulsion",
            "tags": {"instance": engine.instance},
            "fields": {
                "fuel.economy": mpg,
                "fuel.range": range_mi,
            },
        }
    ]


def _notification_point(path: str, state: str, message: str) -> dict:
    return {
        "measurement": "notifications",
        "tags": {"path": path},
        "fields": {
            "state": state,
            "severity": SEVERITY_CODE[state],
            "message": message,
        },
    }
