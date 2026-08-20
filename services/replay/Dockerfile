# Build context is the repo root (see docker-compose.yml's "replay"
# service), not this directory, because this image also needs
# tools/smartcraft_toolkit -- the CAN parsing/extraction code this service
# reuses rather than duplicating (see app/__init__.py).
FROM python:3.12-slim

WORKDIR /repo/services/replay

COPY services/replay/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/replay/app ./app
COPY tools/smartcraft_toolkit /repo/tools/smartcraft_toolkit
COPY tools/samples /repo/tools/samples

# Interactive controls (p/r/q on stdin) need a real stdin/tty -- run this
# service with `docker compose run --rm` (or `-it` with `docker run`), not
# `up -d`, if you want to use them.
ENTRYPOINT ["python", "-m", "app.main"]
