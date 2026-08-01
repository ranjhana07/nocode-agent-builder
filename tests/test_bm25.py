from __future__ import annotations

from nocode_agent.rag.bm25 import BM25Index, tokenize
from nocode_agent.rag.filters import MetadataFilter
from nocode_agent.rag.types import Chunk

CHUNKS = [
    Chunk("seed", "seed_records inserts at most 500 records per call", {"doc_type": "api_spec", "workflow": "seed_records"}),
    Chunk("publish", "publish_site publishes the app to staging or production", {"doc_type": "api_spec", "workflow": "publish_site"}),
    Chunk("guide", "Publishing guide explains staging and production environments", {"doc_type": "guide", "workflow": "publish_site"}),
    Chunk("forms", "Forms collect input from end users", {"doc_type": "guide", "workflow": "create_form"}),
]


def test_tokenize_drops_stopwords_and_lowercases() -> None:
    assert tokenize("What is the Maximum number of Records?") == ["maximum", "number", "records"]


def test_exact_term_ranks_first() -> None:
    results = BM25Index(CHUNKS).search("maximum records per call", 3)
    assert results[0].chunk.id == "seed"


def test_scores_are_descending_and_limited() -> None:
    results = BM25Index(CHUNKS).search("production staging", 2)
    assert len(results) == 2
    assert results[0].score >= results[1].score


def test_filter_is_applied_before_limit() -> None:
    results = BM25Index(CHUNKS).search("staging production", 5, MetadataFilter(doc_types=("guide",)))
    assert [hit.chunk.id for hit in results] == ["guide"]


def test_no_matching_tokens_returns_nothing() -> None:
    assert BM25Index(CHUNKS).search("zebra", 3) == []
    assert BM25Index(CHUNKS).search("the of", 3) == []


def test_empty_index() -> None:
    assert BM25Index([]).search("anything", 3) == []
