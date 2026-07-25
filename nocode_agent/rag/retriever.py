from __future__ import annotations

from dataclasses import dataclass

from nocode_agent.rag.bm25 import BM25Index
from nocode_agent.rag.filters import MetadataFilter
from nocode_agent.rag.fusion import reciprocal_rank_fusion
from nocode_agent.rag.types import ScoredChunk
from nocode_agent.rag.vector_store import VectorIndex


@dataclass
class RetrievalResult:
    hits: list[ScoredChunk]
    queries: list[str]


class HybridRetriever:
    def __init__(self, vector_index: VectorIndex, bm25_index: BM25Index, rrf_k: int = 60, fetch_k: int = 20) -> None:
        self.vector_index = vector_index
        self.bm25_index = bm25_index
        self.rrf_k = rrf_k
        self.fetch_k = fetch_k

    def vector_only(self, query: str, k: int, metadata_filter: MetadataFilter | None = None) -> RetrievalResult:
        hits = self.vector_index.search(query, k, metadata_filter)
        return RetrievalResult(hits, [query])

    def hybrid(self, query: str, k: int, metadata_filter: MetadataFilter | None = None) -> RetrievalResult:
        dense = self.vector_index.search(query, self.fetch_k, metadata_filter)
        sparse = self.bm25_index.search(query, self.fetch_k, metadata_filter)
        fused = reciprocal_rank_fusion([dense, sparse], k=self.rrf_k)
        return RetrievalResult(fused[:k], [query])
