from __future__ import annotations

from nocode_agent.agent.graph import build_graph
from nocode_agent.agent.plan_checker import check_plan
from nocode_agent.agent.planner import IntentDecision
from nocode_agent.agent.state import BuildPlan, PlanStep, ToolInvocation
from tests.graph_helpers import chat, make_deps


def steps(*names: str) -> list[PlanStep]:
    return [PlanStep(workflow=name, intent=name) for name in names]


def test_valid_plan_has_no_problems() -> None:
    plan = steps("create_app", "create_page", "add_component", "create_database", "create_table", "add_field", "seed_records", "publish_site")
    assert check_plan(plan) == []


def test_missing_prerequisites_are_named() -> None:
    problems = check_plan(steps("create_table", "create_app"))
    assert problems == ["step 1 (create_table) needs create_database to run earlier"]


def test_seed_needs_fields() -> None:
    plan = steps("create_app", "create_database", "create_table", "seed_records")
    assert any("seed_records" in problem and "add_field" in problem for problem in check_plan(plan))


def test_publish_must_be_last_but_can_repeat() -> None:
    assert check_plan(steps("create_app", "create_page", "publish_site", "publish_site")) == []
    problems = check_plan(steps("create_app", "create_page", "publish_site", "create_auth_flow"))
    assert "publish_site must come after every other step" in problems


def test_duplicate_aliases_and_step_limit() -> None:
    plan = [
        PlanStep(workflow="create_app", intent="a", bind_as="app"),
        PlanStep(workflow="create_page", intent="b", bind_as="app"),
    ]
    assert "bind_as aliases must be unique: app" in check_plan(plan)
    assert any("limit is 1" in problem for problem in check_plan(steps("create_app", "create_page"), max_steps=1))


def test_planner_replans_after_a_bad_plan() -> None:
    bad = BuildPlan(summary="bad", steps=steps("create_table"))
    good = BuildPlan(summary="good", steps=[PlanStep(workflow="create_app", intent="create Orders", bind_as="app")])
    llm = chat(
        {
            IntentDecision: IntentDecision(kind="build"),
            BuildPlan: [bad, good],
            ToolInvocation: ToolInvocation(workflow="create_app", arguments={"name": "Orders"}),
        }
    )
    state = build_graph(make_deps(llm)).invoke({"request": "build me an orders app"})
    assert state["status"] == "completed"
    assert any("plan rejected" in line for line in state["trace"])
    assert "rejected" in llm.calls[2][1][1].content


def test_planner_gives_up_after_the_replan_budget() -> None:
    bad = BuildPlan(summary="bad", steps=steps("add_field"))
    llm = chat({IntentDecision: IntentDecision(kind="build"), BuildPlan: [bad] * 5})
    state = build_graph(make_deps(llm, max_replans=1)).invoke({"request": "build me something"})
    assert state["status"] == "failed"
    assert llm.calls_for(BuildPlan) == 2
