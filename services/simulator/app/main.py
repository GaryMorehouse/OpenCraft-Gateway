"""Simulator entrypoint.

Stands in for the future SmartCraft telemetry publisher: this process's only
job is "produce Signal K-shaped points, publish them to InfluxDB." When the
real SmartCraft/CAN driver replaces this later, it fills the same role
through the same publish path — nothing downstream (InfluxDB, Grafana,
dashboards) should need to change.
"""

import logging
import time

from . import signalk
from .config import Config
from .engine import EngineSimulator, VesselEnvironment
from .publisher import TelemetryPublisher, wait_for_influxdb

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    config = Config.from_env()
    log.info(
        "starting simulator: engines=%s tick=%ss target=%s",
        config.engines,
        config.tick_seconds,
        config.influxdb_url,
    )

    wait_for_influxdb(config)

    engines = [EngineSimulator(instance=name) for name in config.engines]
    environment = VesselEnvironment()
    publisher = TelemetryPublisher(config)

    try:
        while True:
            start = time.monotonic()

            points = []
            for engine in engines:
                engine.step(config.tick_seconds)
                points.extend(signalk.engine_points(engine))
                points.extend(signalk.electrical_points(engine))

            avg_rpm = sum(e.rpm for e in engines) / len(engines)
            avg_trim = sum(e.trim_ratio for e in engines) / len(engines)
            environment.step(config.tick_seconds, propulsion_rpm=avg_rpm, propulsion_trim=avg_trim)
            points.extend(signalk.environment_points(environment))
            points.extend(signalk.navigation_points(environment))

            for engine in engines:
                points.extend(signalk.fuel_estimate_points(engine, environment))

            publisher.publish(points)

            elapsed = time.monotonic() - start
            time.sleep(max(0.0, config.tick_seconds - elapsed))
    except KeyboardInterrupt:
        log.info("shutting down")
    finally:
        publisher.close()


if __name__ == "__main__":
    main()
