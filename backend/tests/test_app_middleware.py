"""Tests for WSGI middleware: proxy header handling and per-IP rate limiting."""

from utils.rate_limit import rate_limit


class TestProxyFix:
    """nginx terminates TLS and forwards; the app must see the real client."""

    def test_remote_addr_comes_from_forwarded_for(self, app):
        from flask import request as flask_request

        @app.route("/__test/remote-addr")
        def _probe():
            return {"addr": flask_request.remote_addr, "scheme": flask_request.scheme}

        resp = app.test_client().get(
            "/__test/remote-addr", headers={"X-Forwarded-For": "203.0.113.9"}
        )

        assert resp.get_json()["addr"] == "203.0.113.9"

    def test_scheme_comes_from_forwarded_proto(self, app):
        from flask import request as flask_request

        @app.route("/__test/scheme")
        def _probe():
            return {"scheme": flask_request.scheme}

        resp = app.test_client().get(
            "/__test/scheme", headers={"X-Forwarded-Proto": "https"}
        )

        assert resp.get_json()["scheme"] == "https"


class TestRateLimitBuckets:
    def test_limit_is_enforced_per_endpoint(self, app):
        @app.route("/__test/limited-one", methods=["POST"])
        @rate_limit(max_requests=1, window_seconds=60)
        def _limited():
            return {"ok": True}

        client = app.test_client()
        ip = {"X-Forwarded-For": "198.51.100.7"}

        assert client.post("/__test/limited-one", headers=ip).status_code == 200
        assert client.post("/__test/limited-one", headers=ip).status_code == 429

    def test_clients_get_independent_buckets(self, app):
        """One abusive client must not exhaust the limit for everyone else."""
        @app.route("/__test/limited-many", methods=["POST"])
        @rate_limit(max_requests=1, window_seconds=60)
        def _limited():
            return {"ok": True}

        client = app.test_client()
        noisy = {"X-Forwarded-For": "198.51.100.11"}
        quiet = {"X-Forwarded-For": "198.51.100.12"}

        assert client.post("/__test/limited-many", headers=noisy).status_code == 200
        assert client.post("/__test/limited-many", headers=noisy).status_code == 429
        assert client.post("/__test/limited-many", headers=quiet).status_code == 200
