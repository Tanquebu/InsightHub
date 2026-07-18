"""Rate-limiting tests.

These exercise the exact slowapi wiring used in `app/main.py` /
`app/core/rate_limit.py` (Limiter + SlowAPIMiddleware + RateLimitExceeded
handler) against a small, isolated FastAPI app rather than the real
InsightHub app. Reusing the shared `client`/`unauthenticated_client`
fixtures would tie the test to how many requests every other test in the
suite happens to make against a single global, process-wide limiter — this
keeps the test fast, deterministic, and independent of the rest of the
suite while still proving the mechanism (limiter, middleware, 429 handler)
behaves as configured.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address


def _build_rate_limited_app(limit: str) -> FastAPI:
    app = FastAPI()
    limiter = Limiter(key_func=get_remote_address, storage_uri="memory://", default_limits=[limit])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    return app


def test_requests_within_the_limit_succeed():
    app = _build_rate_limited_app("3/minute")
    with TestClient(app) as client:
        for _ in range(3):
            assert client.get("/ping").status_code == 200


def test_requests_beyond_the_limit_return_429():
    app = _build_rate_limited_app("3/minute")
    with TestClient(app) as client:
        for _ in range(3):
            assert client.get("/ping").status_code == 200
        response = client.get("/ping")
        assert response.status_code == 429
