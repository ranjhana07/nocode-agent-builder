from __future__ import annotations

import sqlite3
from functools import partial
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from nocode_agent.agent import executor, router
from nocode_agent.agent.crag import build_crag_graph
from nocode_agent.agent.deps import AgentDeps
from nocode_agent.agent.planner import classify_node, planner_node
from nocode_agent.agent.state import AgentState, QuestionAnswer
from nocode_agent.llm import structured_call

ANSWER_SYSTEM = (
    "Answer the question using only the documentation excerpts. Name the workflow involved when there is one. "
    "If the excerpts do not contain the answer, say so."
)


def make_checkpointer(path: Path) -> SqliteSaver:
    connection = sqlite3.connect(str(path), check_same_thread=False)
    return SqliteSaver(connection)


def prepare_question_node(state: AgentState) -> dict[str, Any]:
    return {
        "query": state["request"],
        "original_query": state["request"],
        "documents": [],
        "retrieval_attempts": 0,
        "widen_search": False,
        "grade_decision": "",
    }


def answer_node(deps: AgentDeps):
    def answer(state: AgentState) -> dict[str, Any]:
        if not state.get("documents"):
            message = "I could not find documentation that answers this question."
            return {"answer": message, "status": "unanswered", "trace": ["no usable context, declined to answer"]}
        context = executor.format_documents(state.get("documents", []))
        prompt = f"Question: {state['request']}\n\nDocumentation:\n{context}"
        reply = structured_call(deps.llm, QuestionAnswer, ANSWER_SYSTEM, prompt)
        return {
            "answer": reply.answer,
            "selected_workflow": reply.workflow or "",
            "status": "answered",
            "trace": ["answered question"],
        }

    return answer


def build_graph(deps: AgentDeps, checkpointer: Any | None = None):
    max_repairs = deps.settings.max_repair_attempts
    graph = StateGraph(AgentState)
    graph.add_node("classify", classify_node(deps))
    graph.add_node("planner", planner_node(deps))
    graph.add_node("prepare_step", executor.prepare_step_node)
    graph.add_node("prepare_question", prepare_question_node)
    graph.add_node("crag", build_crag_graph(deps))
    graph.add_node("generate_call", executor.generate_call_node(deps))
    graph.add_node("validate", executor.validate_node(deps))
    graph.add_node("execute", executor.execute_node(deps))
    graph.add_node("advance", executor.advance_node)
    graph.add_node("answer", answer_node(deps))
    graph.add_node("finalize", executor.finalize_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", router.route_intent, ["planner", "prepare_question"])
    graph.add_conditional_edges("planner", router.route_after_plan, ["prepare_step", "finalize"])
    graph.add_edge("prepare_step", "crag")
    graph.add_edge("prepare_question", "crag")
    graph.add_conditional_edges("crag", router.route_after_retrieval, ["generate_call", "answer"])
    graph.add_edge("generate_call", "validate")
    graph.add_conditional_edges(
        "validate", partial(router.route_after_check, max_repairs=max_repairs), ["execute", "generate_call", "finalize"]
    )
    graph.add_conditional_edges(
        "execute", partial(router.route_after_execute, max_repairs=max_repairs), ["advance", "generate_call", "finalize"]
    )
    graph.add_conditional_edges("advance", router.route_after_advance, ["prepare_step", "finalize"])
    graph.add_edge("answer", END)
    graph.add_edge("finalize", END)
    return graph.compile(checkpointer=checkpointer)
