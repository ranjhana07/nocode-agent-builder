from __future__ import annotations

import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models import BaseChatModel

from nocode_agent.agent.deps import AgentDeps
from nocode_agent.agent.graph import build_graph, make_checkpointer
from nocode_agent.agent.retrieval_agents import make_docs_agent, make_spec_agent
from nocode_agent.agent.tools import PlatformClient, build_tools, tool_registry
from nocode_agent.config import Settings, get_settings
from nocode_agent.llm import build_chat_model
from nocode_agent.openapi import load_operations
from nocode_agent.rag.query_filters import known_workflows_from
from nocode_agent.rag.service import RagStack, build_rag_stack


@dataclass
class AgentRuntime:
    graph: Any
    deps: AgentDeps

    def run(
        self, request: str, thread_id: str | None = None, intent: str | None = None, dry_run: bool = False
    ) -> dict[str, Any]:
        config = {"configurable": {"thread_id": thread_id or uuid.uuid4().hex}}
        payload: dict[str, Any] = {"request": request, "dry_run": dry_run}
        if intent:
            payload["intent"] = intent
        return self.graph.invoke(payload, config)

    def stream(
        self, request: str, thread_id: str | None = None, intent: str | None = None, dry_run: bool = False
    ) -> Iterator[dict[str, Any]]:
        thread = thread_id or uuid.uuid4().hex
        config = {"configurable": {"thread_id": thread}}
        payload: dict[str, Any] = {"request": request, "dry_run": dry_run}
        if intent:
            payload["intent"] = intent
        mark = time.perf_counter()
        for namespace, update in self.graph.stream(payload, config, stream_mode="updates", subgraphs=True):
            now = time.perf_counter()
            elapsed_ms = round((now - mark) * 1000)
            mark = now
            for node, values in update.items():
                yield {
                    "thread_id": thread,
                    "node": node,
                    "subgraph": bool(namespace),
                    "trace": (values or {}).get("trace", []),
                    "elapsed_ms": elapsed_ms,
                }
        final = self.graph.get_state(config).values
        yield {"thread_id": thread, "node": "__end__", "subgraph": False, "state": final}


def build_runtime(
    settings: Settings | None = None,
    llm: BaseChatModel | None = None,
    rag_stack: RagStack | None = None,
    platform_client: PlatformClient | None = None,
) -> AgentRuntime:
    settings = settings or get_settings()
    llm = llm or build_chat_model(settings)
    stack = rag_stack or build_rag_stack(settings, llm=llm)
    operations = load_operations(settings.openapi_path)
    client = platform_client or PlatformClient(
        settings.platform_url, api_key=settings.platform_api_key, max_retries=settings.platform_max_retries
    )
    workflows = known_workflows_from(stack.index.all_chunks())
    deps = AgentDeps(
        llm=llm,
        operations=operations,
        tools=tool_registry(build_tools(operations, client)),
        docs_retriever=make_docs_agent(stack.retriever),
        spec_retriever=make_spec_agent(stack.retriever, workflows),
        settings=settings,
    )
    graph = build_graph(deps, make_checkpointer(settings.checkpoint_db))
    return AgentRuntime(graph=graph, deps=deps)
