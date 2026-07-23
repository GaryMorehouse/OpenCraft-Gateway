"""Physically-motivated single-engine simulation.

Goal: believable engine behavior (a helm at idle, underway, and at cruise —
not random noise per sample). Every quantity either eases toward a target
with a time constant appropriate to its real-world inertia (RPM responds in
seconds, coolant temperature over minutes) or derives directly from RPM/load,
the way the real signals would.

All stored values use Signal K's mandated SI units (Kelvin, Pascal, Hz,
cubic metres per second, ratio 0..1). Unit conversion to PSI/°F/GPH etc. is a
presentation concern and happens in Grafana, not here — see
docs/adr/0001-signal-k-canonical-data-model.md.
"""

import math
import random


KELVIN_OFFSET = 273.15
IDLE_RPM = 650.0
MAX_RPM = 4800.0
IDLE_TEMP_C = 38.0
OPERATING_TEMP_C = 82.0  # thermostat-regulated coolant target, ~180F
RESTING_VOLTAGE = 12.6
CHARGING_VOLTAGE = 14.3

# Assumed fuel tank capacity for the (single, OC-001-scope) simulated engine.
# ~198 US gal, plausible for a MerCruiser-class sterndrive boat. A real
# installation shares one tank across engines; per-engine tank accounting
# is a known simplification here, same category as the shared-battery one
# below — see docs/Software.md "Known gaps".
TANK_CAPACITY_L = 750.0


def _ease(current: float, target: float, dt: float, tau: float) -> float:
    """Exponential approach toward target; tau is the time constant in seconds."""
    if tau <= 0:
        return target
    alpha = 1.0 - math.exp(-dt / tau)
    return current + (target - current) * alpha


class ThrottleProfile:
    """Wanders between idle, cruise, and WOT like an operator would, holding
    each state for a while rather than jittering every tick."""

    def __init__(self, rng: random.Random):
        self._rng = rng
        self.target = 0.0
        self._hold_until = 0.0
        self._t = 0.0

    def step(self, dt: float) -> float:
        self._t += dt
        if self._t >= self._hold_until:
            self.target = self._rng.choice(
                [0.0, 0.0, 0.15, 0.45, 0.6, 0.85, 1.0]
            )
            self._hold_until = self._t + self._rng.uniform(20.0, 90.0)
        return self.target


class EngineSimulator:
    """Simulates one propulsion engine instance (e.g. "port")."""

    def __init__(self, instance: str, seed: int | None = None):
        self.instance = instance
        self._rng = random.Random(seed)
        self._throttle_profile = ThrottleProfile(self._rng)

        self.throttle = 0.0
        self.rpm = IDLE_RPM
        self.temp_c = IDLE_TEMP_C
        self.voltage = RESTING_VOLTAGE
        self.trim_ratio = 0.2
        self._trim_target = 0.2
        self._trim_hold_until = 0.0
        self.runtime_s = 0.0
        self.fuel_used_l = 0.0
        self._elapsed_s = 0.0

    @property
    def running(self) -> bool:
        return self.rpm > IDLE_RPM * 1.05

    def _target_rpm(self, throttle: float) -> float:
        return IDLE_RPM + throttle * (MAX_RPM - IDLE_RPM)

    def _target_temp_c(self, rpm: float) -> float:
        load = (rpm - IDLE_RPM) / (MAX_RPM - IDLE_RPM)
        # Thermostat holds operating temp once warm; heavier load nudges it
        # up slightly rather than letting it run away.
        return OPERATING_TEMP_C + load * 3.0

    def _oil_pressure_kpa(self, rpm: float) -> float:
        # Idle ~15 psi (~103 kPa), WOT ~55 psi (~380 kPa) — roughly linear
        # with a small sqrt curve to flatten the top end like a real pump.
        load = max(0.0, (rpm - IDLE_RPM) / (MAX_RPM - IDLE_RPM))
        base_kpa = 103.0
        span_kpa = 280.0
        return base_kpa + span_kpa * math.sqrt(load) + self._rng.uniform(-3, 3)

    def _fuel_rate_lph(self, rpm: float) -> float:
        # Idle ~1 GPH (~3.8 L/h), WOT ~26 GPH (~98 L/h) for a MerCruiser-class
        # V8 sterndrive, cubic-ish curve since fuel burn grows faster than RPM.
        load = max(0.0, (rpm - IDLE_RPM) / (MAX_RPM - IDLE_RPM))
        return 3.8 + (98.0 - 3.8) * (load**1.6)

    def _target_trim(self, throttle: float) -> float:
        # Operators trim out at speed, trim in near idle — not exact, just plausible.
        return 0.15 + 0.7 * throttle

    def step(self, dt: float) -> None:
        self._elapsed_s += dt

        self.throttle = _ease(self.throttle, self._throttle_profile.step(dt), dt, tau=4.0)
        self.rpm = _ease(self.rpm, self._target_rpm(self.throttle), dt, tau=3.0)
        self.temp_c = _ease(self.temp_c, self._target_temp_c(self.rpm), dt, tau=90.0)

        target_voltage = CHARGING_VOLTAGE if self.running else RESTING_VOLTAGE
        self.voltage = _ease(self.voltage, target_voltage, dt, tau=8.0) + self._rng.uniform(-0.05, 0.05)

        if self._elapsed_s >= self._trim_hold_until:
            self._trim_target = max(0.0, min(1.0, self._target_trim(self.throttle) + self._rng.uniform(-0.05, 0.05)))
            self._trim_hold_until = self._elapsed_s + self._rng.uniform(15.0, 60.0)
        self.trim_ratio = _ease(self.trim_ratio, self._trim_target, dt, tau=6.0)

        self.oil_pressure_kpa_value = self._oil_pressure_kpa(self.rpm)
        self.fuel_rate_lph_value = self._fuel_rate_lph(self.rpm)
        self.fuel_used_l += self.fuel_rate_lph_value * dt / 3600.0

        if self.running:
            self.runtime_s += dt

    # --- Signal K SI unit accessors -------------------------------------

    @property
    def revolutions_hz(self) -> float:
        return self.rpm / 60.0

    @property
    def temperature_kelvin(self) -> float:
        return self.temp_c + KELVIN_OFFSET

    @property
    def oil_pressure_pascal(self) -> float:
        return self.oil_pressure_kpa_value * 1000.0

    @property
    def fuel_rate_m3s(self) -> float:
        return self.fuel_rate_lph_value / 1000.0 / 3600.0

    @property
    def fuel_used_m3(self) -> float:
        return self.fuel_used_l / 1000.0


def _target_speed_kn(throttle: float) -> float:
    # Displacement speed up to ~7kn below the planing threshold, then the
    # hull comes up on plane and speed rises quickly toward WOT — a rough
    # but recognizable planing-hull curve, not a straight line with throttle.
    planing_threshold = 0.35
    if throttle < planing_threshold:
        return (throttle / planing_threshold) * 7.0
    planing_fraction = (throttle - planing_threshold) / (1.0 - planing_threshold)
    return 7.0 + planing_fraction * 31.0


class VesselEnvironment:
    """Shared, non-per-engine signals: depth below transducer, speed over ground."""

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)
        self.depth_m = 12.0
        self._target = 12.0
        self._hold_until = 0.0
        self._t = 0.0
        self.speed_kn = 0.0

    def step(self, dt: float, propulsion_throttle: float = 0.0) -> None:
        self._t += dt
        if self._t >= self._hold_until:
            self._target = self._rng.uniform(2.0, 40.0)
            self._hold_until = self._t + self._rng.uniform(30.0, 120.0)
        self.depth_m = _ease(self.depth_m, self._target, dt, tau=20.0) + self._rng.uniform(-0.1, 0.1)

        # Hull acceleration is slower than engine spool-up but faster than
        # thermal response — tau chosen between the two.
        self.speed_kn = _ease(self.speed_kn, _target_speed_kn(propulsion_throttle), dt, tau=15.0)

    @property
    def speed_over_ground_ms(self) -> float:
        return self.speed_kn * 0.514444
