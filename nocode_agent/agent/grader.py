from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

from nocode_agent.llm import structured_call

GRADER_SYSTEM = """You grade retrieved documentation chunks for a question about a no-code platform API.
Score each chunk from 0 to 1: 1 means it directly contains what is needed to answer or to call the right workflow,
0.5 means related but incomplete, 0 means irrelevant. Return one grade per chunk using the given index."""


class ChunkGrade(BaseModel):
    index: int = Field(description="Index of the chunk in the provided list")
    score: float = Field(ge=0, le=1, description="Relevance from 0 to 1")
    reason: str = Field(default="", description="Short justification")


class GradeReport(BaseModel):
    grades: list[ChunkGrade]


Action = Literal["proceed", "rewrite", "retrieve_again", "give_up"]


@dataclass
class Decision:
    action: Action
    relevant: list[int] = field(default_factory=list)


def grade_documents(llm: Any, query: str, documents: list[dict[str, Any]]) -> list[ChunkGrade]:
    if not documents:
        return []
    listing = "\n\n".join(f"[{index}] {document['text'][:700]}" for index, document in enumerate(documents))
    report = structured_call(llm, GradeReport, GRADER_SYSTEM, f"Question: {query}\n\nChunks:\n{listing}")
    by_index = {grade.index: grade for grade in report.grades if 0 <= grade.index < len(documents)}
    return [by_index.get(index, ChunkGrade(index=index, score=0.0)) for index in range(len(documents))]


def decide(grades: list[ChunkGrade], attempts: int, max_attempts: int, threshold: float, min_relevant: int) -> Decision:
    relevant = [grade.index for grade in grades if grade.score >= threshold]
    if len(relevant) >= min_relevant:
        return Decision("proceed", relevant)
    if not relevant:
        return Decision("rewrite", relevant)
    return Decision("retrieve_again", relevant)
