from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from pydantic import BaseModel, Field

WorkflowName = Literal[
    "create_app",
    "create_page",
    "add_component",
    "create_database",
    "create_table",
    "add_field",
    "create_relation",
    "seed_records",
    "create_form",
    "bind_form_to_table",
    "create_auth_flow",
    "publish_site",
]


class PlanStep(BaseModel):
    workflow: WorkflowName = Field(description="Platform workflow to call")
    intent: str = Field(description="What this call should accomplish, in plain English with concrete values")
    bind_as: str = Field(
        default="", description="Short alias for the object this call creates, for example app or customers_table"
    )


class BuildPlan(BaseModel):
    summary: str = Field(description="One sentence describing what will be built")
    steps: list[PlanStep] = Field(description="Ordered workflow calls")


class ToolInvocation(BaseModel):
    workflow: WorkflowName
    arguments: dict[str, Any] = Field(default_factory=dict)


class QuestionAnswer(BaseModel):
    answer: str = Field(description="Answer grounded in the documentation excerpts")
    workflow: WorkflowName | None = Field(
        default=None, description="The platform workflow the question is about, if there is exactly one"
    )


class AgentState(TypedDict, total=False):
    request: str
    dry_run: bool
    plan_only: bool
    intent: Literal["build", "question"]
    plan: list[PlanStep]
    plan_summary: str
    step_index: int
    query: str
    original_query: str
    documents: list[dict[str, Any]]
    grade_decision: str
    retrieval_attempts: int
    widen_search: bool
    pending_call: dict[str, Any]
    validation_errors: list[str]
    repair_attempts: int
    refs: dict[str, dict[str, Any]]
    selected_workflow: str
    answer: str
    status: str
    results: Annotated[list[dict[str, Any]], operator.add]
    trace: Annotated[list[str], operator.add]
