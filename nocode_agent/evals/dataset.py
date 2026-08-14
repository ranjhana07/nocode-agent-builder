from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

from nocode_agent.evals.corpus_facts import (
    ApiSpecFacts,
    GuideFacts,
    load_api_specs,
    load_guides,
    workflow_order_pairs,
)

INTENTS: dict[str, list[str]] = {
    "create_app": [
        "start a brand new app for tracking orders",
        "make a new application from the inventory template",
        "spin up an empty app called Helpdesk",
        "I need a fresh app to hold my pages and data",
        "set up a new blog app",
    ],
    "create_page": [
        "add a new screen to my app",
        "make a landing page at the slug home",
        "create a dashboard layout page",
        "add another page to my app with a two column layout",
        "add an about page to the site",
    ],
    "add_component": [
        "put a button on a page",
        "place a chart component on my dashboard page",
        "add a table view of my customers to a page",
        "drop an image onto the page",
        "insert a text block at position 2",
    ],
    "create_database": [
        "give my app a place to store data",
        "make a new database named main for an app",
        "set up a database inside my app",
        "add a separate database for archived records",
        "create an empty database for my app",
    ],
    "create_table": [
        "add a customers table to my database",
        "make a new table called orders",
        "define a table with a custom primary key",
        "define a new table in snake case",
        "create a table inside the main database",
    ],
    "add_field": [
        "add an email column to a table",
        "define a required text field on a table",
        "add a status field with fixed choices",
        "add a column that stores dates",
        "add a boolean field with a default value",
    ],
    "create_relation": [
        "link orders to customers",
        "connect two tables with a one to many relation",
        "set up a many to many link between students and courses",
        "make one table reference another",
        "add a one to one relation between users and profiles",
    ],
    "seed_records": [
        "load some sample rows into a table",
        "insert initial records for my demo",
        "import a batch of test data",
        "populate a table with starter data",
        "add several rows to a table in one call",
    ],
    "create_form": [
        "build a contact form",
        "create a signup form with name and email",
        "make a form that asks users for feedback",
        "add a form with a custom submit button label",
        "add an input form to my app",
    ],
    "bind_form_to_table": [
        "save form submissions into a table",
        "connect my form to the customers table",
        "map form inputs to table columns",
        "make the signup form write records to a table",
        "send what users type in a form into my database",
    ],
    "create_auth_flow": [
        "let users log in with google",
        "add email and password sign in to my app",
        "set up roles like admin and editor",
        "enable magic link login",
        "require email verification for new accounts",
    ],
    "publish_site": [
        "make my site live",
        "deploy the app to staging for review",
        "push my app to production on a custom domain",
        "publish the app",
        "get a public url for my app",
    ],
}

QUOTAS = {
    "workflow_purpose": 12,
    "workflow_selection": 30,
    "endpoint": 12,
    "required_fields": 12,
    "allowed_values": 10,
    "default_value": 12,
    "error_status": 24,
    "quick_fact": 26,
    "call_order": 4,
}


@dataclass
class Example:
    id: str
    category: str
    question: str
    reference_answer: str
    expected_sources: list[str]
    expected_workflow: str | None = None
    tags: list[str] = field(default_factory=list)


def guides_for(workflow: str, guides: list[GuideFacts]) -> list[str]:
    return [guide.source for guide in guides if guide.workflow == workflow]


def purpose_examples(specs: list[ApiSpecFacts]) -> list[Example]:
    return [
        Example(
            "",
            "workflow_purpose",
            f"What does the {spec.workflow} workflow do?",
            spec.summary,
            [spec.source],
        )
        for spec in specs
    ]


def selection_examples(specs: list[ApiSpecFacts], guides: list[GuideFacts]) -> list[Example]:
    examples: list[Example] = []
    for spec in specs:
        for intent in INTENTS[spec.workflow][:3]:
            examples.append(
                Example(
                    "",
                    "workflow_selection",
                    f"Which API workflow should I call to {intent}?",
                    f"Call {spec.workflow}. {spec.summary}",
                    [spec.source, *guides_for(spec.workflow, guides)],
                    expected_workflow=spec.workflow,
                )
            )
    return examples


def endpoint_examples(specs: list[ApiSpecFacts]) -> list[Example]:
    return [
        Example(
            "",
            "endpoint",
            f"Which HTTP method and path does {spec.workflow} use?",
            f"{spec.method} {spec.path}",
            [spec.source, "openapi.json"],
            expected_workflow=spec.workflow,
        )
        for spec in specs
    ]


def required_examples(specs: list[ApiSpecFacts]) -> list[Example]:
    examples: list[Example] = []
    for spec in specs:
        required = [*spec.path_params, *(item.name for item in spec.fields if item.required)]
        answer = ", ".join(required) if required else "none, every field is optional"
        examples.append(
            Example(
                "",
                "required_fields",
                f"Which parameters must I send when calling {spec.workflow}?",
                answer,
                [spec.source, "openapi.json"],
                expected_workflow=spec.workflow,
            )
        )
    return examples


def allowed_value_examples(specs: list[ApiSpecFacts]) -> list[Example]:
    examples: list[Example] = []
    for spec in specs:
        for item in spec.fields:
            if "one of" not in item.constraints:
                continue
            values = item.constraints.split("one of", 1)[1].split(";")[0].replace("`", "").strip()
            examples.append(
                Example(
                    "",
                    "allowed_values",
                    f"Which values does the {item.name} parameter of {spec.workflow} accept?",
                    values,
                    [spec.source, "openapi.json"],
                    expected_workflow=spec.workflow,
                )
            )
    return examples


def default_examples(specs: list[ApiSpecFacts]) -> list[Example]:
    examples: list[Example] = []
    for spec in specs:
        for item in spec.fields:
            if "default `" not in item.constraints:
                continue
            value = item.constraints.split("default `", 1)[1].split("`", 1)[0].strip('"')
            examples.append(
                Example(
                    "",
                    "default_value",
                    f"What is the default value of {item.name} in {spec.workflow}?",
                    value if value else "an empty string",
                    [spec.source, "openapi.json"],
                    expected_workflow=spec.workflow,
                )
            )
    return examples


def error_examples(specs: list[ApiSpecFacts]) -> list[Example]:
    examples: list[Example] = []
    for spec in specs:
        for status, condition in spec.errors:
            examples.append(
                Example(
                    "",
                    "error_status",
                    f"Which status code does {spec.workflow} return when {condition}?",
                    status,
                    [spec.source],
                    expected_workflow=spec.workflow,
                )
            )
    return examples


def quick_fact_examples(guides: list[GuideFacts]) -> list[Example]:
    examples: list[Example] = []
    for guide in guides:
        for label, value in guide.facts:
            examples.append(
                Example(
                    "",
                    "quick_fact",
                    f"In the {guide.title.lower()} documentation, what is the value for: {label.lower()}?",
                    value,
                    [guide.source],
                )
            )
    return examples


def order_examples(docs_dir: Path) -> list[Example]:
    return [
        Example(
            "",
            "call_order",
            f"Which workflow has to run before {later}?",
            earlier,
            ["guides/workflow-order.md"],
            expected_workflow=None,
        )
        for earlier, later in workflow_order_pairs(docs_dir)
    ]


def build_examples(docs_dir: Path, seed: int = 7, total: int = 150) -> list[Example]:
    specs = load_api_specs(docs_dir)
    guides = load_guides(docs_dir)
    pools = {
        "workflow_purpose": purpose_examples(specs),
        "workflow_selection": selection_examples(specs, guides),
        "endpoint": endpoint_examples(specs),
        "required_fields": required_examples(specs),
        "allowed_values": allowed_value_examples(specs),
        "default_value": default_examples(specs),
        "error_status": error_examples(specs),
        "quick_fact": quick_fact_examples(guides),
        "call_order": order_examples(docs_dir),
    }
    rng = random.Random(seed)
    chosen: list[Example] = []
    leftovers: list[Example] = []
    for category, pool in pools.items():
        shuffled = pool[:]
        rng.shuffle(shuffled)
        quota = QUOTAS[category]
        chosen.extend(shuffled[:quota])
        leftovers.extend(shuffled[quota:])
    rng.shuffle(leftovers)
    chosen.extend(leftovers[: max(0, total - len(chosen))])
    chosen = chosen[:total]
    rng.shuffle(chosen)
    for position, example in enumerate(chosen, start=1):
        example.id = f"q{position:03d}"
    return chosen


def build_retrieval_queries(docs_dir: Path, examples: list[Example]) -> list[dict]:
    guides = load_guides(docs_dir)
    queries = [
        {"id": example.id, "query": example.question, "expected_sources": example.expected_sources}
        for example in examples
    ]
    for workflow, intents in INTENTS.items():
        expected = [f"api/{workflow}.md", *guides_for(workflow, guides)]
        for number, intent in enumerate(intents, start=1):
            queries.append({"id": f"i-{workflow}-{number}", "query": intent, "expected_sources": expected})
    return queries


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def generate_datasets(docs_dir: Path, questions_path: Path, retrieval_path: Path) -> tuple[int, int]:
    examples = build_examples(docs_dir)
    write_jsonl(questions_path, [asdict(example) for example in examples])
    queries = build_retrieval_queries(docs_dir, examples)
    write_jsonl(retrieval_path, queries)
    return len(examples), len(queries)


if __name__ == "__main__":
    from nocode_agent.config import get_settings

    settings = get_settings()
    counts = generate_datasets(settings.docs_dir, settings.eval_dataset_path, settings.retrieval_queries_path)
    print(f"wrote {counts[0]} questions and {counts[1]} retrieval queries")
