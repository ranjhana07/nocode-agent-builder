from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from pathlib import Path

from nocode_agent.config import Settings
from nocode_agent.evals.dataset import read_jsonl
from nocode_agent.rag.eval import QueryOutcome, RetrievalMetrics, SearchFn, rank_queries, summarize, write_results
from nocode_agent.rag.retriever import HybridRetriever

DEPTH = 5


def build_systems(retriever: HybridRetriever, include_multi_query: bool) -> dict[str, SearchFn]:
    systems: dict[str, SearchFn] = {
        "vector only (baseline)": lambda query: retriever.vector_only(query, DEPTH).hits,
        "bm25 only": lambda query: retriever.bm25_index.search(query, DEPTH),
        "hybrid bm25 + vector (rrf)": lambda query: retriever.hybrid(query, DEPTH, multi_query=False, rerank=False).hits,
        "hybrid + rerank": lambda query: retriever.hybrid(query, DEPTH, multi_query=False, rerank=True).hits,
    }
    if include_multi_query:
        systems["hybrid + rerank + multi-query"] = lambda query: retriever.hybrid(query, DEPTH, multi_query=True, rerank=True).hits
    return systems


@dataclass
class RetrievalRun:
    results: list[RetrievalMetrics]
    outcomes: dict[str, list[QueryOutcome]] = field(default_factory=dict)

    def misses(self, system: str, depth: int = DEPTH) -> list[QueryOutcome]:
        return [item for item in self.outcomes[system] if item.rank is None or item.rank > depth]


def group_of(query_id: str) -> str:
    return "intent" if query_id.startswith("i-") else "question"


def run_retrieval_eval(
    retriever: HybridRetriever,
    settings: Settings,
    include_multi_query: bool,
    results_dir: Path | None = None,
    limit: int | None = None,
) -> RetrievalRun:
    queries = read_jsonl(settings.retrieval_queries_path)
    if limit:
        queries = queries[:limit]
    results: list[RetrievalMetrics] = []
    all_outcomes: dict[str, list[QueryOutcome]] = {}
    for name, search in build_systems(retriever, include_multi_query).items():
        outcomes = rank_queries(search, queries)
        all_outcomes[name] = outcomes
        results.append(summarize(name, outcomes, "all"))
        for group in ("question", "intent"):
            subset = [item for item in outcomes if group_of(item.query_id) == group]
            if subset:
                results.append(summarize(name, subset, group))
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
    return RetrievalRun(results, all_outcomes)
