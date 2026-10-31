from __future__ import annotations

from fastapi.testclient import TestClient

from tests.test_platform import make_app, make_table


def test_field_name_cannot_reuse_the_primary_key_or_another_field(platform: TestClient) -> None:
    _, table_id = make_table(platform, make_app(platform))
    assert platform.post(f"/tables/{table_id}/fields", json={"name": "id", "type": "integer"}).status_code == 409
    assert platform.post(f"/tables/{table_id}/fields", json={"name": "email", "type": "email"}).status_code == 201
    assert platform.post(f"/tables/{table_id}/fields", json={"name": "email", "type": "text"}).status_code == 409


def test_enum_values_are_rejected_on_other_types(platform: TestClient) -> None:
    _, table_id = make_table(platform, make_app(platform))
    response = platform.post(f"/tables/{table_id}/fields", json={"name": "note", "type": "text", "enum_values": ["a"]})
    assert response.status_code == 422


def test_enum_records_must_use_allowed_values(platform: TestClient) -> None:
    _, table_id = make_table(platform, make_app(platform))
    platform.post(f"/tables/{table_id}/fields", json={"name": "tier", "type": "enum", "enum_values": ["gold", "basic"]})
    assert platform.post(f"/tables/{table_id}/records", json={"records": [{"tier": "gold"}]}).status_code == 201
    assert platform.post(f"/tables/{table_id}/records", json={"records": [{"tier": "platinum"}]}).status_code == 422


def test_seed_is_all_or_nothing(platform: TestClient) -> None:
    _, table_id = make_table(platform, make_app(platform))
    platform.post(f"/tables/{table_id}/fields", json={"name": "age", "type": "integer", "required": True})
    response = platform.post(f"/tables/{table_id}/records", json={"records": [{"age": 1}, {"age": 2}, {"age": "x"}]})
    assert response.status_code == 422
    assert "record 2" in response.json()["detail"]


def test_seed_rejects_more_than_500_records(platform: TestClient) -> None:
    _, table_id = make_table(platform, make_app(platform))
    platform.post(f"/tables/{table_id}/fields", json={"name": "n", "type": "integer"})
    assert platform.post(f"/tables/{table_id}/records", json={"records": [{"n": 1}] * 501}).status_code == 422


def test_defaults_satisfy_required_fields(platform: TestClient) -> None:
    _, table_id = make_table(platform, make_app(platform))
    platform.post(f"/tables/{table_id}/fields", json={"name": "status", "type": "text", "required": True, "default": "new"})
    assert platform.post(f"/tables/{table_id}/records", json={"records": [{}]}).status_code == 201


def test_one_to_one_cannot_point_at_itself_but_one_to_many_can(platform: TestClient) -> None:
    _, table_id = make_table(platform, make_app(platform), "categories")
    body = {"from_table_id": table_id, "to_table_id": table_id, "field_name": "parent"}
    assert platform.post("/relations", json={**body, "kind": "one_to_one"}).status_code == 422
    assert platform.post("/relations", json={**body, "kind": "one_to_many"}).status_code == 201


def test_form_input_names_must_be_unique(platform: TestClient) -> None:
    app_id = make_app(platform)
    response = platform.post(f"/apps/{app_id}/forms", json={"name": "Signup", "fields": ["email", "email"]})
    assert response.status_code == 422


def test_binding_a_table_of_another_app_is_rejected(platform: TestClient) -> None:
    first = make_app(platform, "First")
    second = make_app(platform, "Second")
    _, foreign_table = make_table(platform, second)
    form_id = platform.post(f"/apps/{first}/forms", json={"name": "Signup", "fields": ["email"]}).json()["id"]
    response = platform.post(f"/forms/{form_id}/binding", json={"table_id": foreign_table})
    assert response.status_code == 422


def test_oauth_flows_skip_verification(platform: TestClient) -> None:
    app_id = make_app(platform)
    response = platform.post(f"/apps/{app_id}/auth", json={"method": "oauth_google", "require_verification": True})
    assert response.json()["require_verification"] is False


def test_component_limit_per_page(platform: TestClient) -> None:
    app_id = make_app(platform)
    page_id = platform.post(f"/apps/{app_id}/pages", json={"title": "Home", "slug": "home"}).json()["id"]
    for position in range(60):
        assert platform.post(f"/pages/{page_id}/components", json={"type": "text", "position": position % 10}).status_code == 201
    assert platform.post(f"/pages/{page_id}/components", json={"type": "text"}).status_code == 422


def test_production_publish_with_custom_domain(platform: TestClient) -> None:
    app_id = make_app(platform)
    platform.post(f"/apps/{app_id}/pages", json={"title": "Home", "slug": "home"})
    response = platform.post(f"/apps/{app_id}/publish", json={"environment": "production", "custom_domain": "shop.example.com"})
    assert response.json()["url"] == "https://shop.example.com"
