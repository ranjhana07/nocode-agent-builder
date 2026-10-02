from __future__ import annotations

import csv
import json
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from nocode_agent.rag.types import ScoredChunk

SearchFn = Callable[[str], list[ScoredChunk]]


@dataclass
class QueryOutcome:
    query_id: str
    query: str
    rank: int | None
    seconds: float


@dataclass
class RetrievalMetrics:
    system: str
    group: str
    queries: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float
    seconds_per_query: float


def first_relevant_rank(hits: Sequence[ScoredChunk], expected_sources: Sequence[str]) -> int | None:
    expected = set(expected_sources)
    for rank, hit in enumerate(hits, start=1):
        if hit.chunk.source in expected:
            return rank
    return None


def rank_queries(search: SearchFn, queries: Sequence[dict]) -> list[QueryOutcome]:
    outcomes: list[QueryOutcome] = []
    for row in queries:
        started = time.perf_counter()
        hits = search(row["query"])
        elapsed = time.perf_counter() - started
        outcomes.append(
            QueryOutcome(row.get("id", ""), row["query"], first_relevant_rank(hits, row["expected_sources"]), elapsed)
        )
    return outcomes


def summarize(system: str, outcomes: Sequence[QueryOutcome], group: str = "all") -> RetrievalMetrics:
    total = len(outcomes) or 1

    def hit_rate(k: int) -> float:
        return sum(1 for item in outcomes if item.rank is not None and item.rank <= k) / total

    return RetrievalMetrics(
        system=system,
        group=group,
        queries=len(outcomes),
        hit_at_1=hit_rate(1),
        hit_at_3=hit_rate(3),
        hit_at_5=hit_rate(5),
        mrr=sum(1 / item.rank for item in outcomes if item.rank is not None) / total,
        seconds_per_query=sum(item.seconds for item in outcomes) / total,
    )


def evaluate_retrieval(system: str, search: SearchFn, queries: Sequence[dict]) -> RetrievalMetrics:
    return summarize(system, rank_queries(search, queries))


def format_table(results: Sequence[RetrievalMetrics]) -> str:
    header = f"{'system':<34}{'group':<10}{'n':>5}{'hit@1':>8}{'hit@3':>8}{'hit@5':>8}{'mrr':>8}{'s/query':>9}"
    lines = [header, "-" * len(header)]
    for item in results:
        lines.append(
            f"{item.system:<34}{item.group:<10}{item.queries:>5}{item.hit_at_1:>8.3f}{item.hit_at_3:>8.3f}"
            f"{item.hit_at_5:>8.3f}{item.mrr:>8.3f}{item.seconds_per_query:>9.3f}"
        )
    return "\n".join(lines)


def write_results(results: Sequence[RetrievalMetrics], directory: Path, name: str, context: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    rows = [asdict(item) for item in results]
    with (directory / f"{name}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    payload = {"context": context, "results": rows}
    (directory / f"{name}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
