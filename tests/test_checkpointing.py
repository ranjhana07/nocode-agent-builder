from __future__ import annotations

from nocode_agent.agent.graph import build_graph, make_checkpointer
from nocode_agent.agent.planner import IntentDecision
from nocode_agent.agent.state import BuildPlan, PlanStep, ToolInvocation
from tests.graph_helpers import chat, make_deps


def test_state_is_persisted_per_thread(tmp_path) -> None:
    llm = chat(
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


def test_history_reads_a_saved_thread_back(tmp_path) -> None:
    from nocode_agent.agent.history import load_thread_state

    llm = chat(
        {
            IntentDecision: IntentDecision(kind="build"),
            BuildPlan: BuildPlan(summary="s", steps=[PlanStep(workflow="create_app", intent="create Orders", bind_as="app")]),
            ToolInvocation: ToolInvocation(workflow="create_app", arguments={"name": "Orders"}),
        }
    )
    path = tmp_path / "checkpoints.db"
    build_graph(make_deps(llm), make_checkpointer(path)).invoke(
        {"request": "build me an app"}, {"configurable": {"thread_id": "saved"}}
    )
    state = load_thread_state(path, "saved")
    assert state["status"] == "completed"
    assert any("create_app ok" in line for line in state["trace"])
    assert load_thread_state(path, "missing") is None
    assert load_thread_state(tmp_path / "absent.db", "saved") is None
