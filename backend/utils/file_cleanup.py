"""Temporary file cleanup via scheduled task.

Replaces the old @after_this_request immediate-deletion pattern.
Files are kept for 7 days to allow:
- Debugging failed operations
- Re-downloading previous results
- Auditing operation logs against file artifacts
"""

import logging
import os
import shutil
import time

logger = logging.getLogger(__name__)

# The upload folder doubles as the home of live state: the stats counter is
# rewritten on every conversion, and .gitkeep keeps the directory in version
# control.  Neither may ever be aged out.
PRESERVED_NAMES = {".stats", ".gitkeep"}


def _tree_stats(path: str) -> tuple[int, int]:
    """Return (file_count, total_bytes) for a file or a directory tree."""
    if os.path.isfile(path):
        return 1, os.path.getsize(path)

    files = 0
    size = 0
    for root, _dirs, names in os.walk(path):
        for name in names:
            try:
                files += 1
                size += os.path.getsize(os.path.join(root, name))
            except OSError:
                continue
    return files, size


def cleanup_temp_files(upload_folder: str, max_age_days: int = 7) -> dict:
    """Delete temporary files and directories older than max_age_days.

    Per-task output directories (pdf2img_*, thumbs_*, print-split task dirs,
    properties batch dirs) are removed recursively with their contents.

    Designed to be called by the worker's daily cleanup thread (see
    backend/worker.py) or by an external cron job.

    Args:
        upload_folder: Directory containing temporary files.
        max_age_days: Entries older than this many days are deleted.

    Returns:
        dict with keys: deleted_count, freed_bytes, errors.
    """
    if not os.path.isdir(upload_folder):
        logger.warning("Upload folder does not exist: %s", upload_folder)
        return {"deleted_count": 0, "freed_bytes": 0, "errors": 0}

    cutoff = time.time() - max_age_days * 86400
    deleted = 0
    freed = 0
    error_count = 0

    for fname in os.listdir(upload_folder):
        if fname in PRESERVED_NAMES:
            continue
        fpath = os.path.join(upload_folder, fname)
        try:
            if os.path.getmtime(fpath) >= cutoff:
                continue
            files, size = _tree_stats(fpath)
            if os.path.isdir(fpath):
                shutil.rmtree(fpath)
            else:
                os.remove(fpath)
            deleted += files or 1
            freed += size
        except OSError as e:
            logger.warning("Failed to delete %s: %s", fpath, e)
            error_count += 1

    if deleted:
        logger.info(
            "Cleaned %d temp files, freed %d bytes, %d errors",
            deleted, freed, error_count,
        )

    return {
        "deleted_count": deleted,
        "freed_bytes": freed,
        "errors": error_count,
    }
