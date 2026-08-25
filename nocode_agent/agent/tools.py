from __future__ import annotations

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


class PlatformClient:
    def __init__(self, base_url: str, client: httpx.Client | None = None, timeout: float = 15.0) -> None:
        self.client = client or httpx.Client(base_url=base_url, timeout=timeout)

    def call(self, operation: Operation, arguments: dict[str, Any]) -> dict[str, Any]:
        path = operation.path
        body = dict(arguments)
        for name in operation.path_params:
            path = path.replace("{" + name + "}", str(body.pop(name)))
        response = self.client.request(operation.method, path, json=body or None)
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
