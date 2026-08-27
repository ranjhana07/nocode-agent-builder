from __future__ import annotations

import sqlite3
from functools import partial
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from nocode_agent.agent import executor, router
from nocode_agent.agent.deps import AgentDeps
from nocode_agent.agent.planner import classify_node, planner_node
from nocode_agent.agent.state import AgentState
from nocode_agent.llm import text_call

ANSWER_SYSTEM = (
    "Answer the question using only the documentation excerpts. Name the workflow involved when there is one. "
    "If the excerpts do not contain the answer, say so."
)


def make_checkpointer(path: Path) -> SqliteSaver:
    connection = sqlite3.connect(str(path), check_same_thread=False)
    return SqliteSaver(connection)


def retrieve_node(deps: AgentDeps):
    def retrieve(state: AgentState) -> dict[str, Any]:
        query = state.get("query") or state["request"]
        hits = deps.spec_retriever(query, deps.settings.retrieval_top_k, False)
        hits += deps.docs_retriever(query, deps.settings.retrieval_top_k, False)
        documents = [hit.chunk.to_dict() for hit in hits]
        return {"query": query, "documents": documents, "trace": [f"retrieved {len(documents)} chunks"]}

    return retrieve


def answer_node(deps: AgentDeps):
    def answer(state: AgentState) -> dict[str, Any]:
        context = executor.format_documents(state.get("documents", []))
        reply = text_call(deps.llm, ANSWER_SYSTEM, f"Question: {state['request']}\n\nDocumentation:\n{context}")
        return {"answer": reply, "status": "answered", "trace": ["answered question"]}

    return answer


def build_graph(deps: AgentDeps, checkpointer: Any | None = None):
    max_repairs = deps.settings.max_repair_attempts
    graph = StateGraph(AgentState)
    graph.add_node("classify", classify_node(deps))
    graph.add_node("planner", planner_node(deps))
    graph.add_node("prepare_step", executor.prepare_step_node)
    graph.add_node("retrieve", retrieve_node(deps))
    graph.add_node("retrieve_question", retrieve_node(deps))
    graph.add_node("generate_call", executor.generate_call_node(deps))
    graph.add_node("validate", executor.validate_node(deps))
    graph.add_node("execute", executor.execute_node(deps))
    graph.add_node("advance", executor.advance_node)
    graph.add_node("answer", answer_node(deps))
    graph.add_node("finalize", executor.finalize_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", router.route_intent, ["planner", "retrieve_question"])
    graph.add_conditional_edges("planner", router.route_after_plan, ["prepare_step", "finalize"])
    graph.add_edge("prepare_step", "retrieve")
    graph.add_edge("retrieve", "generate_call")
    graph.add_edge("retrieve_question", "answer")
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
