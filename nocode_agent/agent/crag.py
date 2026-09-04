from __future__ import annotations

import operator
from functools import partial
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from nocode_agent.agent.deps import AgentDeps
from nocode_agent.agent.grader import decide, grade_documents
from nocode_agent.llm import structured_call

REWRITE_SYSTEM = """You rewrite a failed documentation search query for a no-code platform with API workflows
(create_app, create_page, add_component, create_database, create_table, add_field, create_relation,
seed_records, create_form, bind_form_to_table, create_auth_flow, publish_site).
Use concrete platform vocabulary and workflow names. Return only the new query."""


class RewrittenQuery(BaseModel):
    query: str = Field(description="Improved search query")


class RagState(TypedDict, total=False):
    query: str
    original_query: str
    documents: list[dict[str, Any]]
    docs_hits: list[dict[str, Any]]
    spec_hits: list[dict[str, Any]]
    retrieval_attempts: int
    widen_search: bool
    grade_decision: str
    trace: Annotated[list[str], operator.add]


def interleave(first: list[dict[str, Any]], second: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position in range(max(len(first), len(second))):
        for source in (first, second):
            if position < len(source) and source[position]["id"] not in seen:
                seen.add(source[position]["id"])
                merged.append(source[position])
    return merged


def retrieval_node(retriever, key: str, label: str, k: int):
    def retrieve(state: RagState) -> dict[str, Any]:
        hits = retriever(state["query"], k, state.get("widen_search", False))
        return {key: [hit.chunk.to_dict() for hit in hits], "trace": [f"{label} agent returned {len(hits)} chunks"]}

    return retrieve


def merge_node(state: RagState) -> dict[str, Any]:
    merged = interleave(state.get("spec_hits", []), state.get("docs_hits", []))
    return {
        "documents": merged,
        "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
        "trace": [f"merged into {len(merged)} unique chunks"],
    }


def grade_node(deps: AgentDeps):
    settings = deps.settings

    def grade(state: RagState) -> dict[str, Any]:
        documents = state.get("documents", [])
        grades = grade_documents(deps.llm, state["query"], documents)
        decision = decide(
            grades,
            attempts=state.get("retrieval_attempts", 1),
            max_attempts=settings.max_retrieval_attempts,
            threshold=settings.grader_relevance_threshold,
            min_relevant=settings.grader_min_relevant,
        )
        update: dict[str, Any] = {"grade_decision": decision.action}
        if decision.action in ("proceed", "give_up"):
            keep = [documents[index] for index in decision.relevant]
            ranked = sorted(zip(decision.relevant, keep), key=lambda pair: -grades[pair[0]].score)
            update["documents"] = [document for _, document in ranked]
        scores = ", ".join(f"{grade.score:.1f}" for grade in grades)
        update["trace"] = [f"grader scored [{scores}] -> {decision.action}"]
        return update

    return grade


def rewrite_node(deps: AgentDeps):
    def rewrite(state: RagState) -> dict[str, Any]:
        result = structured_call(
            deps.llm,
            RewrittenQuery,
            REWRITE_SYSTEM,
            f"Original request: {state['original_query']}\nFailed query: {state['query']}",
        )
        return {"query": result.query, "widen_search": False, "trace": [f"rewrote query to: {result.query}"]}

    return rewrite


def widen_node(state: RagState) -> dict[str, Any]:
    return {"widen_search": True, "trace": ["retrieving again with wider search"]}


def route_after_grade(state: RagState) -> str:
    return {"rewrite": "rewrite", "retrieve_again": "widen"}.get(state.get("grade_decision", ""), END)


def build_crag_graph(deps: AgentDeps):
    k = deps.settings.retrieval_top_k
    graph = StateGraph(RagState)
    graph.add_node("retrieve_docs", retrieval_node(deps.docs_retriever, "docs_hits", "docs", k))
    graph.add_node("retrieve_specs", retrieval_node(deps.spec_retriever, "spec_hits", "api-spec", k))
    graph.add_node("merge", merge_node)
    graph.add_node("grade", grade_node(deps))
    graph.add_node("rewrite", rewrite_node(deps))
    graph.add_node("widen", widen_node)
    graph.add_edge(START, "retrieve_docs")
    graph.add_edge(START, "retrieve_specs")
    graph.add_edge(["retrieve_docs", "retrieve_specs"], "merge")
    graph.add_edge("merge", "grade")
    graph.add_conditional_edges("grade", route_after_grade, ["rewrite", "widen", END])
    graph.add_edge("rewrite", "retrieve_docs")
    graph.add_edge("rewrite", "retrieve_specs")
    graph.add_edge("widen", "retrieve_docs")
    graph.add_edge("widen", "retrieve_specs")
    return graph.compile()
