from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from mockplatform.deps import get_or_404, get_session
from mockplatform.models import App, AuthFlow, Deployment, Form, Table
from mockplatform.schemas import (
    AuthFlowCreate,
    AuthFlowOut,
    FormBinding,
    FormCreate,
    FormOut,
    PublishOut,
    PublishRequest,
)

router = APIRouter()


@router.post(
    "/apps/{app_id}/forms", response_model=FormOut, status_code=201, operation_id="create_form", tags=["forms"]
)
def create_form(app_id: int, payload: FormCreate, session: Session = Depends(get_session)) -> Form:
    app = get_or_404(session, App, app_id, "app")
    if len(set(payload.fields)) != len(payload.fields):
        raise HTTPException(status_code=422, detail="form field names must be unique")
    form = Form(app_id=app.id, name=payload.name, fields=payload.fields, submit_label=payload.submit_label)
    session.add(form)
    session.flush()
    return form


@router.post(
    "/forms/{form_id}/binding",
    response_model=FormOut,
    operation_id="bind_form_to_table",
    tags=["forms"],
)
def bind_form_to_table(form_id: int, payload: FormBinding, session: Session = Depends(get_session)) -> Form:
    form = get_or_404(session, Form, form_id, "form")
    table = get_or_404(session, Table, payload.table_id, "table")
    if table.database.app_id != form.app_id:
        raise HTTPException(status_code=422, detail="the table belongs to a different app than the form")
    table_fields = {field.name for field in table.fields}
    mapping = payload.field_mapping or {name: name for name in form.fields if name in table_fields}
    for form_input, table_field in mapping.items():
        if form_input not in form.fields:
            raise HTTPException(status_code=422, detail=f"form has no input named {form_input!r}")
        if table_field not in table_fields:
            raise HTTPException(status_code=422, detail=f"table has no field named {table_field!r}")
    form.table_id = table.id
    form.field_mapping = mapping
    session.flush()
    return form


@router.post(
    "/apps/{app_id}/auth",
    response_model=AuthFlowOut,
    status_code=201,
    operation_id="create_auth_flow",
    tags=["auth"],
)
def create_auth_flow(app_id: int, payload: AuthFlowCreate, session: Session = Depends(get_session)) -> AuthFlow:
    app = get_or_404(session, App, app_id, "app")
    if session.scalar(select(AuthFlow).where(AuthFlow.app_id == app.id)):
        raise HTTPException(status_code=409, detail="this app already has an auth flow")
    if payload.method.startswith("oauth") and payload.require_verification:
        payload = payload.model_copy(update={"require_verification": False})
    flow = AuthFlow(
        app_id=app.id,
        method=payload.method,
        require_verification=payload.require_verification,
        roles=payload.roles,
    )
    session.add(flow)
    session.flush()
    return flow


@router.post(
    "/apps/{app_id}/publish", response_model=PublishOut, operation_id="publish_site", tags=["publishing"]
)
def publish_site(app_id: int, payload: PublishRequest, session: Session = Depends(get_session)) -> PublishOut:
    app = get_or_404(session, App, app_id, "app")
    if not app.pages:
        raise HTTPException(status_code=422, detail="an app needs at least one page before it can be published")
    if payload.custom_domain and payload.environment != "production":
        raise HTTPException(status_code=422, detail="custom domains are only available in production")
    slug = app.name.lower().replace(" ", "-")
    url = f"https://{payload.custom_domain}" if payload.custom_domain else f"https://{slug}.{payload.environment}.nocode.example"
    session.add(Deployment(app_id=app.id, environment=payload.environment, url=url))
    return PublishOut(app_id=app.id, environment=payload.environment, url=url)
