from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from nocode_agent.rag.filters import MetadataFilter
from nocode_agent.rag.types import Chunk, ScoredChunk

WORD = re.compile(r"[a-z0-9_]+")
STOPWORDS = frozenset("a an and are as at be by for from how in is it of on or that the this to what when which with".split())


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for word in WORD.findall(text.lower()):
        parts = [part for part in word.split("_") if part]
        if "_" in word.strip("_") and len(parts) > 1:
            tokens.append("_".join(parts))
        tokens.extend(part for part in parts if part not in STOPWORDS)
    return tokens


class BM25Index:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = list(chunks)
        corpus = [tokenize(chunk.text) for chunk in self.chunks]
        self.vocabularies = [set(tokens) for tokens in corpus]
        self.model = BM25Okapi(corpus) if corpus else None

    def search(self, query: str, k: int, metadata_filter: MetadataFilter | None = None) -> list[ScoredChunk]:
        if self.model is None:
            return []
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self.model.get_scores(tokens)
        query_terms = set(tokens)
        ranked = sorted(range(len(self.chunks)), key=lambda position: -scores[position])
        results: list[ScoredChunk] = []
        for position in ranked:
            chunk = self.chunks[position]
            if not query_terms & self.vocabularies[position]:
                continue
            if metadata_filter and not metadata_filter.matches(chunk.metadata):
                continue
            results.append(ScoredChunk(chunk, float(scores[position])))
            if len(results) == k:
                break
        return results
