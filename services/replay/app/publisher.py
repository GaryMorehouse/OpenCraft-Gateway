"""Writes replay points to InfluxDB, deliberately using measurement names
that never overlap the simulator/gateway publisher's calibrated Signal K
measurements (propulsion, electrical.batteries, environment, navigation --
see services/simulator/app/signalk.py).

None of candidates.py's values have a confirmed scale factor -- the
published confidence only identifies *which byte*, not a unit conversion
-- so writing them into those unit-specific fields (Hz, Kelvin, Pascal...)
would silently misrepresent an unconfirmed raw CAN value as a calibrated
reading. Two new measurements instead:

    can_replay      one point per candidate per publish tick
                     tags: capture, hypothesis, tier, unit (guess unit, or
                           "" if this candidate has no guess)
                     fields: value (raw CAN integer, no unit conversion),
                             confidence_pct (-1 if unscored),
                             guess_value (candidates.py's Guess applied to
                             value -- an explicit, separately-labeled
                             illustrative estimate, never a decode; absent
                             for candidates with no Guess, e.g. status flags)
    replay_status    one point per publish tick, drives the dashboard's
                     REPLAY MODE banner
                     tags: capture
                     fields: state, position_s, duration_s, pct_complete,
                             speed, timing_mode ("real" if --log has actual
                             candump -L timestamps, "synthetic" if it
                             doesn't and app/notimestamp.py assigned
                             arbitrary evenly-spaced ones instead -- see
                             docs/replay.md)

Mirrors services/simulator/app/publisher.py's InfluxDB write pattern
(lazy connect, retry-by-logging on write failure, SYNCHRONOUS write API).
"""
from __future__ import annotations

import logging

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from .candidates import ReplayCandidate
from .config import Config
from .pacing import pct_complete

log = logging.getLogger(__name__)


class ReplayPublisher:
    def __init__(self, config: Config):
        self._config = config
        self._client = InfluxDBClient(
            url=config.influxdb_url, token=config.influxdb_token, org=config.influxdb_org
        )
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)

    def publish_candidates(self, capture: str, values: dict[str, int], by_label: dict[str, ReplayCandidate]) -> None:
        points = []
        for label, value in values.items():
            candidate = by_label[label]
            point = (
                Point("can_replay")
                .tag("capture", capture)
                .tag("hypothesis", label)
                .tag("tier", candidate.tier)
                .tag("unit", candidate.guess.unit if candidate.guess else "")
                .field("value", value)
                .field("confidence_pct", candidate.confidence_pct)
            )
            if candidate.guess is not None:
                point = point.field("guess_value", candidate.guess.apply(value))
            points.append(point)
        self._write(points)

    def publish_status(
        self, capture: str, state: str, position_s: float, duration_s: float, speed_label: str,
        timing_mode: str = "real",
    ) -> None:
        point = (
            Point("replay_status")
            .tag("capture", capture)
            .field("state", state)
            .field("position_s", position_s)
            .field("duration_s", duration_s)
            .field("pct_complete", pct_complete(position_s, duration_s))
            .field("speed", speed_label)
            .field("timing_mode", timing_mode)
        )
        self._write([point])

    def _write(self, points: list[Point]) -> None:
        if not points:
            return
        try:
            self._write_api.write(bucket=self._config.influxdb_bucket, record=points)
        except Exception:
            log.exception(
                "failed to write %d point(s) to %s -- will retry next tick",
                len(points), self._config.influxdb_url,
            )

    def close(self) -> None:
        self._client.close()


def wait_for_influxdb(config: Config, timeout_s: float = 60.0) -> bool:
    """Best-effort readiness check, matching services/simulator/app/publisher.py."""
    import time

    deadline = time.monotonic() + timeout_s
    with InfluxDBClient(url=config.influxdb_url, token=config.influxdb_token, org=config.influxdb_org) as client:
        while time.monotonic() < deadline:
            try:
                if client.ping():
                    return True
            except Exception:
                pass
            log.info("waiting for InfluxDB at %s ...", config.influxdb_url)
            time.sleep(2)
    return False
