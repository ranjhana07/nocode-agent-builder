from __future__ import annotations

from nocode_agent.rag.multi_query import QueryVariants, expand_query
from tests.fakes import FakeChat


def test_original_query_comes_first_and_duplicates_are_dropped() -> None:
    llm = FakeChat({QueryVariants: QueryVariants(queries=["Add a column", "add a column", "append a field to a table", ""])})
    queries = expand_query(llm, "Add a column", count=3)
    assert queries == ["Add a column", "append a field to a table"]


def test_count_caps_the_variants() -> None:
    llm = FakeChat({QueryVariants: QueryVariants(queries=["a one", "b two", "c three", "d four"])})
    assert len(expand_query(llm, "original", count=2)) == 3


def test_llm_failure_falls_back_to_the_original_query() -> None:
    def explode(_messages):
        raise RuntimeError("rate limited")

    llm = FakeChat({QueryVariants: explode})
    assert expand_query(llm, "original") == ["original"]
