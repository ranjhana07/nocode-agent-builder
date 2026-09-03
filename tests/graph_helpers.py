from __future__ import annotations

from pathlib import Path
from typing import Any

from nocode_agent.agent.deps import AgentDeps
from nocode_agent.config import Settings
from nocode_agent.openapi import load_operations
from nocode_agent.rag.types import Chunk, ScoredChunk
from tests.fakes import FakeChat, fake_tools

OPERATIONS = load_operations(Path("docs/openapi.json"))


def static_retriever(texts: list[str] | None = None):
    chunks = [
        ScoredChunk(Chunk(f"doc#{index}", text, {"source": f"doc{index}.md", "doc_type": "api_spec"}), 1.0)
        for index, text in enumerate(texts or ["create_app creates an app"])
    ]
    return lambda query, k, widen: chunks[:k]


def make_deps(llm: FakeChat, tools: dict[str, Any] | None = None, retriever=None, **settings: Any) -> AgentDeps:
    retriever = retriever or static_retriever()
    return AgentDeps(
        llm=llm,
        operations=OPERATIONS,
        tools=tools if tools is not None else fake_tools(list(OPERATIONS)),
        docs_retriever=retriever,
        spec_retriever=retriever,
        settings=Settings(**settings),
    )
