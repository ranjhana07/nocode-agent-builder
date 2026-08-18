from __future__ import annotations

import pytest

from nocode_agent.rag.eval import evaluate_retrieval, first_relevant_rank, format_table
from nocode_agent.rag.types import Chunk, ScoredChunk


def hits(*sources: str) -> list[ScoredChunk]:
    return [ScoredChunk(Chunk(f"{source}#{index}", "", {"source": source}), 1.0) for index, source in enumerate(sources)]


def test_first_relevant_rank() -> None:
    assert first_relevant_rank(hits("a.md", "b.md", "c.md"), ["c.md"]) == 3
    assert first_relevant_rank(hits("a.md"), ["z.md"]) is None
    assert first_relevant_rank(hits("a.md", "b.md"), ["b.md", "a.md"]) == 1


def test_metrics_over_a_small_query_set() -> None:
    answers = {
        "first": hits("a.md", "b.md"),
        "third": hits("x.md", "y.md", "a.md"),
        "miss": hits("x.md", "y.md"),
        "late": hits("x.md", "x.md", "x.md", "x.md", "a.md"),
    }
    queries = [{"query": name, "expected_sources": ["a.md"]} for name in answers]
    metrics = evaluate_retrieval("fake", lambda query: answers[query], queries)
    assert metrics.queries == 4
    assert metrics.hit_at_1 == pytest.approx(0.25)
    assert metrics.hit_at_3 == pytest.approx(0.5)
    assert metrics.hit_at_5 == pytest.approx(0.75)
    assert metrics.mrr == pytest.approx((1 + 1 / 3 + 0 + 1 / 5) / 4)


def test_table_lists_every_system() -> None:
    metrics = evaluate_retrieval("system-one", lambda query: hits("a.md"), [{"query": "q", "expected_sources": ["a.md"]}])
    table = format_table([metrics])
    assert "system-one" in table
    assert "1.000" in table
