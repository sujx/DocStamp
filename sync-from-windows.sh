#!/usr/bin/env bash
# Sync backend/ + frontend i18n sources from the Windows working tree into the
# WSL clone, normalizing CRLF → LF (the Windows checkout is core.autocrlf=true).
# Usage (from anywhere, inside WSL):  bash sync-from-windows.sh [relative-dir...]
set -euo pipefail

WIN=/mnt/d/Workdir/DocStamp
WSL=/root/Project/DocStamp
DIRS="${*:-backend frontend/i18n frontend/components frontend/pages frontend/layouts}"

for d in $DIRS; do
    mkdir -p "$WSL/$d"
    cp -r "$WIN/$d/." "$WSL/$d/"
done

# Normalize line endings and drop stray pycache (skip .venv)
find "$WSL/backend" "$WSL/frontend" -path "$WSL/backend/.venv" -prune -o -type d -name __pycache__ -print 2>/dev/null \
    | xargs -r rm -rf
find "$WSL/backend" "$WSL/frontend" -path "$WSL/backend/.venv" -prune -o \( -name '*.py' -o -name '*.cfg' -o -name '*.po' -o -name '*.pot' -o -name '*.vue' -o -name '*.ts' -o -name '*.json' \) -print 2>/dev/null \
    | xargs -r sed -i 's/\r$//'

echo "synced: $DIRS"
