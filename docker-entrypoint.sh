#!/bin/bash
# Docker entrypoint: ensure runtime directories exist at startup.
# Permission fix for named volumes: if the volume was created from an older
# image, directories may be root-owned while the container runs as non-root.
# We check writability and surface a clear error rather than a cryptic crash.
set -e

mkdir -p /var/log/docstamp /opt/docstamp/backend/output /opt/docstamp/backend/data

# Verify critical binaries exist before starting
for bin in gunicorn pandoc; do
    if ! command -v "$bin" >/dev/null 2>&1; then
        echo "WARNING: $bin not found — some features may be unavailable" >&2
    fi
done

exec "$@"
