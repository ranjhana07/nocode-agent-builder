from __future__ import annotations

from nocode_agent.agent.graph import build_graph, make_checkpointer
from nocode_agent.agent.planner import IntentDecision
from nocode_agent.agent.state import BuildPlan, PlanStep, ToolInvocation
from tests.fakes import FakeChat
from tests.graph_helpers import make_deps


def test_state_is_persisted_per_thread(tmp_path) -> None:
    llm = FakeChat(
        {
            IntentDecision: IntentDecision(kind="build"),
            BuildPlan: BuildPlan(summary="s", steps=[PlanStep(workflow="create_app", intent="create Orders", bind_as="app")]),
            ToolInvocation: ToolInvocation(workflow="create_app", arguments={"name": "Orders"}),
        }
    )
    checkpointer = make_checkpointer(tmp_path / "checkpoints.db")
    graph = build_graph(make_deps(llm), checkpointer)
    config = {"configurable": {"thread_id": "t-1"}}
    graph.invoke({"request": "build me an app"}, config)
    saved = graph.get_state(config)
    assert saved.values["status"] == "completed"
    assert saved.values["refs"]["app"]["name"] == "Orders"
    assert graph.get_state({"configurable": {"thread_id": "other"}}).values == {}
    history = list(graph.get_state_history(config))
    assert len(history) > 5
