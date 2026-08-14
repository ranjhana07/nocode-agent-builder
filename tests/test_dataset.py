from __future__ import annotations

from collections import Counter
from pathlib import Path

from nocode_agent.evals.dataset import build_examples, build_retrieval_queries, read_jsonl

DOCS = Path("docs")


def test_dataset_has_150_unique_questions() -> None:
    examples = build_examples(DOCS)
    assert len(examples) == 150
    assert len({example.question for example in examples}) == 150
    assert len({example.id for example in examples}) == 150


def test_generation_is_deterministic() -> None:
    first = [example.question for example in build_examples(DOCS)]
    second = [example.question for example in build_examples(DOCS)]
    assert first == second


def test_every_example_points_at_existing_docs() -> None:
    for example in build_examples(DOCS):
        assert example.reference_answer
        for source in example.expected_sources:
            assert (DOCS / source).exists(), source


def test_selection_questions_carry_the_expected_workflow() -> None:
    examples = build_examples(DOCS)
    selection = [example for example in examples if example.category == "workflow_selection"]
    assert len(selection) >= 25
    assert all(example.expected_workflow for example in selection)
    assert len({example.expected_workflow for example in selection}) == 12


def test_retrieval_queries_extend_the_questions() -> None:
    examples = build_examples(DOCS)
    queries = build_retrieval_queries(DOCS, examples)
    assert len(queries) == 150 + 60
    assert Counter(query["id"][0] for query in queries)["i"] == 60


def test_committed_jsonl_matches_the_generator() -> None:
    committed = read_jsonl(Path("data/eval/questions.jsonl"))
    assert [row["question"] for row in committed] == [example.question for example in build_examples(DOCS)]
