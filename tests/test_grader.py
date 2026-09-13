from __future__ import annotations

import pytest

from nocode_agent.agent.grader import ChunkGrade, GradeReport, decide, grade_documents
from tests.fakes import FakeChat

DOCUMENTS = [{"id": str(index), "text": f"chunk {index}", "metadata": {}} for index in range(4)]


def grades(*scores: float) -> list[ChunkGrade]:
    return [ChunkGrade(index=index, score=score) for index, score in enumerate(scores)]


def test_enough_relevant_chunks_proceed() -> None:
    decision = decide(grades(0.9, 0.7, 0.1), attempts=1, max_attempts=3, threshold=0.5, min_relevant=2)
    assert decision.action == "proceed"
    assert decision.relevant == [0, 1]


def test_nothing_relevant_rewrites_the_query() -> None:
    decision = decide(grades(0.1, 0.2), attempts=1, max_attempts=3, threshold=0.5, min_relevant=2)
    assert decision.action == "rewrite"


def test_partial_context_retrieves_again() -> None:
    decision = decide(grades(0.9, 0.2, 0.1), attempts=1, max_attempts=3, threshold=0.5, min_relevant=2)
    assert decision.action == "retrieve_again"
    assert decision.relevant == [0]


def test_retry_cap_stops_the_loop() -> None:
    assert decide(grades(0.1), attempts=3, max_attempts=3, threshold=0.5, min_relevant=2).action == "give_up"
    assert decide(grades(0.9, 0.1), attempts=3, max_attempts=3, threshold=0.5, min_relevant=2).action == "proceed"


@pytest.mark.parametrize("attempts", [1, 2, 3])
def test_empty_retrieval_never_loops_past_the_cap(attempts: int) -> None:
    action = decide([], attempts=attempts, max_attempts=3, threshold=0.5, min_relevant=1).action
    assert action == ("rewrite" if attempts < 3 else "give_up")


def test_grade_documents_fills_missing_indexes_with_zero() -> None:
    llm = FakeChat({GradeReport: GradeReport(grades=[ChunkGrade(index=1, score=0.8), ChunkGrade(index=9, score=1)])})
    result = grade_documents(llm, "query", DOCUMENTS)
    assert [grade.score for grade in result] == [0.0, 0.8, 0.0, 0.0]


def test_grade_documents_skips_the_llm_for_no_documents() -> None:
    llm = FakeChat({})
    assert grade_documents(llm, "query", []) == []
    assert llm.calls == []
