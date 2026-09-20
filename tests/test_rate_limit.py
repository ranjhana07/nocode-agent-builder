from __future__ import annotations

from fastapi.testclient import TestClient

from mockplatform.main import create_platform_app
from mockplatform.ratelimit import SlidingWindowLimiter


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_limiter_allows_up_to_the_limit_then_reports_wait() -> None:
    clock = Clock()
    limiter = SlidingWindowLimiter(2, 60, clock)
    assert limiter.check("a") is None
    assert limiter.check("a") is None
    wait = limiter.check("a")
    assert wait is not None and 59 <= wait <= 60


def test_window_slides_and_keys_are_independent() -> None:
    clock = Clock()
    limiter = SlidingWindowLimiter(1, 10, clock)
    assert limiter.check("a") is None
    assert limiter.check("b") is None
    assert limiter.check("a") is not None
    clock.now = 10.5
    assert limiter.check("a") is None


def test_platform_returns_429_with_retry_after() -> None:
    client = TestClient(create_platform_app("sqlite://", rate_limit=3))
    statuses = [client.post("/apps", json={"name": f"App {number}"}).status_code for number in range(5)]
    assert statuses == [201, 201, 201, 429, 429]
    blocked = client.post("/apps", json={"name": "Another"})
    assert blocked.headers["retry-after"].isdigit()
    assert blocked.json() == {"detail": "rate limit exceeded"}


def test_api_keys_get_separate_budgets_and_health_is_exempt() -> None:
    client = TestClient(create_platform_app("sqlite://", rate_limit=1))
    assert client.post("/apps", json={"name": "One"}, headers={"x-api-key": "k1"}).status_code == 201
    assert client.post("/apps", json={"name": "Two"}, headers={"x-api-key": "k2"}).status_code == 201
    assert client.post("/apps", json={"name": "Three"}, headers={"x-api-key": "k1"}).status_code == 429
    assert client.get("/health").status_code == 200
