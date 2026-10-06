from __future__ import annotations

import pytest
from langchain_core.embeddings import Embeddings

from nocode_agent.config import Settings
from nocode_agent.embedding_cache import CachedEmbeddings
from nocode_agent.embeddings import HashingEmbeddings, build_embeddings


class CountingEmbeddings(Embeddings):
    def __init__(self) -> None:
        self.embedded: list[str] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.embedded.extend(texts)
        return [[float(len(text)), 1.0] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def test_repeated_texts_are_served_from_the_cache(tmp_path) -> None:
    inner = CountingEmbeddings()
    cached = CachedEmbeddings(inner, tmp_path / "cache.db", "model-a")
    first = cached.embed_documents(["alpha", "beta"])
    second = cached.embed_documents(["beta", "alpha", "gamma"])
    assert second[:2] == [first[1], first[0]]
    assert inner.embedded == ["alpha", "beta", "gamma"]
    assert (cached.hits, cached.misses) == (2, 3)


def test_cache_survives_reopening_and_is_namespaced(tmp_path) -> None:
    path = tmp_path / "cache.db"
    CachedEmbeddings(CountingEmbeddings(), path, "model-a").embed_documents(["alpha"])
    inner = CountingEmbeddings()
    CachedEmbeddings(inner, path, "model-a").embed_documents(["alpha"])
    assert inner.embedded == []
    other_model = CountingEmbeddings()
    CachedEmbeddings(other_model, path, "model-b").embed_documents(["alpha"])
    assert other_model.embedded == ["alpha"]


def test_duplicate_texts_in_one_call(tmp_path) -> None:
    inner = CountingEmbeddings()
    cached = CachedEmbeddings(inner, tmp_path / "cache.db", "m")
    vectors = cached.embed_documents(["same", "same"])
    assert vectors[0] == vectors[1]


def test_build_embeddings_wraps_when_a_cache_path_is_set(tmp_path) -> None:
    settings = Settings(embedding_backend="hashing", embedding_cache_path=tmp_path / "c.db")
    assert isinstance(build_embeddings(settings), CachedEmbeddings)
    assert isinstance(build_embeddings(Settings(embedding_backend="hashing")), HashingEmbeddings)


def test_unknown_backend_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_embeddings(Settings(embedding_backend="word2vec"))
