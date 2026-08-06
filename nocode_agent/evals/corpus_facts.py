from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from nocode_agent.rag.splitter import parse_front_matter


@dataclass
class RequestField:
    name: str
    type: str
    required: bool
    constraints: str
    description: str


@dataclass
class ApiSpecFacts:
    workflow: str
    source: str
    summary: str
    method: str
    path: str
    path_params: list[str] = field(default_factory=list)
    fields: list[RequestField] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class GuideFacts:
    title: str
    source: str
    workflow: str
    facts: list[tuple[str, str]] = field(default_factory=list)


def table_rows(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in lines:
        if not line.startswith("|") or set(line.replace("|", "").strip()) <= {"-", " "}:
            continue
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows[1:]


def section_lines(body: str, heading: str) -> list[str]:
    lines = body.splitlines()
    collected: list[str] = []
    active = False
    for line in lines:
        if line.startswith("## "):
            active = line[3:].strip() == heading
            continue
        if active:
            collected.append(line)
    return collected


def parse_api_spec(path: Path, docs_dir: Path) -> ApiSpecFacts:
    metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
    summary = paragraphs[1]
    endpoint = re.search(r"`([A-Z]+) ([^`]+)`", body)
    facts = ApiSpecFacts(
        workflow=metadata["workflow"],
        source=path.relative_to(docs_dir).as_posix(),
        summary=summary,
        method=endpoint.group(1),
        path=endpoint.group(2),
    )
    facts.path_params = [row[0] for row in table_rows(section_lines(body, "Path parameters"))]
    for name, kind, required, constraints, description in table_rows(section_lines(body, "Request body")):
        facts.fields.append(RequestField(name, kind, required == "yes", constraints, description))
    for line in section_lines(body, "Errors"):
        match = re.match(r"- (\d{3}): (.+)", line)
        if match:
            facts.errors.append((match.group(1), match.group(2)))
    return facts


def parse_guide(path: Path, docs_dir: Path) -> GuideFacts:
    metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
    guide = GuideFacts(
        title=metadata.get("title", path.stem),
        source=path.relative_to(docs_dir).as_posix(),
        workflow=metadata.get("workflow", "none"),
    )
    for line in section_lines(body, "Quick facts"):
        match = re.match(r"- ([^:]+): (.+)", line)
        if match:
            guide.facts.append((match.group(1).strip(), match.group(2).strip()))
    return guide


def load_api_specs(docs_dir: Path) -> list[ApiSpecFacts]:
    return [parse_api_spec(path, docs_dir) for path in sorted((docs_dir / "api").glob("*.md"))]


def load_guides(docs_dir: Path) -> list[GuideFacts]:
    return [parse_guide(path, docs_dir) for path in sorted((docs_dir / "guides").glob("*.md"))]


def workflow_order_pairs(docs_dir: Path) -> list[tuple[str, str]]:
    text = (docs_dir / "guides" / "workflow-order.md").read_text(encoding="utf-8")
    return re.findall(r"`(\w+)` before `(\w+)`", text)
