from __future__ import annotations

import os
import platform
from pathlib import Path

from nocode_agent.config import Settings
from nocode_agent.evals.dataset import read_jsonl
from nocode_agent.rag.eval import RetrievalMetrics, SearchFn, evaluate_retrieval, write_results
from nocode_agent.rag.retriever import HybridRetriever

DEPTH = 5


def build_systems(retriever: HybridRetriever, include_multi_query: bool) -> dict[str, SearchFn]:
    systems: dict[str, SearchFn] = {
        "vector only (baseline)": lambda query: retriever.vector_only(query, DEPTH).hits,
        "hybrid bm25 + vector (rrf)": lambda query: retriever.hybrid(query, DEPTH, multi_query=False, rerank=False).hits,
        "hybrid + rerank": lambda query: retriever.hybrid(query, DEPTH, multi_query=False, rerank=True).hits,
    }
    if include_multi_query:
        systems["hybrid + rerank + multi-query"] = lambda query: retriever.hybrid(query, DEPTH, multi_query=True, rerank=True).hits
    return systems


def run_retrieval_eval(
    retriever: HybridRetriever,
    settings: Settings,
    include_multi_query: bool,
    results_dir: Path | None = None,
    limit: int | None = None,
) -> list[RetrievalMetrics]:
    queries = read_jsonl(settings.retrieval_queries_path)
    if limit:
        queries = queries[:limit]
    results = [
        evaluate_retrieval(name, search, queries)
        for name, search in build_systems(retriever, include_multi_query).items()
    ]
    if results_dir:
        context = {
            "queries": len(queries),
            "embedding_model": settings.embedding_model,
            "rerank_model": settings.rerank_model,
            "multi_query": include_multi_query,
            "python": platform.python_version(),
            "machine": platform.processor() or platform.machine(),
            "cpu_count": os.cpu_count(),
        }
        write_results(results, results_dir, "retrieval", context)
    return results
