from __future__ import annotations

import pytest

from nocode_agent.rag.fusion import reciprocal_rank_fusion
from nocode_agent.rag.types import Chunk, ScoredChunk


def ranking(*ids: str) -> list[ScoredChunk]:
    return [ScoredChunk(Chunk(identifier, identifier), float(len(ids) - position)) for position, identifier in enumerate(ids)]


def fused_ids(*rankings: list[ScoredChunk], **options) -> list[str]:
    return [hit.chunk.id for hit in reciprocal_rank_fusion(list(rankings), **options)]


def test_documents_in_both_rankings_beat_single_list_documents() -> None:
    assert fused_ids(ranking("a", "b", "c"), ranking("d", "b", "e"))[0] == "b"


def test_single_ranking_keeps_order() -> None:
    assert fused_ids(ranking("a", "b", "c")) == ["a", "b", "c"]


def test_scores_follow_the_rrf_formula() -> None:
    fused = reciprocal_rank_fusion([ranking("a", "b"), ranking("b", "a")], k=10)
    by_id = {hit.chunk.id: hit.score for hit in fused}
    assert by_id["a"] == pytest.approx(1 / 11 + 1 / 12)
    assert by_id["a"] == pytest.approx(by_id["b"])


def test_ties_break_on_chunk_id_for_stable_output() -> None:
    assert fused_ids(ranking("b", "a"), ranking("a", "b")) == ["a", "b"]


def test_weights_shift_the_outcome() -> None:
    unweighted = fused_ids(ranking("a"), ranking("b"))
    weighted = fused_ids(ranking("a"), ranking("b"), weights=[1.0, 3.0])
    assert unweighted == ["a", "b"]
    assert weighted == ["b", "a"]


def test_weights_length_is_checked() -> None:
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([ranking("a")], weights=[1.0, 2.0])


def test_empty_rankings() -> None:
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []
