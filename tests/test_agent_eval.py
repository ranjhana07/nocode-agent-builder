from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from nocode_agent.evals.judges import Verdict, judge_correctness, judge_groundedness
from nocode_agent.evals.langsmith_eval import ensure_dataset, example_payloads, make_evaluators
from nocode_agent.evals.local_eval import run_local_eval
from nocode_agent.evals.metrics import mean, retrieved_expected_source, wrong_tool_call
from nocode_agent.evals.scoring import score_example
from tests.fakes import FakeChat

ROW = {
    "id": "q1",
    "category": "workflow_selection",
    "question": "Which API workflow should I call to publish the app?",
    "reference_answer": "Call publish_site.",
    "expected_sources": ["api/publish_site.md"],
    "expected_workflow": "publish_site",
}


def judge(groundedness: float = 1.0, correctness: float = 1.0) -> FakeChat:
    def responder(messages):
        text = messages[0].content
        return Verdict(score=groundedness if "grounded" in text else correctness)

    return FakeChat({Verdict: responder})


@pytest.mark.parametrize(
    "expected, selected, result",
    [("publish_site", "publish_site", 0.0), ("publish_site", "create_app", 1.0), ("publish_site", "", 1.0), (None, "create_app", None)],
)
def test_wrong_tool_call(expected, selected, result) -> None:
    assert wrong_tool_call(expected, selected) == result


def test_source_hit() -> None:
    contexts = [{"metadata": {"source": "api/publish_site.md"}}, {"metadata": {"source": "guides/faq.md"}}]
    assert retrieved_expected_source(["api/publish_site.md"], contexts) == 1.0
    assert retrieved_expected_source(["api/create_app.md"], contexts) == 0.0
    assert retrieved_expected_source(["x"], []) == 0.0


def test_mean_of_empty_is_zero() -> None:
    assert mean([]) == 0.0
    assert mean([1.0, 0.0]) == 0.5


def test_judges_pass_context_and_reference_to_the_prompt() -> None:
    llm = judge()
    judge_groundedness(llm, "the answer", ["excerpt one", "excerpt two"])
    judge_correctness(llm, "the question", "the answer", "the reference")
    prompts = [messages[1].content for _, messages in llm.calls]
    assert "[2] excerpt two" in prompts[0]
    assert "the reference" in prompts[1] and "the question" in prompts[1]


def test_score_example_collects_all_metrics() -> None:
    outputs = {
        "answer": "Call publish_site.",
        "contexts": ["publish_site publishes the app"],
        "context_sources": ["api/publish_site.md"],
        "selected_workflow": "publish_site",
    }
    scores = score_example(judge(0.5, 1.0), ROW, outputs)
    assert scores == {"groundedness": 0.5, "correctness": 1.0, "wrong_tool_call": 0.0, "source_hit": 1.0}


def test_score_example_skips_wrong_tool_without_an_expected_workflow() -> None:
    scores = score_example(judge(), {**ROW, "expected_workflow": None}, {"answer": "a", "contexts": []})
    assert "wrong_tool_call" not in scores


def test_local_eval_averages_per_metric(tmp_path: Path) -> None:
    dataset = tmp_path / "questions.jsonl"
    second = {**ROW, "id": "q2"}
    dataset.write_text("\n".join(__import__("json").dumps(row) for row in (ROW, second)) + "\n", encoding="utf-8")
    answers = iter(["publish_site", "create_app"])

    def target(inputs):
        return {"answer": "x", "contexts": ["c"], "context_sources": [], "selected_workflow": next(answers)}

    summary = run_local_eval(target, judge(), dataset)
    assert summary["examples"] == 2
    assert summary["metrics"]["wrong_tool_call"] == 0.5
    assert summary["metrics"]["groundedness"] == 1.0
    assert len(summary["per_example"]) == 2


class FakeClient:
    def __init__(self, existing: bool) -> None:
        self.existing = existing
        self.created: list[tuple] = []

    def has_dataset(self, dataset_name: str) -> bool:
        return self.existing

    def create_dataset(self, name: str, description: str = ""):
        self.created.append(("dataset", name))
        return SimpleNamespace(id="ds-1")

    def create_examples(self, inputs, outputs, dataset_id) -> None:
        self.created.append(("examples", len(inputs), dataset_id))


def test_example_payloads_split_inputs_and_references() -> None:
    inputs, outputs = example_payloads([ROW])
    assert inputs == [{"question": ROW["question"]}]
    assert outputs[0]["expected_workflow"] == "publish_site"


def test_ensure_dataset_only_uploads_once() -> None:
    fresh = FakeClient(existing=False)
    ensure_dataset(fresh, "nocode-agent-eval", [ROW, ROW])
    assert fresh.created == [("dataset", "nocode-agent-eval"), ("examples", 2, "ds-1")]
    existing = FakeClient(existing=True)
    ensure_dataset(existing, "nocode-agent-eval", [ROW])
    assert existing.created == []


def test_langsmith_evaluators_share_one_judge_pass_per_run() -> None:
    llm = judge()
    evaluators = make_evaluators(llm)
    run = SimpleNamespace(
        id="run-1",
        outputs={"answer": "a", "contexts": ["c"], "context_sources": ["api/publish_site.md"], "selected_workflow": "publish_site"},
    )
    example = SimpleNamespace(outputs=ROW)
    results = {fn.__name__: fn(run, example) for fn in evaluators}
    assert results["wrong_tool_call"] == {"key": "wrong_tool_call", "score": 0.0}
    assert results["groundedness"]["score"] == 1.0
    assert len(llm.calls) == 2
