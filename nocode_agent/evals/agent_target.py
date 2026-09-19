from __future__ import annotations

from typing import Any

from nocode_agent.agent.runtime import AgentRuntime


def make_target(runtime: AgentRuntime):
    def target(inputs: dict[str, Any]) -> dict[str, Any]:
        state = runtime.run(inputs["question"], intent="question")
        documents = state.get("documents", [])
        return {
            "answer": state.get("answer", ""),
            "contexts": [document["text"] for document in documents],
            "context_sources": [document["metadata"].get("source", "") for document in documents],
            "selected_workflow": state.get("selected_workflow", ""),
            "retrieval_attempts": state.get("retrieval_attempts", 0),
        }

    return target
