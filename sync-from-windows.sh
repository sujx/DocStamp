#!/usr/bin/env bash
# Sync tracked sources from the Windows working tree into the WSL clone,
# normalising CRLF → LF (the Windows checkout is core.autocrlf=true).
# Usage (from anywhere, inside WSL):  bash sync-from-windows.sh [pathspec...]
set -euo pipefail

WIN=/mnt/d/Workdir/DocStamp
WSL=/root/Project/DocStamp
# Everything the repository tracks, so repo-root files (AGENTS.md, SPEC.md,
# manage.sh, Dockerfile) don't rot in the clone; pass pathspecs to narrow it.
PATHS="${*:-.}"

# Drive the copy off `git ls-files -s`: only what the repository tracks crosses
# over. Untracked runtime state on the Windows side (tasks.db and its backups,
# backend/output/, __pycache__, .pytest_cache) is stale relative to the WSL
# clone, and copying it once clobbered the local stats DB.
#
# Modes come from the index, not from a guess: /mnt/d reports every file as
# 0777 and the Windows checkout cannot carry exec bits, so a blanket chmod
# (0644 everywhere, or 0755 for *.sh) disagrees with HEAD on one half of the
# files either way. Mirroring the recorded mode keeps the clone's status clean.
cd "$WIN"
git ls-files -s -z -- $PATHS |
    while IFS=$'\t' read -r -d '' meta f; do
        case "${meta%% *}" in
            100755) perm=0755 ;;
            *) perm=0644 ;;
        esac
        mkdir -p "$WSL/$(dirname "$f")"
        cp "$WIN/$f" "$WSL/$f"
        chmod "$perm" "$WSL/$f"
        case "$f" in
            # Binaries must never be touched by sed. Everything else is text
            # stored LF in the repository and checked out CRLF here, so
            # stripping CR restores what git recorded. A CRLF Dockerfile or
            # *.sh baked into the image breaks the build or the entrypoint.
            *.mo|*.db|*.pdf|*.png|*.jpg|*.jpeg|*.gif|*.webp|*.ico|*.woff|*.woff2|*.ttf|*.eot) ;;
            *) sed -i 's/\r$//' "$WSL/$f" ;;
        esac
    done

echo "synced: $PATHS"
