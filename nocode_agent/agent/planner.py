from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from nocode_agent.agent.deps import AgentDeps
from nocode_agent.agent.plan_checker import check_plan
from nocode_agent.agent.state import AgentState, BuildPlan
from nocode_agent.llm import structured_call

CLASSIFY_SYSTEM = (
    "Decide whether the user wants the platform to build or change something (build) "
    "or wants information about how the platform or its API works (question)."
)

PLANNER_SYSTEM = """You plan builds on a no-code platform. The platform exposes exactly these workflows:
create_app, create_page, add_component, create_database, create_table, add_field, create_relation,
seed_records, create_form, bind_form_to_table, create_auth_flow, publish_site.

Rules:
- The first step is always create_app and the last step is publish_site when the user wants the site live.
- A workflow can only run after the objects it needs exist: pages before components, databases before tables,
  tables before fields, fields before seed_records, forms before bind_form_to_table.
- Give every step that creates an object a short bind_as alias so later steps can refer to it.
- Put concrete values (names, slugs, field types, sample rows) in each intent. Keep plans minimal."""


class IntentDecision(BaseModel):
    kind: Literal["build", "question"] = Field(description="build for requests to create things, question otherwise")


def classify_node(deps: AgentDeps):
    def classify(state: AgentState) -> dict[str, Any]:
        if state.get("intent"):
            return {"trace": [f"intent preset to {state['intent']}"]}
        decision = structured_call(deps.llm, IntentDecision, CLASSIFY_SYSTEM, state["request"])
        return {"intent": decision.kind, "trace": [f"classified request as {decision.kind}"]}

    return classify


def planner_node(deps: AgentDeps):
    def plan(state: AgentState) -> dict[str, Any]:
        prompt = state["request"]
        trace: list[str] = []
        for _ in range(deps.settings.max_replans + 1):
            result = structured_call(deps.llm, BuildPlan, PLANNER_SYSTEM, prompt)
            problems = check_plan(result.steps, deps.settings.max_plan_steps)
            if not problems:
                break
            trace.append(f"plan rejected: {'; '.join(problems)}")
            feedback = "; ".join(problems)
            prompt = f"{state['request']}\n\nYour previous plan was rejected: {feedback}. Fix it."
        else:
            return {
                "plan": [],
                "plan_summary": result.summary,
                "status": "failed",
                "validation_errors": problems,
                "trace": [*trace, "no valid plan after replanning"],
            }
        steps = result.steps
        return {
            "plan": steps,
            "plan_summary": result.summary,
            "step_index": 0,
            "refs": {},
            "trace": [*trace, f"planned {len(steps)} steps: " + ", ".join(step.workflow for step in steps)],
        }

    return plan
