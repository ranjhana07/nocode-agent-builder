from __future__ import annotations

from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel

from nocode_agent.rag.bm25 import BM25Index
from nocode_agent.rag.filters import MetadataFilter
from nocode_agent.rag.fusion import reciprocal_rank_fusion
from nocode_agent.rag.multi_query import expand_query
from nocode_agent.rag.rerank import Reranker
from nocode_agent.rag.types import ScoredChunk
from nocode_agent.rag.vector_store import VectorIndex


@dataclass
class RetrievalResult:
    hits: list[ScoredChunk]
    queries: list[str]


class HybridRetriever:
    def __init__(
        self,
        vector_index: VectorIndex,
        bm25_index: BM25Index,
        reranker: Reranker | None = None,
        llm: BaseChatModel | None = None,
        rrf_k: int = 60,
        fetch_k: int = 20,
        multi_query_count: int = 3,
    ) -> None:
        self.vector_index = vector_index
        self.bm25_index = bm25_index
        self.reranker = reranker
        self.llm = llm
        self.rrf_k = rrf_k
        self.fetch_k = fetch_k
        self.multi_query_count = multi_query_count

    def vector_only(self, query: str, k: int, metadata_filter: MetadataFilter | None = None) -> RetrievalResult:
        hits = self.vector_index.search(query, k, metadata_filter)
        return RetrievalResult(hits, [query])

    def hybrid(
        self,
        query: str,
        k: int,
        metadata_filter: MetadataFilter | None = None,
        multi_query: bool = True,
        rerank: bool = True,
    ) -> RetrievalResult:
        queries = [query]
        if multi_query and self.llm is not None:
            queries = expand_query(self.llm, query, self.multi_query_count)
        rankings: list[list[ScoredChunk]] = []
        for variant in queries:
            rankings.append(self.vector_index.search(variant, self.fetch_k, metadata_filter))
            rankings.append(self.bm25_index.search(variant, self.fetch_k, metadata_filter))
        fused = reciprocal_rank_fusion(rankings, k=self.rrf_k)
        if rerank and self.reranker is not None:
            return RetrievalResult(self.reranker.rerank(query, fused[: self.fetch_k], k), queries)
        return RetrievalResult(fused[:k], queries)
