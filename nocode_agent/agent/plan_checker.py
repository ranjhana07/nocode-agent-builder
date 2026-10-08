from __future__ import annotations

from nocode_agent.agent.state import PlanStep

REQUIRES_EARLIER = {
    "create_page": ["create_app"],
    "add_component": ["create_page"],
    "create_database": ["create_app"],
    "create_table": ["create_database"],
    "add_field": ["create_table"],
    "create_relation": ["create_table"],
    "seed_records": ["add_field"],
    "create_form": ["create_app"],
    "bind_form_to_table": ["create_form", "create_table"],
    "create_auth_flow": ["create_app"],
    "publish_site": ["create_app", "create_page"],
}


def check_plan(steps: list[PlanStep], max_steps: int = 60) -> list[str]:
    problems: list[str] = []
    if len(steps) > max_steps:
        problems.append(f"the plan has {len(steps)} steps, the limit is {max_steps}")
    seen: set[str] = set()
    for position, step in enumerate(steps, start=1):
        for needed in REQUIRES_EARLIER.get(step.workflow, []):
            if needed not in seen:
                problems.append(f"step {position} ({step.workflow}) needs {needed} to run earlier")
        seen.add(step.workflow)
    first_publish = next((position for position, step in enumerate(steps) if step.workflow == "publish_site"), None)
    if first_publish is not None and any(step.workflow != "publish_site" for step in steps[first_publish:]):
        problems.append("publish_site must come after every other step")
    aliases = [step.bind_as for step in steps if step.bind_as]
    duplicated = sorted({alias for alias in aliases if aliases.count(alias) > 1})
    if duplicated:
        problems.append("bind_as aliases must be unique: " + ", ".join(duplicated))
    return problems
