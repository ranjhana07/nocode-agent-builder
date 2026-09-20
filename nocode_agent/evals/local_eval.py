from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

from nocode_agent.evals.dataset import read_jsonl
from nocode_agent.evals.metrics import mean
from nocode_agent.evals.scoring import score_example


def run_local_eval(
    target: Callable[[dict], dict],
    judge_llm: Any,
    dataset_path: Path,
    limit: int | None = None,
) -> dict[str, Any]:
    rows = read_jsonl(dataset_path)[:limit]
    per_example: list[dict[str, Any]] = []
    by_metric: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        outputs = target({"question": row["question"]})
        scores = score_example(judge_llm, row, outputs)
        for metric, value in scores.items():
            by_metric[metric].append(value)
        per_example.append({"id": row["id"], "category": row["category"], "scores": scores, "answer": outputs["answer"]})
    return {
        "examples": len(rows),
        "metrics": {metric: mean(values) for metric, values in by_metric.items()},
        "per_example": per_example,
    }


def write_summary(summary: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
