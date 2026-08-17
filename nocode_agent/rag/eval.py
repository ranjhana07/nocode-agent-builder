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
class RetrievalMetrics:
    system: str
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


def evaluate_retrieval(system: str, search: SearchFn, queries: Sequence[dict], ks: Sequence[int] = (1, 3, 5)) -> RetrievalMetrics:
    ranks: list[int | None] = []
    started = time.perf_counter()
    for row in queries:
        ranks.append(first_relevant_rank(search(row["query"]), row["expected_sources"]))
    elapsed = time.perf_counter() - started
    total = len(ranks) or 1

    def hit_rate(k: int) -> float:
        return sum(1 for rank in ranks if rank is not None and rank <= k) / total

    reciprocal = sum(1 / rank for rank in ranks if rank is not None) / total
    return RetrievalMetrics(
        system=system,
        queries=len(ranks),
        hit_at_1=hit_rate(ks[0]),
        hit_at_3=hit_rate(ks[1]),
        hit_at_5=hit_rate(ks[2]),
        mrr=reciprocal,
        seconds_per_query=elapsed / total,
    )


def format_table(results: Sequence[RetrievalMetrics]) -> str:
    header = f"{'system':<34}{'n':>5}{'hit@1':>8}{'hit@3':>8}{'hit@5':>8}{'mrr':>8}{'s/query':>9}"
    lines = [header, "-" * len(header)]
    for item in results:
        lines.append(
            f"{item.system:<34}{item.queries:>5}{item.hit_at_1:>8.3f}{item.hit_at_3:>8.3f}"
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
