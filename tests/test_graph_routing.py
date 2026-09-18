from __future__ import annotations

import pytest

from nocode_agent.agent import router
from nocode_agent.agent.graph import build_graph
from nocode_agent.agent.planner import IntentDecision
from nocode_agent.agent.state import BuildPlan, PlanStep, QuestionAnswer, ToolInvocation
from nocode_agent.agent.tools import PlatformError
from tests.fakes import fake_tools
from tests.graph_helpers import OPERATIONS, chat, make_deps


def plan(*steps: tuple[str, str, str]) -> BuildPlan:
    return BuildPlan(
        summary="Build the thing",
        steps=[PlanStep(workflow=name, intent=intent, bind_as=alias) for name, intent, alias in steps],
    )


def invocation(workflow: str, **arguments) -> ToolInvocation:
    return ToolInvocation(workflow=workflow, arguments=arguments)


def run(graph, request: str = "build me a thing", **extra):
    return graph.invoke({"request": request, **extra})


def test_build_request_runs_every_step_in_order() -> None:
    llm = chat(
        {
            IntentDecision: IntentDecision(kind="build"),
            BuildPlan: plan(("create_app", "create Orders", "app"), ("create_page", "add a home page", "page")),
            ToolInvocation: [
                invocation("create_app", name="Orders"),
                invocation("create_page", app_id=1, title="Home", slug="home"),
            ],
        }
    )
    tools = fake_tools(list(OPERATIONS))
    state = run(build_graph(make_deps(llm, tools)))
    assert state["status"] == "completed"
    assert [item["workflow"] for item in state["results"]] == ["create_app", "create_page"]
    assert tools["create_page"].invocations == [{"app_id": 1, "title": "Home", "slug": "home"}]
    assert set(state["refs"]) == {"app", "page"}


def test_question_intent_skips_the_planner() -> None:
    reply = QuestionAnswer(answer="Use create_app.", workflow="create_app")
    llm = chat({IntentDecision: IntentDecision(kind="question"), QuestionAnswer: reply})
    state = run(build_graph(make_deps(llm)), "how do I create an app?")
    assert state["status"] == "answered"
    assert state["answer"] == "Use create_app."
    assert state["selected_workflow"] == "create_app"
    assert llm.calls_for(BuildPlan) == 0


def test_preset_intent_skips_classification() -> None:
    llm = chat({QuestionAnswer: QuestionAnswer(answer="answer")})
    state = run(build_graph(make_deps(llm)), "q", intent="question")
    assert state["answer"] == "answer"
    assert llm.calls_for(IntentDecision) == 0


def test_empty_plan_goes_straight_to_finalize() -> None:
    llm = chat({IntentDecision: IntentDecision(kind="build"), BuildPlan: plan()})
    state = run(build_graph(make_deps(llm)))
    assert state["status"] == "completed"
    assert state.get("results", []) == []


def test_invalid_arguments_are_repaired_once() -> None:
    llm = chat(
        {
            IntentDecision: IntentDecision(kind="build"),
            BuildPlan: plan(("create_app", "create Orders", "app")),
            ToolInvocation: [invocation("create_app", name="O"), invocation("create_app", name="Orders")],
        }
    )
    tools = fake_tools(list(OPERATIONS))
    state = run(build_graph(make_deps(llm, tools)))
    assert state["status"] == "completed"
    assert state["repair_attempts"] == 1
    assert len(tools["create_app"].invocations) == 1


def test_repair_budget_is_capped() -> None:
    llm = chat(
        {
            IntentDecision: IntentDecision(kind="build"),
            BuildPlan: plan(("create_app", "create Orders", "app")),
            ToolInvocation: [invocation("create_app", name="O")] * 3,
        }
    )
    state = run(build_graph(make_deps(llm, max_repair_attempts=2)))
    assert state["status"] == "failed"
    assert "too short" in state["answer"]
    assert llm.calls_for(ToolInvocation) == 3


def test_wrong_workflow_is_rejected_by_the_validator() -> None:
    llm = chat(
        {
            IntentDecision: IntentDecision(kind="build"),
            BuildPlan: plan(("create_app", "create Orders", "app")),
            ToolInvocation: [invocation("publish_site", app_id=1), invocation("create_app", name="Orders")],
        }
    )
    tools = fake_tools(list(OPERATIONS))
    state = run(build_graph(make_deps(llm, tools)))
    assert tools["publish_site"].invocations == []
    assert state["status"] == "completed"


def test_platform_rejection_triggers_a_repair_loop() -> None:
    llm = chat(
        {
            IntentDecision: IntentDecision(kind="build"),
            BuildPlan: plan(("create_app", "create Orders", "app")),
            ToolInvocation: [invocation("create_app", name="Orders"), invocation("create_app", name="Orders 2")],
        }
    )
    tools = fake_tools(list(OPERATIONS), {"create_app": [PlatformError(409, "an app with that name already exists")]})
    state = run(build_graph(make_deps(llm, tools)))
    assert state["status"] == "completed"
    assert tools["create_app"].invocations[-1] == {"name": "Orders 2"}


@pytest.mark.parametrize(
    "state, expected",
    [
        ({"intent": "build"}, "planner"),
        ({"intent": "question"}, "prepare_question"),
    ],
)
def test_route_intent(state, expected) -> None:
    assert router.route_intent(state) == expected


def test_route_after_advance() -> None:
    assert router.route_after_advance({"step_index": 1, "plan": [1, 2]}) == "prepare_step"
    assert router.route_after_advance({"step_index": 2, "plan": [1, 2]}) == "finalize"


def test_route_after_check() -> None:
    assert router.route_after_check({"validation_errors": []}, 2) == "execute"
    assert router.route_after_check({"validation_errors": ["x"], "repair_attempts": 1}, 2) == "generate_call"
    assert router.route_after_check({"validation_errors": ["x"], "repair_attempts": 2}, 2) == "finalize"


def test_question_without_usable_context_is_not_answered_by_guessing() -> None:
    from nocode_agent.agent.grader import ChunkGrade, GradeReport
    from nocode_agent.agent.crag import RewrittenQuery

    def nothing_relevant(messages):
        return GradeReport(grades=[ChunkGrade(index=index, score=0.0) for index in range(10)])

    llm = chat(
        {GradeReport: nothing_relevant, RewrittenQuery: RewrittenQuery(query="try again")},
        text="a made up answer",
    )
    state = run(build_graph(make_deps(llm)), "what is the airspeed of a swallow", intent="question")
    assert state["status"] == "unanswered"
    assert "could not find" in state["answer"]
    assert state["retrieval_attempts"] == 3
