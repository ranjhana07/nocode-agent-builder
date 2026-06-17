from __future__ import annotations

from fastapi.testclient import TestClient


def make_app(client: TestClient, name: str = "Orders") -> int:
    response = client.post("/apps", json={"name": name, "template": "inventory"})
    assert response.status_code == 201
    return response.json()["id"]


def make_table(client: TestClient, app_id: int, table_name: str = "customers") -> tuple[int, int]:
    database_id = client.post("/databases", json={"app_id": app_id, "name": "main"}).json()["id"]
    table_id = client.post(f"/databases/{database_id}/tables", json={"name": table_name}).json()["id"]
    return database_id, table_id


def test_create_app_rejects_duplicate_names(platform: TestClient) -> None:
    make_app(platform)
    response = platform.post("/apps", json={"name": "Orders"})
    assert response.status_code == 409


def test_create_app_validates_template(platform: TestClient) -> None:
    response = platform.post("/apps", json={"name": "Orders", "template": "spaceship"})
    assert response.status_code == 422


def test_create_page_and_duplicate_slug(platform: TestClient) -> None:
    app_id = make_app(platform)
    first = platform.post(f"/apps/{app_id}/pages", json={"title": "Home", "slug": "home"})
    assert first.status_code == 201
    second = platform.post(f"/apps/{app_id}/pages", json={"title": "Home 2", "slug": "home"})
    assert second.status_code == 409


def test_create_page_unknown_app(platform: TestClient) -> None:
    response = platform.post("/apps/99/pages", json={"title": "Home", "slug": "home"})
    assert response.status_code == 404


def test_add_component(platform: TestClient) -> None:
    app_id = make_app(platform)
    page_id = platform.post(f"/apps/{app_id}/pages", json={"title": "Home", "slug": "home"}).json()["id"]
    response = platform.post(
        f"/pages/{page_id}/components", json={"type": "button", "props": {"label": "Buy"}, "position": 2}
    )
    assert response.status_code == 201
    assert response.json()["props"] == {"label": "Buy"}


def test_enum_field_requires_values(platform: TestClient) -> None:
    _, table_id = make_table(platform, make_app(platform))
    response = platform.post(f"/tables/{table_id}/fields", json={"name": "tier", "type": "enum"})
    assert response.status_code == 422


def test_seed_records_checks_types_and_required(platform: TestClient) -> None:
    _, table_id = make_table(platform, make_app(platform))
    platform.post(f"/tables/{table_id}/fields", json={"name": "email", "type": "email", "required": True})
    platform.post(f"/tables/{table_id}/fields", json={"name": "age", "type": "integer"})
    ok = platform.post(f"/tables/{table_id}/records", json={"records": [{"email": "a@b.co", "age": 31}]})
    assert ok.status_code == 201
    assert ok.json()["inserted"] == 1
    missing = platform.post(f"/tables/{table_id}/records", json={"records": [{"age": 31}]})
    assert missing.status_code == 422
    wrong_type = platform.post(f"/tables/{table_id}/records", json={"records": [{"email": "a@b.co", "age": "x"}]})
    assert wrong_type.status_code == 422


def test_seed_records_requires_fields(platform: TestClient) -> None:
    _, table_id = make_table(platform, make_app(platform))
    response = platform.post(f"/tables/{table_id}/records", json={"records": [{"a": 1}]})
    assert response.status_code == 422


def test_relation_needs_same_database(platform: TestClient) -> None:
    app_id = make_app(platform)
    _, first = make_table(platform, app_id, "customers")
    other_database = platform.post("/databases", json={"app_id": app_id, "name": "archive"}).json()["id"]
    second = platform.post(f"/databases/{other_database}/tables", json={"name": "orders"}).json()["id"]
    response = platform.post(
        "/relations",
        json={"from_table_id": second, "to_table_id": first, "kind": "one_to_many", "field_name": "customer"},
    )
    assert response.status_code == 422


def test_form_binding_maps_inputs_to_fields(platform: TestClient) -> None:
    app_id = make_app(platform)
    _, table_id = make_table(platform, app_id)
    platform.post(f"/tables/{table_id}/fields", json={"name": "email", "type": "email"})
    form_id = platform.post(f"/apps/{app_id}/forms", json={"name": "Signup", "fields": ["email"]}).json()["id"]
    response = platform.post(f"/forms/{form_id}/binding", json={"table_id": table_id})
    assert response.status_code == 200
    assert response.json()["table_id"] == table_id
    bad = platform.post(
        f"/forms/{form_id}/binding", json={"table_id": table_id, "field_mapping": {"email": "missing"}}
    )
    assert bad.status_code == 422


def test_auth_flow_is_unique_per_app(platform: TestClient) -> None:
    app_id = make_app(platform)
    first = platform.post(f"/apps/{app_id}/auth", json={"method": "email_password"})
    assert first.status_code == 201
    second = platform.post(f"/apps/{app_id}/auth", json={"method": "magic_link"})
    assert second.status_code == 409


def test_publish_requires_a_page(platform: TestClient) -> None:
    app_id = make_app(platform)
    assert platform.post(f"/apps/{app_id}/publish", json={}).status_code == 422
    platform.post(f"/apps/{app_id}/pages", json={"title": "Home", "slug": "home"})
    response = platform.post(f"/apps/{app_id}/publish", json={"environment": "staging"})
    assert response.status_code == 200
    assert response.json()["url"].startswith("https://orders.staging")


def test_custom_domain_is_production_only(platform: TestClient) -> None:
    app_id = make_app(platform)
    platform.post(f"/apps/{app_id}/pages", json={"title": "Home", "slug": "home"})
    response = platform.post(f"/apps/{app_id}/publish", json={"custom_domain": "shop.example.com"})
    assert response.status_code == 422


def test_openapi_exposes_twelve_workflows(platform: TestClient) -> None:
    spec = platform.get("/openapi.json").json()
    operation_ids = {
        operation["operationId"] for path in spec["paths"].values() for operation in path.values()
    }
    assert len(operation_ids) == 12
