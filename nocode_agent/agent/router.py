from __future__ import annotations

from nocode_agent.agent.state import AgentState


def route_intent(state: AgentState) -> str:
    return "planner" if state.get("intent") == "build" else "prepare_question"


def route_after_plan(state: AgentState) -> str:
    return "prepare_step" if state.get("plan") else "finalize"


def route_after_retrieval(state: AgentState) -> str:
    return "generate_call" if state.get("intent") == "build" else "answer"


def route_after_check(state: AgentState, max_repairs: int) -> str:
    if not state.get("validation_errors"):
        return "execute"
    if state.get("repair_attempts", 0) < max_repairs:
        return "generate_call"
    return "finalize"


def route_after_execute(state: AgentState, max_repairs: int) -> str:
    if not state.get("validation_errors"):
        return "advance"
    if state.get("repair_attempts", 0) < max_repairs:
        return "generate_call"
    return "finalize"


def route_after_advance(state: AgentState) -> str:
    if state["step_index"] < len(state.get("plan", [])):
        return "prepare_step"
    return "finalize"
