from __future__ import annotations

from nocode_agent.rag.query_filters import infer_filter, known_workflows_from
from nocode_agent.rag.types import Chunk

WORKFLOWS = {"create_app", "create_table", "publish_site"}


def test_workflow_names_in_the_query_become_a_filter() -> None:
    result = infer_filter("what does create_table return when publish_site fails", WORKFLOWS)
    assert result.workflows == ("create_table", "publish_site")


def test_unknown_snake_case_words_are_ignored() -> None:
    assert infer_filter("set primary_key to id", WORKFLOWS).workflows == ()


def test_version_is_passed_through() -> None:
    assert infer_filter("anything", WORKFLOWS, "1.4").version == "1.4"


def test_known_workflows_skip_none() -> None:
    chunks = [Chunk("a", "x", {"workflow": "create_app"}), Chunk("b", "y", {"workflow": "none"}), Chunk("c", "z", {})]
    assert known_workflows_from(chunks) == {"create_app"}
