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

# Writability guard. The mkdir above only creates missing directories — it can
# never repair a named volume that an older, root-running image left root-owned.
# Without this check the process starts and then dies inside sqlite3 with an
# opaque "unable to open database file". Fail early, with a fix that keeps data.
for entry in "output_data:/opt/docstamp/backend/output" \
             "log_data:/var/log/docstamp" \
             "db_data:/opt/docstamp/backend/data"; do
    volume="${entry%%:*}"
    dir="${entry#*:}"
    if ! ( : >"$dir/.write-probe" ) 2>/dev/null; then
        echo "ERROR: $dir is not writable by $(id -un) (uid $(id -u))." >&2
        echo "       The '$volume' volume is most likely root-owned — created by an" >&2
        echo "       older image that ran as root, or by 'docker volume create'." >&2
        echo "       Re-own it on the host, then restart the container:" >&2
        echo "         docker compose down" >&2
        echo "         docker run --rm -v ${COMPOSE_PROJECT_NAME:-$(basename "$PWD")}_${volume}:/d alpine chown -R $(id -u):$(id -g) /d" >&2
        echo "         docker compose up -d" >&2
        echo "       Do NOT delete the volume: db_data holds tasks.db, the only copy" >&2
        echo "       of the usage statistics." >&2
        exit 1
    fi
    rm -f "$dir/.write-probe" || true
done

exec "$@"
