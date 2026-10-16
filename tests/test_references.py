from __future__ import annotations

from nocode_agent.agent.graph import build_graph
from nocode_agent.agent.planner import IntentDecision
from nocode_agent.agent.references import resolve_references
from nocode_agent.agent.state import BuildPlan, PlanStep, ToolInvocation
from tests.fakes import fake_tools
from tests.graph_helpers import OPERATIONS, chat, make_deps

REFS = {"app": {"id": 7, "name": "Orders"}, "customers": {"id": 12}}


def test_scalar_and_nested_references_are_resolved() -> None:
    errors: list[str] = []
    value = {"app_id": "$app.id", "ids": ["$customers.id", 3], "label": "plain $text", "nested": {"table": "$customers.id"}}
    assert resolve_references(value, REFS, errors) == {
        "app_id": 7,
        "ids": [12, 3],
        "label": "plain $text",
        "nested": {"table": 12},
    }
    assert errors == []


def test_unknown_aliases_and_fields_are_reported() -> None:
    errors: list[str] = []
    resolved = resolve_references({"a": "$missing.id", "b": "$app.colour"}, REFS, errors)
    assert resolved == {"a": "$missing.id", "b": "$app.colour"}
    assert len(errors) == 2
    assert "no object was saved as missing" in errors[0]
    assert "no field colour" in errors[1]


def test_graph_resolves_references_before_validation_and_calls() -> None:
    plan = BuildPlan(
        summary="Orders",
        steps=[
            PlanStep(workflow="create_app", intent="create Orders", bind_as="app"),
            PlanStep(workflow="create_page", intent="home page", bind_as="home"),
        ],
    )
    llm = chat(
        {
            IntentDecision: IntentDecision(kind="build"),
            BuildPlan: plan,
            ToolInvocation: [
                ToolInvocation(workflow="create_app", arguments={"name": "Orders"}),
                ToolInvocation(workflow="create_page", arguments={"app_id": "$app.id", "title": "Home", "slug": "home"}),
            ],
        }
    )
    tools = fake_tools(list(OPERATIONS))
    state = build_graph(make_deps(llm, tools)).invoke({"request": "build orders"})
    assert state["status"] == "completed"
    assert tools["create_page"].invocations == [{"app_id": 1, "title": "Home", "slug": "home"}]


def test_bad_reference_goes_through_the_repair_loop() -> None:
    plan = BuildPlan(
        summary="s",
        steps=[
            PlanStep(workflow="create_app", intent="app", bind_as="app"),
            PlanStep(workflow="create_page", intent="page", bind_as="page"),
        ],
    )
    llm = chat(
        {
            IntentDecision: IntentDecision(kind="build"),
            BuildPlan: plan,
            ToolInvocation: [
                ToolInvocation(workflow="create_app", arguments={"name": "Orders"}),
                ToolInvocation(workflow="create_page", arguments={"app_id": "$ghost.id", "title": "Home", "slug": "home"}),
                ToolInvocation(workflow="create_page", arguments={"app_id": "$app.id", "title": "Home", "slug": "home"}),
            ],
        }
    )
    tools = fake_tools(list(OPERATIONS))
    state = build_graph(make_deps(llm, tools)).invoke({"request": "x"})
    assert state["status"] == "completed"
    assert state["repair_attempts"] == 1
    assert tools["create_page"].invocations == [{"app_id": 1, "title": "Home", "slug": "home"}]


def test_dry_run_validates_without_calling_tools_and_still_chains_ids() -> None:
    plan = BuildPlan(
        summary="s",
        steps=[
            PlanStep(workflow="create_app", intent="app", bind_as="app"),
            PlanStep(workflow="create_page", intent="page", bind_as="page"),
        ],
    )
    llm = chat(
        {
            IntentDecision: IntentDecision(kind="build"),
            BuildPlan: plan,
            ToolInvocation: [
                ToolInvocation(workflow="create_app", arguments={"name": "Orders"}),
                ToolInvocation(workflow="create_page", arguments={"app_id": "$app.id", "title": "Home", "slug": "home"}),
            ],
        }
    )
    tools = fake_tools(list(OPERATIONS))
    state = build_graph(make_deps(llm, tools)).invoke({"request": "x", "dry_run": True})
    assert state["status"] == "completed"
    assert all(tool.invocations == [] for tool in tools.values())
    assert state["results"][1]["arguments"]["app_id"] == 1
    assert state["results"][0]["output"]["dry_run"] is True
