from __future__ import annotations

import re

from nocode_agent.rag.filters import MetadataFilter

WORKFLOW_NAME = re.compile(r"\b([a-z]+(?:_[a-z]+)+)\b")


def known_workflows_from(chunks) -> set[str]:
    return {chunk.workflow for chunk in chunks if chunk.workflow and chunk.workflow != "none"}


def infer_filter(query: str, workflows: set[str], version: str | None = None) -> MetadataFilter:
    mentioned = tuple(sorted({name for name in WORKFLOW_NAME.findall(query.lower()) if name in workflows}))
    return MetadataFilter(workflows=mentioned, version=version)
