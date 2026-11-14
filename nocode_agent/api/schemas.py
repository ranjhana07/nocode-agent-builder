from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RagQuery(BaseModel):
    query: str = Field(min_length=2)
    k: int = Field(default=5, ge=1, le=20)
    mode: Literal["vector", "hybrid"] = "hybrid"
    rerank: bool = True
    multi_query: bool = False
    doc_type: str | None = None
    workflow: str | None = None


class RagHit(BaseModel):
    id: str
    score: float
    source: str
    section: str
    doc_type: str
    workflow: str
    text: str


class RagResponse(BaseModel):
    queries: list[str]
    hits: list[RagHit]


class AgentRequest(BaseModel):
    request: str = Field(min_length=3)
    thread_id: str | None = None
    intent: Literal["build", "question"] | None = None
    stream: bool = True
    dry_run: bool = False
    plan_only: bool = False


class AgentResponse(BaseModel):
    thread_id: str | None = None
    status: str
    answer: str
    results: list[dict[str, Any]] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)
