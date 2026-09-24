"""Tests for the PDF redaction session store (utils/redact_session.py)."""

import json
import os
import time

import pytest

from utils.redact_session import (
    SESSION_TTL_SECONDS,
    cleanup_expired,
    create_session,
    delete_session,
    is_valid_sid,
    load_meta,
    session_dir,
)


@pytest.fixture
def root(tmp_dir):
    """A stand-in for Config.UPLOAD_FOLDER."""
    return tmp_dir


class TestCreateSession:
    def test_creates_a_session_directory_with_source_and_meta(self, root):
        sid = create_session(root, "report.pdf", b"%PDF-1.4 fake", {"page_count": 2})

        assert is_valid_sid(sid)
        directory = session_dir(root, sid)
        assert os.path.isfile(os.path.join(directory, "source.pdf"))
        assert os.path.isfile(os.path.join(directory, "meta.json"))

    def test_meta_round_trips(self, root):
        sid = create_session(root, "报告.pdf", b"%PDF-1.4 fake", {"page_count": 7})

        meta = load_meta(root, sid)

        assert meta["page_count"] == 7
        assert meta["original_name"] == "报告.pdf"
        assert meta["created_at"] <= time.time()

    def test_two_sessions_do_not_collide(self, root):
        a = create_session(root, "a.pdf", b"%PDF-1.4 a", {"page_count": 1})
        b = create_session(root, "b.pdf", b"%PDF-1.4 b", {"page_count": 1})

        assert a != b
        assert load_meta(root, a)["page_count"] == 1


class TestLookup:
    def test_unknown_session_returns_none(self, root):
        assert load_meta(root, "0" * 32) is None

    def test_malformed_meta_returns_none(self, root):
        sid = create_session(root, "a.pdf", b"%PDF-1.4 a", {"page_count": 1})
        with open(os.path.join(session_dir(root, sid), "meta.json"), "w") as f:
            f.write("{not json")

        assert load_meta(root, sid) is None

    @pytest.mark.parametrize(
        "sid",
        ["", "..", "../etc", "a" * 31, "A" * 32, "z" * 32, "0" * 32 + "/x", None],
    )
    def test_rejects_sids_that_could_escape_the_root(self, sid):
        assert not is_valid_sid(sid)

    def test_session_dir_is_none_for_a_bad_sid(self, root):
        assert session_dir(root, "../../etc") is None


class TestDelete:
    def test_removes_the_whole_session_directory(self, root):
        sid = create_session(root, "a.pdf", b"%PDF-1.4 a", {"page_count": 1})
        directory = session_dir(root, sid)

        delete_session(root, sid)

        assert not os.path.isdir(directory)
        assert load_meta(root, sid) is None

    def test_is_idempotent(self, root):
        sid = create_session(root, "a.pdf", b"%PDF-1.4 a", {"page_count": 1})
        delete_session(root, sid)

        delete_session(root, sid)


class TestCleanup:
    def test_removes_only_sessions_past_the_ttl(self, root):
        fresh = create_session(root, "new.pdf", b"%PDF-1.4 n", {"page_count": 1})
        stale = create_session(root, "old.pdf", b"%PDF-1.4 o", {"page_count": 1})
        old = time.time() - SESSION_TTL_SECONDS - 60
        os.utime(session_dir(root, stale), (old, old))

        removed = cleanup_expired(root)

        assert removed == 1
        assert os.path.isdir(session_dir(root, fresh))
        assert not os.path.isdir(session_dir(root, stale))

    def test_ignores_other_entries_in_the_upload_folder(self, root):
        os.makedirs(os.path.join(root, "thumbs_abc"), exist_ok=True)
        stray = os.path.join(root, "loose.pdf")
        open(stray, "wb").write(b"%PDF-1.4")

        removed = cleanup_expired(root)

        assert removed == 0
        assert os.path.isfile(stray)
        assert os.path.isdir(os.path.join(root, "thumbs_abc"))

    def test_missing_root_is_not_an_error(self, tmp_dir):
        assert cleanup_expired(os.path.join(tmp_dir, "nope")) == 0
