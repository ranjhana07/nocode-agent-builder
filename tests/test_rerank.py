from __future__ import annotations

from nocode_agent.config import Settings
from nocode_agent.rag.rerank import LexicalReranker, build_reranker
from nocode_agent.rag.types import Chunk, ScoredChunk


def hit(identifier: str, text: str, score: float = 0.0) -> ScoredChunk:
    return ScoredChunk(Chunk(identifier, text), score)


def test_lexical_reranker_prefers_phrase_matches() -> None:
    hits = [
        hit("loose", "tables have a name and a database and some records", 0.9),
        hit("exact", "create table inside a database with snake case name", 0.1),
    ]
    reranked = LexicalReranker().rerank("create table in a database", hits, 2)
    assert [item.chunk.id for item in reranked] == ["exact", "loose"]


def test_rerank_truncates_to_k() -> None:
    hits = [hit(str(index), f"publish site {index}") for index in range(6)]
    assert len(LexicalReranker().rerank("publish site", hits, 3)) == 3


def test_empty_query_keeps_order() -> None:
    hits = [hit("a", "alpha"), hit("b", "beta")]
    assert [item.chunk.id for item in LexicalReranker().rerank("the of", hits, 5)] == ["a", "b"]


def test_build_reranker_honours_lexical_backend() -> None:
    assert isinstance(build_reranker(Settings(rerank_backend="lexical")), LexicalReranker)


def test_build_reranker_falls_back_when_model_cannot_load(monkeypatch) -> None:
    def broken(*_args, **_kwargs):
        raise OSError("model files missing")

    monkeypatch.setattr("nocode_agent.rag.rerank.CrossEncoderReranker", broken)
    reranker = build_reranker(Settings(rerank_backend="cross-encoder"))
    assert isinstance(reranker, LexicalReranker)
