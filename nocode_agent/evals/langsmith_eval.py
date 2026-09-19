from __future__ import annotations

from typing import Any, Callable

from nocode_agent.evals.dataset import read_jsonl
from nocode_agent.evals.scoring import score_example


def example_payloads(rows: list[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
    inputs = [{"question": row["question"]} for row in rows]
    outputs = [
        {
            "reference_answer": row["reference_answer"],
            "expected_workflow": row.get("expected_workflow"),
            "expected_sources": row.get("expected_sources", []),
            "category": row["category"],
            "question": row["question"],
        }
        for row in rows
    ]
    return inputs, outputs


def ensure_dataset(client: Any, name: str, rows: list[dict[str, Any]]) -> None:
    if client.has_dataset(dataset_name=name):
        return
    dataset = client.create_dataset(name, description="Questions over the Nocode platform documentation")
    inputs, outputs = example_payloads(rows)
    client.create_examples(inputs=inputs, outputs=outputs, dataset_id=dataset.id)


def make_evaluators(judge_llm: Any) -> list[Callable[[Any, Any], dict[str, Any]]]:
    cache: dict[str, dict[str, float]] = {}

    def scored(run: Any, example: Any) -> dict[str, float]:
        key = str(run.id)
        if key not in cache:
            cache[key] = score_example(judge_llm, example.outputs, run.outputs or {})
        return cache[key]

    def evaluator(metric: str) -> Callable[[Any, Any], dict[str, Any]]:
        def evaluate_metric(run: Any, example: Any) -> dict[str, Any]:
            value = scored(run, example).get(metric)
            return {"key": metric, "score": value}

        evaluate_metric.__name__ = metric
        return evaluate_metric

    return [evaluator(metric) for metric in ("groundedness", "correctness", "wrong_tool_call", "source_hit")]


def run_langsmith_eval(
    target: Callable[[dict], dict],
    judge_llm: Any,
    dataset_path,
    dataset_name: str,
    experiment_prefix: str,
    limit: int | None = None,
):
    from langsmith import Client, evaluate

    client = Client()
    rows = read_jsonl(dataset_path)
    ensure_dataset(client, dataset_name, rows)
    data = list(client.list_examples(dataset_name=dataset_name, limit=limit)) if limit else dataset_name
    return evaluate(
        target,
        data=data,
        evaluators=make_evaluators(judge_llm),
        experiment_prefix=experiment_prefix,
        max_concurrency=4,
    )
