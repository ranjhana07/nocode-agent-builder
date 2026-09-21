from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx
from langchain_core.tools import StructuredTool

from nocode_agent.openapi import Operation


class PlatformError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"{status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


RETRYABLE = {429, 500, 502, 503, 504}


class PlatformClient:
    def __init__(
        self,
        base_url: str,
        client: httpx.Client | None = None,
        timeout: float = 15.0,
        api_key: str | None = None,
        max_retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        headers = {"x-api-key": api_key} if api_key else {}
        self.client = client or httpx.Client(base_url=base_url, timeout=timeout, headers=headers)
        self.max_retries = max_retries
        self.sleep = sleep

    def send(self, method: str, path: str, body: dict[str, Any] | None) -> httpx.Response:
        for attempt in range(self.max_retries + 1):
            response = self.client.request(method, path, json=body)
            if response.status_code not in RETRYABLE or attempt == self.max_retries:
                return response
            delay = response.headers.get("retry-after")
            self.sleep(float(delay) if delay and delay.isdigit() else 0.5 * 2**attempt)
        return response

    def call(self, operation: Operation, arguments: dict[str, Any]) -> dict[str, Any]:
        path = operation.path
        body = dict(arguments)
        for name in operation.path_params:
            path = path.replace("{" + name + "}", str(body.pop(name)))
        response = self.send(operation.method, path, body or None)
        if response.is_error:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise PlatformError(response.status_code, str(detail))
        return response.json()


def build_tools(operations: dict[str, Operation], client: PlatformClient) -> list[StructuredTool]:
    tools: list[StructuredTool] = []
    for operation in operations.values():
        tools.append(
            StructuredTool.from_function(
                func=make_caller(operation, client),
                name=operation.name,
                description=f"{operation.summary or operation.name} ({operation.method} {operation.path})",
                args_schema=operation.schema,
                infer_schema=False,
            )
        )
    return tools


def make_caller(operation: Operation, client: PlatformClient) -> Callable[..., dict[str, Any]]:
    def call_workflow(**arguments: Any) -> dict[str, Any]:
        return client.call(operation, arguments)

    return call_workflow


def tool_registry(tools: list[StructuredTool]) -> dict[str, StructuredTool]:
    return {tool.name: tool for tool in tools}
