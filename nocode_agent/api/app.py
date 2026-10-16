from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Iterator
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from nocode_agent.agent.runtime import AgentRuntime, build_runtime
from nocode_agent.api.schemas import AgentRequest, AgentResponse, RagHit, RagQuery, RagResponse
from nocode_agent.rag.filters import MetadataFilter
from nocode_agent.rag.service import RagStack, build_rag_stack


def sse(event: str, payload: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, default=str)}\n\n"


def final_payload(state: dict[str, Any], thread_id: str) -> dict[str, Any]:
    return {
        "thread_id": thread_id,
        "status": state.get("status", "unknown"),
        "answer": state.get("answer", ""),
        "results": state.get("results", []),
        "trace": state.get("trace", []),
    }


def create_api(
    rag_factory: Callable[[], RagStack] = build_rag_stack,
    runtime_factory: Callable[[], AgentRuntime] = build_runtime,
) -> FastAPI:
    app = FastAPI(title="Nocode agent builder", version="0.1.0")
    cache: dict[str, Any] = {}

    def rag() -> RagStack:
        if "rag" not in cache:
            cache["rag"] = rag_factory()
        return cache["rag"]

    def runtime() -> AgentRuntime:
        if "runtime" not in cache:
            cache["runtime"] = runtime_factory()
        return cache["runtime"]

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/rag/query", response_model=RagResponse)
    def rag_query(body: RagQuery) -> RagResponse:
        retriever = rag().retriever
        metadata_filter = MetadataFilter(
            doc_types=(body.doc_type,) if body.doc_type else (),
            workflows=(body.workflow,) if body.workflow else (),
        )
        if body.mode == "vector":
            result = retriever.vector_only(body.query, body.k, metadata_filter)
        else:
            result = retriever.hybrid(body.query, body.k, metadata_filter, body.multi_query, body.rerank)
        hits = [
            RagHit(
                id=hit.chunk.id,
                score=hit.score,
                source=hit.chunk.source,
                section=hit.chunk.metadata.get("section", ""),
                doc_type=hit.chunk.metadata.get("doc_type", ""),
                workflow=hit.chunk.workflow,
                text=hit.chunk.text,
            )
            for hit in result.hits
        ]
        return RagResponse(queries=result.queries, hits=hits)

    @app.post("/agent/run")
    def agent_run(body: AgentRequest):
        agent = runtime()
        thread_id = body.thread_id or uuid.uuid4().hex
        if not body.stream:
            state = agent.run(body.request, thread_id, body.intent, body.dry_run)
            return AgentResponse(**final_payload(state, thread_id))

        def events() -> Iterator[str]:
            try:
                for event in agent.stream(body.request, thread_id, body.intent, body.dry_run):
                    if event["node"] == "__end__":
                        yield sse("final", final_payload(event["state"], thread_id))
                    else:
                        yield sse("step", event)
            except Exception as error:
                yield sse("error", {"thread_id": thread_id, "detail": str(error)})

        return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})

    @app.get("/agent/threads/{thread_id}")
    def thread_state(thread_id: str) -> AgentResponse:
        values = runtime().graph.get_state({"configurable": {"thread_id": thread_id}}).values
        if not values:
            raise HTTPException(status_code=404, detail="unknown thread")
        return AgentResponse(**final_payload(values, thread_id))

    return app


def build_app() -> FastAPI:
    return create_api()
