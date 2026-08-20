"""Configuration for the replay publisher: CLI arguments for what/how to
replay, environment variables for where InfluxDB is -- reusing the exact
same INFLUXDB_URL/ORG/BUCKET/TOKEN variable names the simulator publisher
uses (services/simulator/app/config.py) so replay can point at the same
InfluxDB instance without inventing new environment variables for what's
already there.
"""
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .pacing import SPEED_MULTIPLIERS

# tools/samples/logs/master-test01.txt, computed from this file's location
# so it works regardless of the process's current working directory.
DEFAULT_LOG = Path(__file__).resolve().parents[3] / "tools" / "samples" / "logs" / "master-test01.txt"


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"required environment variable {name} is not set")
    return value


@dataclass(frozen=True)
class Config:
    log_path: Path
    capture_name: str
    speed_label: str
    speed_multiplier: Optional[float]  # None means "max" -- no pacing delay
    publish_interval_s: float
    influxdb_url: str
    influxdb_org: str
    influxdb_bucket: str
    influxdb_token: str

    @classmethod
    def from_args(cls, argv=None) -> "Config":
        parser = argparse.ArgumentParser(
            prog="python -m app.main",
            description=(
                "Replay a candump -L SmartCraft capture through the existing "
                "OpenCraft Gateway telemetry pipeline (InfluxDB -> Grafana). "
                "Publishes only the already-published hypothesis/candidate "
                "values from app/candidates.py -- see docs/replay.md."
            ),
        )
        parser.add_argument(
            "--log", type=Path, default=DEFAULT_LOG,
            help=f"path to a candump -L log (default: {DEFAULT_LOG})",
        )
        parser.add_argument(
            "--speed", choices=["1", "5", "10", "max"], default="1",
            help="playback speed: 1, 5, 10, or max (default: 1)",
        )
        parser.add_argument(
            "--capture-name", default=None,
            help="override the InfluxDB 'capture' tag value (default: derived "
            "from --log's filename, e.g. 'master-test01')",
        )
        parser.add_argument(
            "--publish-interval", type=float, default=1.0,
            help="seconds of wall-clock time between InfluxDB snapshot writes "
            "(default: 1.0) -- independent of playback speed, so 'max' speed "
            "doesn't flood InfluxDB with a write per frame",
        )
        args = parser.parse_args(argv)

        if not args.log.is_file():
            raise SystemExit(f"log file not found: {args.log}")

        return cls(
            log_path=args.log,
            capture_name=args.capture_name or args.log.stem,
            speed_label=args.speed,
            speed_multiplier=SPEED_MULTIPLIERS[args.speed],
            publish_interval_s=args.publish_interval,
            influxdb_url=os.environ.get("INFLUXDB_URL", "http://localhost:8086"),
            influxdb_org=_require("INFLUXDB_ORG"),
            influxdb_bucket=_require("INFLUXDB_BUCKET"),
            influxdb_token=_require("INFLUXDB_TOKEN"),
        )
