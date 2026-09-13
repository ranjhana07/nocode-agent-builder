from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from nocode_agent.agent.deps import AgentDeps
from nocode_agent.agent.grader import ChunkGrade, GradeReport
from nocode_agent.config import Settings
from nocode_agent.openapi import load_operations
from nocode_agent.rag.types import Chunk, ScoredChunk
from tests.fakes import FakeChat, fake_tools

OPERATIONS = load_operations(Path("docs/openapi.json"))


def static_retriever(texts: list[str] | None = None):
    chunks = [
        ScoredChunk(Chunk(f"doc#{index}", text, {"source": f"doc{index}.md", "doc_type": "api_spec"}), 1.0)
        for index, text in enumerate(texts or ["create_app creates an app", "create_page adds a page", "publish_site publishes"])
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


def relevant_grader(messages: list[Any]) -> GradeReport:
    count = len(re.findall(r"^\[\d+\]", messages[-1].content, re.M))
    return GradeReport(grades=[ChunkGrade(index=index, score=1.0) for index in range(count)])


def chat(responders: dict[type, Any] | None = None, text: str = "ok") -> FakeChat:
    return FakeChat({GradeReport: relevant_grader, **(responders or {})}, text=text)
