from __future__ import annotations

import logging
from typing import Protocol

from nocode_agent.config import Settings, get_settings
from nocode_agent.rag.bm25 import tokenize
from nocode_agent.rag.types import ScoredChunk

logger = logging.getLogger(__name__)


class Reranker(Protocol):
    def rerank(self, query: str, hits: list[ScoredChunk], k: int) -> list[ScoredChunk]: ...


class LexicalReranker:
    def rerank(self, query: str, hits: list[ScoredChunk], k: int) -> list[ScoredChunk]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return hits[:k]
        query_set = set(query_tokens)
        query_bigrams = set(zip(query_tokens, query_tokens[1:]))
        rescored: list[ScoredChunk] = []
        for hit in hits:
            tokens = tokenize(hit.chunk.text)
            token_set = set(tokens)
            coverage = len(query_set & token_set) / len(query_set)
            bigrams = set(zip(tokens, tokens[1:]))
            phrase = len(query_bigrams & bigrams) / len(query_bigrams) if query_bigrams else 0.0
            rescored.append(ScoredChunk(hit.chunk, coverage + 0.5 * phrase))
        rescored.sort(key=lambda scored: -scored.score)
        return rescored[:k]


class CrossEncoderReranker:
    def __init__(self, model_name: str, batch_size: int = 16) -> None:
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(model_name)
        self.batch_size = batch_size

    def rerank(self, query: str, hits: list[ScoredChunk], k: int) -> list[ScoredChunk]:
        if not hits:
            return []
        pairs = [(query, hit.chunk.text) for hit in hits]
        scores = self.model.predict(pairs, batch_size=self.batch_size, show_progress_bar=False)
        rescored = [ScoredChunk(hit.chunk, float(score)) for hit, score in zip(hits, scores)]
        rescored.sort(key=lambda scored: -scored.score)
        return rescored[:k]


def build_reranker(settings: Settings | None = None) -> Reranker:
    settings = settings or get_settings()
    if settings.rerank_backend == "lexical":
        return LexicalReranker()
    try:
        return CrossEncoderReranker(settings.rerank_model)
    except Exception as error:
        logger.warning("cross-encoder unavailable (%s), using lexical reranker", error)
        return LexicalReranker()
