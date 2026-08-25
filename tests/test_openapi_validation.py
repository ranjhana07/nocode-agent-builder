from __future__ import annotations

from pathlib import Path

import pytest

from nocode_agent.openapi import Operation, load_operations, validate_arguments

OPERATIONS = load_operations(Path("docs/openapi.json"))


def test_twelve_operations_are_extracted() -> None:
    assert len(OPERATIONS) == 12
    assert set(OPERATIONS) >= {"create_app", "publish_site", "bind_form_to_table"}


def test_path_params_are_merged_into_the_schema() -> None:
    operation = OPERATIONS["add_field"]
    assert operation.path_params == ["table_id"]
    assert "table_id" in operation.schema["required"]
    assert operation.body_params == ["default", "enum_values", "name", "required", "type"]


def test_refs_are_resolved() -> None:
    schema = OPERATIONS["create_app"].schema
    assert "$ref" not in str(schema)
    assert schema["properties"]["template"]["enum"] == ["blank", "crm", "inventory", "blog"]


@pytest.mark.parametrize(
    "name, arguments",
    [
        ("create_app", {"name": "Orders"}),
        ("create_page", {"app_id": 1, "title": "Home", "slug": "home"}),
        ("add_field", {"table_id": 2, "name": "status", "type": "enum", "enum_values": ["a"]}),
        ("seed_records", {"table_id": 3, "records": [{"email": "a@b.co"}]}),
        ("publish_site", {"app_id": 1, "environment": "production", "custom_domain": "shop.example.com"}),
    ],
)
def test_valid_arguments_pass(name: str, arguments: dict) -> None:
    assert validate_arguments(OPERATIONS[name], arguments) == []


@pytest.mark.parametrize(
    "name, arguments, fragment",
    [
        ("create_app", {}, "'name' is a required property"),
        ("create_app", {"name": "x"}, "too short"),
        ("create_app", {"name": "Orders", "template": "rocket"}, "is not one of"),
        ("create_page", {"app_id": 1, "title": "Home", "slug": "Home Page"}, "does not match"),
        ("create_page", {"title": "Home", "slug": "home"}, "'app_id' is a required property"),
        ("add_field", {"table_id": 1, "name": "x", "type": "uuid"}, "is not one of"),
        ("seed_records", {"table_id": 1, "records": []}, "should be non-empty"),
        ("create_app", {"name": "Orders", "colour": "red"}, "Additional properties"),
        ("add_component", {"page_id": "one", "type": "text"}, "is not of type 'integer'"),
    ],
)
def test_invalid_arguments_are_reported(name: str, arguments: dict, fragment: str) -> None:
    errors = validate_arguments(OPERATIONS[name], arguments)
    assert any(fragment in error for error in errors), errors


def test_errors_name_the_offending_field() -> None:
    errors = validate_arguments(OPERATIONS["create_page"], {"app_id": 1, "title": "Home", "slug": "BAD"})
    assert errors[0].startswith("slug:")


def test_operation_dataclass_defaults() -> None:
    operation = Operation("noop", "GET", "/", "", [], {"type": "object"})
    assert operation.body_params == []
