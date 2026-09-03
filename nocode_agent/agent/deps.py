from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models import BaseChatModel

from nocode_agent.config import Settings
from nocode_agent.openapi import Operation
from nocode_agent.rag.types import ScoredChunk

RetrieverFn = Callable[[str, int, bool], list[ScoredChunk]]


@dataclass
class AgentDeps:
    llm: BaseChatModel
    operations: dict[str, Operation]
    tools: dict[str, Any]
    docs_retriever: RetrieverFn
    spec_retriever: RetrieverFn
    settings: Settings
