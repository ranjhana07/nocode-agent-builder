from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from mockplatform.deps import get_or_404, get_session
from mockplatform.models import App, Database, Field, Record, Relation, Table
from mockplatform.schemas import (
    DatabaseCreate,
    DatabaseOut,
    FieldCreate,
    FieldOut,
    RelationCreate,
    RelationOut,
    SeedRecords,
    SeedResult,
    TableCreate,
    TableOut,
)

router = APIRouter()

MAX_TABLES_PER_DATABASE = 100


@router.post("/databases", response_model=DatabaseOut, status_code=201, operation_id="create_database", tags=["data"])
def create_database(payload: DatabaseCreate, session: Session = Depends(get_session)) -> Database:
    get_or_404(session, App, payload.app_id, "app")
    duplicate = session.scalar(
        select(Database).where(Database.app_id == payload.app_id, Database.name == payload.name)
    )
    if duplicate:
        raise HTTPException(status_code=409, detail=f"database {payload.name!r} already exists in app {payload.app_id}")
    database = Database(app_id=payload.app_id, name=payload.name)
    session.add(database)
    session.flush()
    return database


@router.post(
    "/databases/{database_id}/tables",
    response_model=TableOut,
    status_code=201,
    operation_id="create_table",
    tags=["data"],
)
def create_table(database_id: int, payload: TableCreate, session: Session = Depends(get_session)) -> Table:
    database = get_or_404(session, Database, database_id, "database")
    if len(database.tables) >= MAX_TABLES_PER_DATABASE:
        raise HTTPException(status_code=422, detail=f"a database can hold at most {MAX_TABLES_PER_DATABASE} tables")
    if any(table.name == payload.name for table in database.tables):
        raise HTTPException(status_code=409, detail=f"table {payload.name!r} already exists in this database")
    table = Table(database_id=database.id, name=payload.name, primary_key=payload.primary_key)
    session.add(table)
    session.flush()
    return table


@router.post(
    "/tables/{table_id}/fields",
    response_model=FieldOut,
    status_code=201,
    operation_id="add_field",
    tags=["data"],
)
def add_field(table_id: int, payload: FieldCreate, session: Session = Depends(get_session)) -> Field:
    table = get_or_404(session, Table, table_id, "table")
    if payload.type == "enum" and not payload.enum_values:
        raise HTTPException(status_code=422, detail="enum fields need at least one value in enum_values")
    if payload.type != "enum" and payload.enum_values:
        raise HTTPException(status_code=422, detail="enum_values is only allowed when type is enum")
    if payload.name == table.primary_key or any(field.name == payload.name for field in table.fields):
        raise HTTPException(status_code=409, detail=f"field {payload.name!r} already exists on table {table.name!r}")
    field = Field(
        table_id=table.id,
        name=payload.name,
        type=payload.type,
        required=payload.required,
        default=payload.default,
        enum_values=payload.enum_values,
    )
    session.add(field)
    session.flush()
    return field


@router.post(
    "/relations",
    response_model=RelationOut,
    status_code=201,
    operation_id="create_relation",
    tags=["data"],
)
def create_relation(payload: RelationCreate, session: Session = Depends(get_session)) -> Relation:
    source = get_or_404(session, Table, payload.from_table_id, "table")
    target = get_or_404(session, Table, payload.to_table_id, "table")
    if source.database_id != target.database_id:
        raise HTTPException(status_code=422, detail="relations can only connect tables of the same database")
    if source.id == target.id and payload.kind == "one_to_one":
        raise HTTPException(status_code=422, detail="a one_to_one relation cannot point a table at itself")
    relation = Relation(
        from_table_id=source.id, to_table_id=target.id, kind=payload.kind, field_name=payload.field_name
    )
    session.add(relation)
    session.flush()
    return relation


TYPE_CHECKS = {
    "text": lambda value: isinstance(value, str),
    "email": lambda value: isinstance(value, str) and "@" in value,
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "float": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "date": lambda value: isinstance(value, str) and len(value) == 10,
    "datetime": lambda value: isinstance(value, str) and "T" in value,
}


def check_record(fields: list[Field], row: dict, index: int) -> None:
    known = {field.name: field for field in fields}
    for name in row:
        if name not in known:
            raise HTTPException(status_code=422, detail=f"record {index}: unknown field {name!r}")
    for field in fields:
        value = row.get(field.name, field.default)
        if value is None:
            if field.required:
                raise HTTPException(status_code=422, detail=f"record {index}: field {field.name!r} is required")
            continue
        if field.type == "enum":
            if value not in field.enum_values:
                raise HTTPException(
                    status_code=422, detail=f"record {index}: {value!r} is not allowed for {field.name!r}"
                )
        elif not TYPE_CHECKS[field.type](value):
            raise HTTPException(
                status_code=422, detail=f"record {index}: field {field.name!r} expects {field.type}"
            )


@router.post(
    "/tables/{table_id}/records",
    response_model=SeedResult,
    status_code=201,
    operation_id="seed_records",
    tags=["data"],
)
def seed_records(table_id: int, payload: SeedRecords, session: Session = Depends(get_session)) -> SeedResult:
    table = get_or_404(session, Table, table_id, "table")
    if not table.fields:
        raise HTTPException(status_code=422, detail="add at least one field before seeding records")
    for index, row in enumerate(payload.records):
        check_record(table.fields, row, index)
    session.add_all(Record(table_id=table.id, data=row) for row in payload.records)
    return SeedResult(table_id=table.id, inserted=len(payload.records))
