"""Writes points to InfluxDB.

Connects lazily and retries on write failure rather than requiring InfluxDB
to be up before this process starts. That matters beyond convenience: in the
"gateway" deployment profile this process runs on different hardware than
InfluxDB and reaches it over the network, so treating the connection as
always-available would be a false assumption. See
docs/adr/0003-deployment-profiles.md.
"""

import logging
import time

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from .config import Config

log = logging.getLogger(__name__)


class TelemetryPublisher:
    def __init__(self, config: Config):
        self._config = config
        self._client = InfluxDBClient(
            url=config.influxdb_url, token=config.influxdb_token, org=config.influxdb_org
        )
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)

    def publish(self, points: list[dict]) -> None:
        influx_points = [self._to_point(p) for p in points]
        try:
            self._write_api.write(bucket=self._config.influxdb_bucket, record=influx_points)
        except Exception:
            log.exception(
                "failed to write %d point(s) to %s — will retry next tick",
                len(influx_points),
                self._config.influxdb_url,
            )

    @staticmethod
    def _to_point(spec: dict) -> Point:
        point = Point(spec["measurement"])
        for key, value in spec.get("tags", {}).items():
            point = point.tag(key, value)
        for key, value in spec["fields"].items():
            point = point.field(key, value)
        return point

    def close(self) -> None:
        self._client.close()


def wait_for_influxdb(config: Config, timeout_s: float = 60.0) -> bool:
    """Best-effort readiness check so early log noise doesn't look like a
    crash loop when InfluxDB is still starting (e.g. first `docker compose up`)."""
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
