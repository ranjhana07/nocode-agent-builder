from __future__ import annotations

from typing import Any

from nocode_agent.evals.judges import judge_correctness, judge_groundedness
from nocode_agent.evals.metrics import retrieved_expected_source, wrong_tool_call


def score_example(judge_llm: Any, row: dict[str, Any], outputs: dict[str, Any]) -> dict[str, float]:
    scores: dict[str, float] = {}
    grounded = judge_groundedness(judge_llm, outputs.get("answer", ""), outputs.get("contexts", []))
    scores["groundedness"] = grounded.score
    correct = judge_correctness(judge_llm, row["question"], outputs.get("answer", ""), row["reference_answer"])
    scores["correctness"] = correct.score
    wrong = wrong_tool_call(row.get("expected_workflow"), outputs.get("selected_workflow"))
    if wrong is not None:
        scores["wrong_tool_call"] = wrong
    sources = [{"metadata": {"source": source}} for source in outputs.get("context_sources", [])]
    scores["source_hit"] = retrieved_expected_source(row.get("expected_sources", []), sources)
    return scores
