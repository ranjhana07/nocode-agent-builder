from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mockplatform.main import create_platform_app
from nocode_agent.agent.tools import PlatformClient, PlatformError, build_tools, tool_registry
from nocode_agent.openapi import load_operations

OPERATIONS = load_operations(Path("docs/openapi.json"))


@pytest.fixture()
def registry():
    http = TestClient(create_platform_app("sqlite://"))
    return tool_registry(build_tools(OPERATIONS, PlatformClient("http://testserver", client=http)))


def test_one_tool_per_workflow(registry) -> None:
    assert len(registry) == 12
    assert registry["create_app"].args_schema["required"] == ["name"]


def test_tool_posts_body_and_fills_path_params(registry) -> None:
    app = registry["create_app"].invoke({"name": "Orders"})
    page = registry["create_page"].invoke({"app_id": app["id"], "title": "Home", "slug": "home"})
    assert page["app_id"] == app["id"]
    assert page["layout"] == "single"


def test_platform_errors_are_raised_with_status(registry) -> None:
    registry["create_app"].invoke({"name": "Orders"})
    with pytest.raises(PlatformError) as caught:
        registry["create_app"].invoke({"name": "Orders"})
    assert caught.value.status_code == 409
    assert "already exists" in caught.value.detail


def test_full_chain_through_tools(registry) -> None:
    app = registry["create_app"].invoke({"name": "Shop"})
    database = registry["create_database"].invoke({"app_id": app["id"], "name": "main"})
    table = registry["create_table"].invoke({"database_id": database["id"], "name": "customers"})
    registry["add_field"].invoke({"table_id": table["id"], "name": "email", "type": "email", "required": True})
    seeded = registry["seed_records"].invoke({"table_id": table["id"], "records": [{"email": "a@b.co"}]})
    assert seeded["inserted"] == 1
