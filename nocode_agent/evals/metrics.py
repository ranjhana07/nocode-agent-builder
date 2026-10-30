from __future__ import annotations

from typing import Any

def wrong_tool_call(expected_workflow: str | None, selected_workflow: str | None) -> float | None:
    if not expected_workflow:
        return None
    return 0.0 if selected_workflow == expected_workflow else 1.0


def retrieved_expected_source(expected_sources: list[str], contexts: list[dict[str, Any]]) -> float:
    sources = {context.get("metadata", {}).get("source", "") for context in contexts}
    return 1.0 if sources & set(expected_sources) else 0.0


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
