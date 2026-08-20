"""Replay entrypoint. See docs/replay.md for the full design and how to
run this against a Docker-composed InfluxDB/Grafana.

Controls, typed on stdin followed by Enter, while replay is running:
    p        pause / resume (toggle)
    r        restart from the beginning of the capture
    q        stop and exit
Ctrl+C also stops cleanly.
"""
from __future__ import annotations

import logging
import sys
import threading
import time

from .candidates import CANDIDATES
from .config import Config
from .pacing import playback_delay
from .publisher import ReplayPublisher, wait_for_influxdb
from .reader import iter_snapshots, load_frames

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


class Controls:
    """Background stdin reader driving pause/restart/stop. A plain class
    (not just flags in main()) so tests can drive it without real stdin."""

    def __init__(self, read_stdin: bool = True) -> None:
        self.paused = False
        self.stop = False
        self.restart = False
        if read_stdin:
            threading.Thread(target=self._read_loop, daemon=True).start()

    def _read_loop(self) -> None:
        for line in sys.stdin:
            self.handle(line.strip().lower())

    def handle(self, cmd: str) -> None:
        if cmd == "p":
            self.paused = not self.paused
            log.info("%s", "PAUSED" if self.paused else "RESUMED")
        elif cmd == "r":
            self.restart = True
            self.paused = False
            log.info("RESTART requested")
        elif cmd in ("q", "quit", "stop"):
            self.stop = True
            log.info("STOP requested")


def run(
    config: Config,
    controls: Controls | None = None,
    sleep=time.sleep,
    publisher=None,
    candidates=None,
) -> None:
    """publisher and candidates are injectable so tests can drive the full
    pause/restart/stop state machine without a real InfluxDB connection or
    the full master-test01 candidate table."""
    frames = load_frames(config.log_path)
    if not frames:
        raise SystemExit(f"no frames parsed from {config.log_path}")
    duration_s = frames[-1].timestamp - frames[0].timestamp
    log.info(
        "loaded %d frames from %s (%.1fs simulated), speed=%s, capture=%s",
        len(frames), config.log_path, duration_s, config.speed_label, config.capture_name,
    )
    log.info("controls: type p<Enter> to pause/resume, r<Enter> to restart, q<Enter> to stop")

    if publisher is None:
        wait_for_influxdb(config)
        publisher = ReplayPublisher(config)
    candidates = candidates if candidates is not None else CANDIDATES
    by_label = {c.label: c for c in candidates}
    controls = controls or Controls()

    try:
        while True:
            controls.restart = False
            _play_once(frames, duration_s, config, publisher, candidates, by_label, controls, sleep)
            if controls.stop or not controls.restart:
                break
    finally:
        publisher.publish_status(config.capture_name, "stopped", 0.0, duration_s, config.speed_label)
        publisher.close()


def _play_once(frames, duration_s, config, publisher, candidates, by_label, controls: Controls, sleep) -> None:
    t0 = frames[0].timestamp
    prev_ts = t0
    last_publish = 0.0
    values: dict[str, int] = {}

    publisher.publish_status(config.capture_name, "playing", 0.0, duration_s, config.speed_label)

    for frame, updates in iter_snapshots(frames, candidates):
        if controls.stop or controls.restart:
            return
        while controls.paused and not controls.stop and not controls.restart:
            sleep(0.1)
        if controls.stop or controls.restart:
            return

        dt = frame.timestamp - prev_ts
        delay = playback_delay(dt, config.speed_multiplier)
        if delay > 0:
            sleep(delay)
        prev_ts = frame.timestamp
        values.update(updates)

        now = time.monotonic()
        if now - last_publish >= config.publish_interval_s:
            publisher.publish_candidates(config.capture_name, values, by_label)
            publisher.publish_status(
                config.capture_name, "playing", frame.timestamp - t0, duration_s, config.speed_label,
            )
            last_publish = now

    if controls.stop or controls.restart:
        return

    publisher.publish_candidates(config.capture_name, values, by_label)
    publisher.publish_status(config.capture_name, "finished", duration_s, duration_s, config.speed_label)
    log.info("replay finished (%d candidate fields published) -- p to restart, or leave running", len(values))

    # Idle here (rather than returning to run()'s loop immediately) so the
    # dashboard keeps showing "finished" until the user explicitly restarts
    # or stops, instead of silently looping.
    while not controls.stop and not controls.restart:
        sleep(0.2)


def main(argv=None) -> None:
    config = Config.from_args(argv)
    try:
        run(config)
    except KeyboardInterrupt:
        log.info("interrupted, shutting down")


if __name__ == "__main__":
    main()
