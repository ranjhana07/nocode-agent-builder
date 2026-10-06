from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

from langchain_core.embeddings import Embeddings

from nocode_agent.config import Settings, get_settings

TOKEN = re.compile(r"[a-z0-9]+")


class HashingEmbeddings(Embeddings):
    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = TOKEN.findall(text.lower())
        grams = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
        for gram in grams:
            digest = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            sign = 1.0 if value & 1 else -1.0
            vector[(value >> 1) % self.dimensions] += sign
        norm = math.sqrt(sum(component * component for component in vector)) or 1.0
        return [component / norm for component in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model_name: str, batch_size: int = 32) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.batch_size = batch_size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(
            texts, batch_size=self.batch_size, normalize_embeddings=True, show_progress_bar=False
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class EmbeddingFactory(Protocol):
    def __call__(self, settings: Settings) -> Embeddings: ...


def build_embeddings(settings: Settings | None = None) -> Embeddings:
    settings = settings or get_settings()
    if settings.embedding_backend == "hashing":
        embeddings: Embeddings = HashingEmbeddings()
    elif settings.embedding_backend == "sentence-transformers":
        embeddings = SentenceTransformerEmbeddings(settings.embedding_model)
    else:
        raise ValueError(f"unknown embedding backend {settings.embedding_backend!r}")
    if settings.embedding_cache_path:
        from nocode_agent.embedding_cache import CachedEmbeddings

        return CachedEmbeddings(embeddings, settings.embedding_cache_path, settings.embedding_model)
    return embeddings
