"""On-disk store for PDF redaction sessions.

The upload folder is the single source of truth. Production runs several
gunicorn workers and recycles them periodically, so anything held in process —
a plain dict, or flask-caching's SimpleCache — would send a follow-up request to
a worker that never saw the upload. Every accessor here re-reads from disk.

The session id is an unguessable 32-hex token the client echoes back on every
follow-up request; only hex ids are accepted, so a crafted id cannot walk out of
the sessions root.
"""

import json
import os
import re
import shutil
import time
import uuid

SESSIONS_DIRNAME = "redact-sessions"
SID_PATTERN = re.compile(r"^[0-9a-f]{32}$")

#: Short by design: redacted documents are sensitive and must not linger.
SESSION_TTL_SECONDS = 3600

SOURCE_NAME = "source.pdf"
OUTPUT_NAME = "redacted.pdf"
META_NAME = "meta.json"


def is_valid_sid(sid) -> bool:
    """True for exactly 32 lowercase hex characters."""
    return isinstance(sid, str) and bool(SID_PATTERN.match(sid))


def session_dir(upload_folder: str, sid) -> str | None:
    """Absolute path of a session directory, or None for an unusable id."""
    if not is_valid_sid(sid):
        return None
    return os.path.join(upload_folder, SESSIONS_DIRNAME, sid)


def create_session(upload_folder: str, original_name: str, source, extra: dict | None = None) -> str:
    """Write the uploaded PDF and its metadata into a new session directory.

    Args:
        upload_folder: Root that holds the sessions directory.
        original_name: The user's filename, kept for the download name.
        source: Bytes or a readable stream (streams are copied in chunks so a
            large upload never has to sit in memory whole).
        extra: Extra metadata to persist alongside (page count, page sizes).

    Returns:
        The new session id.
    """
    sid = uuid.uuid4().hex
    directory = session_dir(upload_folder, sid)
    os.makedirs(directory, exist_ok=True)

    with open(os.path.join(directory, SOURCE_NAME), "wb") as f:
        if isinstance(source, (bytes, bytearray)):
            f.write(source)
        else:
            shutil.copyfileobj(source, f, 1024 * 1024)

    meta = {"original_name": original_name, "created_at": time.time()}
    meta.update(extra or {})
    _write_meta(directory, meta)
    return sid


def load_meta(upload_folder: str, sid) -> dict | None:
    """Metadata for a session, or None if it is gone or unreadable."""
    directory = session_dir(upload_folder, sid)
    if not directory or not os.path.isdir(directory):
        return None
    try:
        with open(os.path.join(directory, META_NAME), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def source_path(upload_folder: str, sid) -> str | None:
    """Path of the stored upload, or None if the session is unknown."""
    directory = session_dir(upload_folder, sid)
    if not directory or not os.path.isfile(os.path.join(directory, SOURCE_NAME)):
        return None
    return os.path.join(directory, SOURCE_NAME)


def output_path(upload_folder: str, sid) -> str | None:
    """Path the redacted copy is written to, whether or not it exists yet."""
    directory = session_dir(upload_folder, sid)
    return os.path.join(directory, OUTPUT_NAME) if directory else None


def write_output(upload_folder: str, sid, data) -> str:
    """Store the redacted PDF in the session directory.

    Raises:
        ValueError: If the session does not exist.
    """
    directory = session_dir(upload_folder, sid)
    if not directory or not os.path.isdir(directory):
        raise ValueError("Unknown redaction session")

    path = os.path.join(directory, OUTPUT_NAME)
    with open(path, "wb") as f:
        if isinstance(data, (bytes, bytearray)):
            f.write(data)
        else:
            shutil.copyfileobj(data, f, 1024 * 1024)
    return path


def delete_session(upload_folder: str, sid) -> None:
    """Remove a session directory and everything in it. Safe to call twice."""
    directory = session_dir(upload_folder, sid)
    if directory:
        shutil.rmtree(directory, ignore_errors=True)


def cleanup_expired(upload_folder: str, ttl_seconds: int = SESSION_TTL_SECONDS) -> int:
    """Delete session directories older than `ttl_seconds`.

    Age comes from the directory mtime rather than meta.json, so a corrupt
    session is still collectable.

    Returns:
        How many sessions were removed.
    """
    root = os.path.join(upload_folder, SESSIONS_DIRNAME)
    if not os.path.isdir(root):
        return 0

    cutoff = time.time() - ttl_seconds
    removed = 0
    for entry in os.listdir(root):
        if not is_valid_sid(entry):
            continue
        directory = os.path.join(root, entry)
        try:
            if os.path.isdir(directory) and os.path.getmtime(directory) < cutoff:
                shutil.rmtree(directory, ignore_errors=True)
                removed += 1
        except OSError:
            continue
    return removed


def _write_meta(directory: str, meta: dict) -> None:
    with open(os.path.join(directory, META_NAME), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
