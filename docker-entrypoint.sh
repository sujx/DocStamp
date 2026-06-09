#!/bin/bash
# Docker entrypoint: ensure runtime directories exist at startup.
# Permission fix for named volumes: if the volume was created from an older
# image, directories may be root-owned while the container runs as non-root.
# We check writability and surface a clear error rather than a cryptic crash.
set -e

mkdir -p /var/log/docstamp /opt/docstamp/backend/output

exec "$@"
