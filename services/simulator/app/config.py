"""Configuration read entirely from the environment.

No default here assumes the simulator is co-located with InfluxDB — the
"gateway" deployment profile points INFLUXDB_URL at a remote host. See
docs/adr/0003-deployment-profiles.md.
"""

import os
from dataclasses import dataclass, field


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"required environment variable {name} is not set")
    return value


@dataclass(frozen=True)
class Config:
    influxdb_url: str
    influxdb_org: str
    influxdb_bucket: str
    influxdb_token: str
    engines: list[str]
    tick_seconds: float

    @classmethod
    def from_env(cls) -> "Config":
        engines = [
            e.strip()
            for e in os.environ.get("SIMULATOR_ENGINES", "port").split(",")
            if e.strip()
        ]
        return cls(
            influxdb_url=os.environ.get("INFLUXDB_URL", "http://influxdb:8086"),
            influxdb_org=_require("INFLUXDB_ORG"),
            influxdb_bucket=_require("INFLUXDB_BUCKET"),
            influxdb_token=_require("INFLUXDB_TOKEN"),
            engines=engines or ["port"],
            tick_seconds=float(os.environ.get("SIMULATOR_TICK_SECONDS", "1")),
        )
