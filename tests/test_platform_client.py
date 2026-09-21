from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from nocode_agent.agent.tools import PlatformClient, PlatformError
from nocode_agent.openapi import load_operations

OPERATIONS = load_operations(Path("docs/openapi.json"))


def client_with(responses: list[httpx.Response], sleeps: list[float], max_retries: int = 3) -> PlatformClient:
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        return queue.pop(0)

    http = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://platform")
    return PlatformClient("http://platform", client=http, max_retries=max_retries, sleep=sleeps.append)


def test_retries_follow_retry_after_then_succeed() -> None:
    sleeps: list[float] = []
    client = client_with(
        [httpx.Response(429, headers={"retry-after": "7"}, json={"detail": "slow"}), httpx.Response(201, json={"id": 1})],
        sleeps,
    )
    assert client.call(OPERATIONS["create_app"], {"name": "Orders"}) == {"id": 1}
    assert sleeps == [7.0]


def test_server_errors_back_off_exponentially() -> None:
    sleeps: list[float] = []
    client = client_with(
        [httpx.Response(503, text="down"), httpx.Response(502, text="down"), httpx.Response(201, json={"id": 2})], sleeps
    )
    assert client.call(OPERATIONS["create_app"], {"name": "Orders"}) == {"id": 2}
    assert sleeps == [0.5, 1.0]


def test_gives_up_after_the_retry_budget() -> None:
    sleeps: list[float] = []
    client = client_with([httpx.Response(503, json={"detail": "down"})] * 3, sleeps, max_retries=2)
    with pytest.raises(PlatformError) as caught:
        client.call(OPERATIONS["create_app"], {"name": "Orders"})
    assert caught.value.status_code == 503
    assert len(sleeps) == 2


def test_client_errors_are_not_retried() -> None:
    sleeps: list[float] = []
    client = client_with([httpx.Response(409, json={"detail": "exists"})], sleeps)
    with pytest.raises(PlatformError, match="exists"):
        client.call(OPERATIONS["create_app"], {"name": "Orders"})
    assert sleeps == []


def test_api_key_is_sent_as_a_header() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.headers)
        return httpx.Response(201, json={})

    client = PlatformClient("http://platform", api_key="secret")
    client.client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://platform", headers={"x-api-key": "secret"}
    )
    client.call(OPERATIONS["create_app"], {"name": "Orders"})
    assert seen["x-api-key"] == "secret"
