from __future__ import annotations

from pathlib import Path

from nocode_agent.evals.corpus_facts import load_api_specs, load_guides, workflow_order_pairs

DOCS = Path("docs")


def test_all_twelve_specs_parse() -> None:
    specs = load_api_specs(DOCS)
    assert len(specs) == 12
    by_name = {spec.workflow: spec for spec in specs}
    assert by_name["create_page"].method == "POST"
    assert by_name["create_page"].path == "/apps/{app_id}/pages"
    assert by_name["create_page"].path_params == ["app_id"]
    assert any(code == "409" for code, _ in by_name["create_page"].errors)


def test_required_fields_are_read_from_the_table() -> None:
    spec = next(spec for spec in load_api_specs(DOCS) if spec.workflow == "create_database")
    required = [item.name for item in spec.fields if item.required]
    assert required == ["app_id", "name"]


def test_guides_expose_quick_facts() -> None:
    guides = load_guides(DOCS)
    assert len(guides) >= 14
    assert sum(len(guide.facts) for guide in guides) >= 25


def test_workflow_order_pairs() -> None:
    pairs = workflow_order_pairs(DOCS)
    assert ("create_page", "add_component") in pairs
    assert ("create_form", "bind_form_to_table") in pairs
