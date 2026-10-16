from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

from nocode_agent.agent.graph import build_graph
from nocode_agent.agent.planner import IntentDecision
from nocode_agent.agent.runtime import AgentRuntime
from nocode_agent.agent.state import BuildPlan, PlanStep, ToolInvocation
from nocode_agent.api.app import create_api
from nocode_agent.embeddings import HashingEmbeddings
from nocode_agent.rag.bm25 import BM25Index
from nocode_agent.rag.ingest import load_corpus
from nocode_agent.rag.rerank import LexicalReranker
from nocode_agent.rag.retriever import HybridRetriever
from nocode_agent.rag.service import RagStack
from nocode_agent.rag.vector_store import InMemoryVectorIndex
from tests.graph_helpers import chat, make_deps


def rag_stack() -> RagStack:
    index = InMemoryVectorIndex(HashingEmbeddings())
    chunks = load_corpus(Path("docs"), Path("docs/openapi.json"))
    index.add(chunks)
    return RagStack(index, HybridRetriever(index, BM25Index(chunks), reranker=LexicalReranker()))


def runtime() -> AgentRuntime:
    llm = chat(
        {
            IntentDecision: IntentDecision(kind="build"),
            BuildPlan: BuildPlan(summary="Build Orders", steps=[PlanStep(workflow="create_app", intent="create Orders", bind_as="app")]),
            ToolInvocation: ToolInvocation(workflow="create_app", arguments={"name": "Orders"}),
        },
        text="Use publish_site.",
    )
    deps = make_deps(llm)
    return AgentRuntime(graph=build_graph(deps, InMemorySaver()), deps=deps)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_api(rag_factory=rag_stack, runtime_factory=runtime))


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_rag_query_returns_ranked_hits(client: TestClient) -> None:
    response = client.post("/rag/query", json={"query": "publish the site to production", "k": 3})
    body = response.json()
    assert response.status_code == 200
    assert len(body["hits"]) == 3
    assert body["queries"] == ["publish the site to production"]


def test_rag_query_filters_by_doc_type(client: TestClient) -> None:
    response = client.post("/rag/query", json={"query": "publishing", "k": 5, "doc_type": "guide", "mode": "vector"})
    assert {hit["doc_type"] for hit in response.json()["hits"]} == {"guide"}


def test_rag_query_validates_input(client: TestClient) -> None:
    assert client.post("/rag/query", json={"query": "x"}).status_code == 422
    assert client.post("/rag/query", json={"query": "valid query", "k": 99}).status_code == 422


def test_agent_run_streams_steps_then_final(client: TestClient) -> None:
    response = client.post("/agent/run", json={"request": "build me an orders app", "thread_id": "t1"})
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    names = [name for name, _ in events]
    assert names[-1] == "final"
    assert "step" in names
    nodes = [payload["node"] for name, payload in events if name == "step"]
    assert "planner" in nodes and "execute" in nodes
    final = events[-1][1]
    assert final["status"] == "completed"
    assert final["results"][0]["workflow"] == "create_app"


def test_agent_run_without_streaming_returns_json(client: TestClient) -> None:
    response = client.post("/agent/run", json={"request": "build me an orders app", "stream": False})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_thread_state_can_be_read_back_or_is_404(client: TestClient) -> None:
    client.post("/agent/run", json={"request": "build me an orders app", "stream": False, "thread_id": "keep"})
    assert client.get("/agent/threads/keep").status_code == 200
    assert client.get("/agent/threads/never-existed").status_code == 404


def test_dry_run_flag_reaches_the_graph(client: TestClient) -> None:
    response = client.post("/agent/run", json={"request": "build me an orders app", "stream": False, "dry_run": True})
    body = response.json()
    assert body["status"] == "completed"
    assert body["results"][0]["output"]["dry_run"] is True
