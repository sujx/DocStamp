#!/usr/bin/env bash
# Sync tracked sources from the Windows working tree into the WSL clone,
# normalising CRLF → LF (the Windows checkout is core.autocrlf=true).
# Usage (from anywhere, inside WSL):  bash sync-from-windows.sh [pathspec...]
set -euo pipefail

WIN=/mnt/d/Workdir/DocStamp
WSL=/root/Project/DocStamp
DEFAULT='backend frontend/i18n frontend/components frontend/pages frontend/layouts'
PATHS="${*:-$DEFAULT}"

# Drive the copy off `git ls-files`: only what the repository tracks crosses
# over. Untracked runtime state on the Windows side (tasks.db and its backups,
# backend/output/, __pycache__, .pytest_cache) is stale relative to the WSL
# clone, and copying it once clobbered the local stats DB.
cd "$WIN"
git ls-files -z -- $PATHS |
    while IFS= read -r -d '' f; do
        mkdir -p "$WSL/$(dirname "$f")"
        cp "$WIN/$f" "$WSL/$f"
        # /mnt/d reports everything as 0777; without this git sees a mode change
        # on every copied file and the clone looks permanently dirty.
        chmod 0644 "$WSL/$f"
        case "$f" in
            *.sh) chmod 0755 "$WSL/$f" ;;
            # Binaries (.mo, images) must not be touched by sed.
            *.py|*.cfg|*.ini|*.txt|*.md|*.po|*.pot|*.vue|*.ts|*.js|*.mjs|*.json|*.yaml|*.yml|*.toml|*.sh)
                sed -i 's/\r$//' "$WSL/$f" ;;
        esac
    done

echo "synced: $PATHS"
