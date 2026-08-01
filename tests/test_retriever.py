from __future__ import annotations

from nocode_agent.embeddings import HashingEmbeddings
from nocode_agent.rag.bm25 import BM25Index
from nocode_agent.rag.filters import MetadataFilter
from nocode_agent.rag.multi_query import QueryVariants
from nocode_agent.rag.rerank import LexicalReranker
from nocode_agent.rag.retriever import HybridRetriever
from nocode_agent.rag.types import Chunk
from nocode_agent.rag.vector_store import InMemoryVectorIndex
from tests.fakes import FakeChat

CHUNKS = [
    Chunk("seed", "seed_records inserts rows into a table, at most 500 records per call", {"doc_type": "api_spec", "workflow": "seed_records"}),
    Chunk("publish", "publish_site makes the app available in staging or production", {"doc_type": "api_spec", "workflow": "publish_site"}),
    Chunk("auth", "create_auth_flow sets the sign in method and roles of an app", {"doc_type": "api_spec", "workflow": "create_auth_flow"}),
    Chunk("guide", "Guide about forms and how inputs are collected from end users", {"doc_type": "guide", "workflow": "create_form"}),
    Chunk("table", "create_table adds a table to a database using a snake_case name", {"doc_type": "api_spec", "workflow": "create_table"}),
]


def build(llm=None, reranker=None) -> HybridRetriever:
    vectors = InMemoryVectorIndex(HashingEmbeddings())
    vectors.add(CHUNKS)
    return HybridRetriever(vectors, BM25Index(CHUNKS), reranker=reranker, llm=llm, fetch_k=5)


def test_vector_only_returns_k_hits() -> None:
    result = build().vector_only("publish to production", 2)
    assert len(result.hits) == 2
    assert result.queries == ["publish to production"]


def test_hybrid_finds_exact_workflow() -> None:
    result = build().hybrid("how do I publish the site to production", 3, multi_query=False, rerank=False)
    assert result.hits[0].chunk.id == "publish"


def test_multi_query_adds_variants_and_uses_each() -> None:
    llm = FakeChat({QueryVariants: QueryVariants(queries=["sign in roles for an app"])})
    result = build(llm=llm).hybrid("who can log in", 3, rerank=False)
    assert result.queries == ["who can log in", "sign in roles for an app"]
    assert result.hits[0].chunk.id == "auth"


def test_multi_query_skipped_without_llm() -> None:
    assert build().hybrid("seed rows", 3).queries == ["seed rows"]


def test_rerank_reorders_the_fused_list() -> None:
    result = build(reranker=LexicalReranker()).hybrid("create a table in a database", 2, multi_query=False)
    assert result.hits[0].chunk.id == "table"


def test_metadata_filter_is_respected() -> None:
    result = build().hybrid("forms", 5, MetadataFilter(doc_types=("guide",)), multi_query=False, rerank=False)
    assert {hit.chunk.id for hit in result.hits} == {"guide"}
