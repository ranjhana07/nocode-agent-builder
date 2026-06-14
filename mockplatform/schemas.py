from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AppCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120, description="Unique display name of the app")
    description: str = Field(default="", max_length=500, description="Short description of what the app does")
    template: Literal["blank", "crm", "inventory", "blog"] = Field(
        default="blank", description="Starter template the app is created from"
    )


class AppOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    template: str


class PageCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120, description="Page title shown in the browser tab")
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=80, description="URL segment, lowercase letters, digits and dashes")
    layout: Literal["single", "two_column", "dashboard"] = Field(
        default="single", description="Layout grid used by the page"
    )


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    app_id: int
    title: str
    slug: str
    layout: str


class ComponentCreate(BaseModel):
    type: Literal["text", "button", "image", "table_view", "form", "chart", "list"] = Field(
        description="Kind of component to place on the page"
    )
    props: dict[str, Any] = Field(default_factory=dict, description="Component specific properties")
    position: int = Field(default=0, ge=0, le=200, description="Zero based slot on the page")


class ComponentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    page_id: int
    type: str
    props: dict[str, Any]
    position: int


class DatabaseCreate(BaseModel):
    app_id: int = Field(ge=1, description="App that owns the database")
    name: str = Field(min_length=2, max_length=80, description="Database name, unique within the app")


class DatabaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    app_id: int
    name: str


class TableCreate(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$", max_length=80, description="Table name in snake_case")
    primary_key: str = Field(default="id", max_length=80, description="Name of the primary key column")


class TableOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    database_id: int
    name: str
    primary_key: str


class FieldCreate(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$", max_length=80, description="Field name in snake_case")
    type: Literal["text", "integer", "float", "boolean", "date", "datetime", "email", "enum"] = Field(
        description="Data type of the field"
    )
    required: bool = Field(default=False, description="Reject records that leave the field empty")
    default: Any = Field(default=None, description="Value used when a record omits the field")
    enum_values: list[str] = Field(default_factory=list, description="Allowed values when type is enum")


class FieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    table_id: int
    name: str
    type: str
    required: bool
    enum_values: list[str]


class RelationCreate(BaseModel):
    from_table_id: int = Field(ge=1, description="Table that holds the reference")
    to_table_id: int = Field(ge=1, description="Table being referenced")
    kind: Literal["one_to_many", "many_to_many", "one_to_one"] = Field(description="Cardinality of the relation")
    field_name: str = Field(pattern=r"^[a-z][a-z0-9_]*$", max_length=80, description="Name of the reference field")


class RelationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_table_id: int
    to_table_id: int
    kind: str
    field_name: str


class SeedRecords(BaseModel):
    records: list[dict[str, Any]] = Field(min_length=1, max_length=500, description="Rows to insert, one object per row")


class SeedResult(BaseModel):
    table_id: int
    inserted: int


class FormCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80, description="Form name, shown as its heading")
    fields: list[str] = Field(min_length=1, max_length=40, description="Input names, in display order")
    submit_label: str = Field(default="Submit", max_length=40, description="Text on the submit button")


class FormOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    app_id: int
    name: str
    fields: list[str]
    submit_label: str
    table_id: int | None = None


class FormBinding(BaseModel):
    table_id: int = Field(ge=1, description="Table that receives submissions")
    field_mapping: dict[str, str] = Field(
        default_factory=dict, description="Maps form input names to table field names"
    )


class AuthFlowCreate(BaseModel):
    method: Literal["email_password", "magic_link", "oauth_google", "oauth_github"] = Field(
        description="Sign in method offered to end users"
    )
    require_verification: bool = Field(default=True, description="Require email verification before first sign in")
    roles: list[str] = Field(default_factory=lambda: ["member"], max_length=10, description="Roles available in the app")


class AuthFlowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    app_id: int
    method: str
    require_verification: bool
    roles: list[str]


class PublishRequest(BaseModel):
    environment: Literal["staging", "production"] = Field(default="staging", description="Target environment")
    custom_domain: str | None = Field(
        default=None, pattern=r"^[a-z0-9.-]+\.[a-z]{2,}$", description="Custom domain, production only"
    )


class PublishOut(BaseModel):
    app_id: int
    environment: str
    url: str


class ErrorOut(BaseModel):
    detail: str
