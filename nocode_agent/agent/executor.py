from __future__ import annotations

import json
from typing import Any

from nocode_agent.agent.deps import AgentDeps
from nocode_agent.agent.references import resolve_references
from nocode_agent.agent.state import AgentState, PlanStep, ToolInvocation
from nocode_agent.agent.tools import PlatformError
from nocode_agent.llm import structured_call
from nocode_agent.openapi import validate_arguments

CALL_SYSTEM = (
    "You turn one planned step into a single platform workflow call.\n"
    "Use only the documentation excerpts and the ids in the known objects. Never invent ids.\n"
    "Return the workflow name and its arguments, including path parameters such as app_id.\n"
    "To use an id of a known object write a reference like $app.id instead of the number."
)


def current_step(state: AgentState) -> PlanStep:
    return state["plan"][state["step_index"]]


def format_documents(documents: list[dict[str, Any]], limit: int = 5) -> str:
    return "\n\n".join(f"[{item['metadata'].get('source', '')}]\n{item['text']}" for item in documents[:limit])


def prepare_step_node(state: AgentState) -> dict[str, Any]:
    step = current_step(state)
    query = f"{step.workflow}: {step.intent}"
    return {
        "query": query,
        "original_query": query,
        "documents": [],
        "retrieval_attempts": 0,
        "widen_search": False,
        "grade_decision": "",
        "pending_call": {},
        "validation_errors": [],
        "repair_attempts": 0,
        "trace": [f"step {state['step_index'] + 1}/{len(state['plan'])}: {step.workflow}"],
    }


def generate_call_node(deps: AgentDeps):
    def generate(state: AgentState) -> dict[str, Any]:
        step = current_step(state)
        operation = deps.operations[step.workflow]
        prompt = "\n".join(
            [
                f"Planned workflow: {step.workflow}",
                f"Intent: {step.intent}",
                f"Known objects: {json.dumps(state.get('refs', {}))}",
                f"Argument schema: {json.dumps(operation.schema)}",
                f"Documentation:\n{format_documents(state.get('documents', []))}",
            ]
        )
        errors = state.get("validation_errors") or []
        if errors:
            previous = json.dumps(state.get("pending_call", {}).get("arguments", {}))
            prompt += f"\nYour previous arguments were {previous} and failed: {'; '.join(errors)}. Fix them."
        invocation = structured_call(deps.llm, ToolInvocation, CALL_SYSTEM, prompt)
        attempts = state.get("repair_attempts", 0) + (1 if errors else 0)
        return {
            "pending_call": {"workflow": invocation.workflow, "arguments": invocation.arguments},
            "repair_attempts": attempts,
            "trace": [f"drafted {invocation.workflow} call"],
        }

    return generate


def validate_node(deps: AgentDeps):
    def validate(state: AgentState) -> dict[str, Any]:
        call = state["pending_call"]
        step = current_step(state)
        errors: list[str] = []
        call = {**call, "arguments": resolve_references(call["arguments"], state.get("refs", {}), errors)}
        if call["workflow"] != step.workflow:
            errors.append(f"the plan requires {step.workflow} but the call targets {call['workflow']}")
        operation = deps.operations.get(call["workflow"])
        if operation is None:
            errors.append(f"unknown workflow {call['workflow']}")
        else:
            errors.extend(validate_arguments(operation, call["arguments"]))
        label = "arguments valid" if not errors else f"{len(errors)} validation errors"
        return {"pending_call": call, "validation_errors": errors, "trace": [label]}

    return validate


def execute_node(deps: AgentDeps):
    def execute(state: AgentState) -> dict[str, Any]:
        call = state["pending_call"]
        step = current_step(state)
        if state.get("dry_run"):
            output = {"id": len(state.get("results", [])) + 1, "dry_run": True, **call["arguments"]}
            return _record(state, step, call, output, "validated only (dry run)")
        try:
            output = deps.tools[call["workflow"]].invoke(call["arguments"])
        except PlatformError as error:
            return {
                "validation_errors": [f"platform rejected the call: {error.detail}"],
                "trace": [f"{call['workflow']} failed with {error.status_code}"],
            }
        return _record(state, step, call, output, "ok")

    return execute


def _record(state: AgentState, step: PlanStep, call: dict[str, Any], output: dict[str, Any], note: str) -> dict[str, Any]:
    alias = step.bind_as or step.workflow
    record = {"workflow": call["workflow"], "arguments": call["arguments"], "output": output}
    return {
        "refs": {**state.get("refs", {}), alias: output},
        "results": [record],
        "validation_errors": [],
        "trace": [f"{call['workflow']} {note}, saved as {alias}"],
    }


def advance_node(state: AgentState) -> dict[str, Any]:
    return {"step_index": state["step_index"] + 1}


def finalize_node(state: AgentState) -> dict[str, Any]:
    plan = state.get("plan", [])
    if state.get("plan_only") and plan and not state.get("validation_errors"):
        listing = "; ".join(f"{position}. {step.workflow}: {step.intent}" for position, step in enumerate(plan, start=1))
        return {"status": "planned", "answer": f"{state.get('plan_summary', 'Plan')}: {listing}", "trace": ["finished: planned"]}
    done = len(state.get("results", []))
    failed = bool(state.get("validation_errors"))
    status = "failed" if failed or done < len(plan) else "completed"
    if status == "completed":
        message = f"{state.get('plan_summary', 'Build')} finished with {done} workflow calls."
    else:
        reason = "; ".join(state.get("validation_errors", [])) or "the plan did not finish"
        message = f"Stopped after {done} of {len(plan)} workflow calls: {reason}"
    return {"status": status, "answer": message, "trace": [f"finished: {status}"]}
