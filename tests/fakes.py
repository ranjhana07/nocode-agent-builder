from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

Responder = Callable[[list[Any]], Any]


class FakeStructured:
    def __init__(self, owner: FakeChat, schema: type) -> None:
        self.owner = owner
        self.schema = schema

    def invoke(self, messages: list[Any]) -> Any:
        self.owner.calls.append((self.schema, messages))
        responder = self.owner.responders[self.schema]
        if isinstance(responder, list):
            if not responder:
                raise AssertionError(f"no scripted response left for {self.schema.__name__}")
            item = responder.pop(0)
        else:
            item = responder
        return item(messages) if callable(item) else item


class FakeChat:
    def __init__(self, responders: dict[type, Any] | None = None, text: str = "ok") -> None:
        self.responders = responders or {}
        self.text = text
        self.calls: list[tuple[type | None, list[Any]]] = []

    def with_structured_output(self, schema: type) -> FakeStructured:
        return FakeStructured(self, schema)

    def invoke(self, messages: list[Any]) -> Any:
        self.calls.append((None, messages))
        return SimpleNamespace(content=self.text)

    def calls_for(self, schema: type) -> int:
        return sum(1 for called, _ in self.calls if called is schema)


class FakeTool:
    def __init__(self, name: str, failures: list[Exception] | None = None) -> None:
        self.name = name
        self.failures = failures or []
        self.invocations: list[dict[str, Any]] = []

    def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self.invocations.append(arguments)
        if self.failures:
            raise self.failures.pop(0)
        return {"id": len(self.invocations), "workflow": self.name, **arguments}


def fake_tools(names: list[str], failures: dict[str, list[Exception]] | None = None) -> dict[str, FakeTool]:
    failures = failures or {}
    return {name: FakeTool(name, failures.get(name)) for name in names}
