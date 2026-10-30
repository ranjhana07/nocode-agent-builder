from __future__ import annotations

import csv
import json

from nocode_agent.config import Settings
from nocode_agent.embeddings import HashingEmbeddings
from nocode_agent.evals.retrieval_runner import build_systems, run_retrieval_eval
from nocode_agent.rag.bm25 import BM25Index
from nocode_agent.rag.rerank import LexicalReranker
from nocode_agent.rag.retriever import HybridRetriever
from nocode_agent.rag.types import Chunk
from nocode_agent.rag.vector_store import InMemoryVectorIndex

CHUNKS = [
    Chunk("pub#0", "publish_site publishes the app to staging or production", {"source": "api/publish_site.md"}),
    Chunk("form#0", "create_form creates a form with inputs for end users", {"source": "api/create_form.md"}),
    Chunk("auth#0", "create_auth_flow sets the sign in method", {"source": "api/create_auth_flow.md"}),
]
QUERIES = [
    {"id": "q001", "query": "publish the app to production", "expected_sources": ["api/publish_site.md"]},
    {"id": "i-create_form-1", "query": "build a form with inputs", "expected_sources": ["api/create_form.md"]},
    {"id": "q002", "query": "completely unrelated zebra", "expected_sources": ["api/create_auth_flow.md"]},
]


def retriever() -> HybridRetriever:
    index = InMemoryVectorIndex(HashingEmbeddings())
    index.add(CHUNKS)
    return HybridRetriever(index, BM25Index(CHUNKS), reranker=LexicalReranker(), fetch_k=3)


def settings_for(tmp_path) -> Settings:
    path = tmp_path / "queries.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in QUERIES) + "\n", encoding="utf-8")
    return Settings(retrieval_queries_path=path)


def test_systems_without_llm_exclude_multi_query() -> None:
    assert not any("multi-query" in name for name in build_systems(retriever(), include_multi_query=False))
    assert any("multi-query" in name for name in build_systems(retriever(), include_multi_query=True))


def test_run_reports_all_groups_and_writes_results(tmp_path) -> None:
    run = run_retrieval_eval(retriever(), settings_for(tmp_path), False, tmp_path / "out")
    groups = {(item.system, item.group) for item in run.results}
    assert ("hybrid + rerank", "question") in groups and ("hybrid + rerank", "intent") in groups
    with (tmp_path / "out" / "retrieval.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(run.results)
    payload = json.loads((tmp_path / "out" / "retrieval.json").read_text(encoding="utf-8"))
    assert payload["context"]["queries"] == 3


def test_misses_list_the_unmatched_queries(tmp_path) -> None:
    run = run_retrieval_eval(retriever(), settings_for(tmp_path), False)
    misses = run.misses("hybrid + rerank", depth=1)
    assert [item.query_id for item in misses] == ["q002"]
