from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from mockplatform.deps import get_or_404, get_session
from mockplatform.models import App, Component, Page
from mockplatform.schemas import AppCreate, AppOut, ComponentCreate, ComponentOut, PageCreate, PageOut

router = APIRouter()

MAX_PAGES_PER_APP = 50
MAX_COMPONENTS_PER_PAGE = 60


@router.post("/apps", response_model=AppOut, status_code=201, operation_id="create_app", tags=["apps"])
def create_app(payload: AppCreate, session: Session = Depends(get_session)) -> App:
    if session.scalar(select(App).where(App.name == payload.name)):
        raise HTTPException(status_code=409, detail=f"an app named {payload.name!r} already exists")
    app = App(name=payload.name, description=payload.description, template=payload.template)
    session.add(app)
    session.flush()
    return app


@router.post(
    "/apps/{app_id}/pages", response_model=PageOut, status_code=201, operation_id="create_page", tags=["pages"]
)
def create_page(app_id: int, payload: PageCreate, session: Session = Depends(get_session)) -> Page:
    app = get_or_404(session, App, app_id, "app")
    if len(app.pages) >= MAX_PAGES_PER_APP:
        raise HTTPException(status_code=422, detail=f"an app can hold at most {MAX_PAGES_PER_APP} pages")
    if any(page.slug == payload.slug for page in app.pages):
        raise HTTPException(status_code=409, detail=f"slug {payload.slug!r} is already used in this app")
    page = Page(app_id=app.id, title=payload.title, slug=payload.slug, layout=payload.layout)
    session.add(page)
    session.flush()
    return page


@router.post(
    "/pages/{page_id}/components",
    response_model=ComponentOut,
    status_code=201,
    operation_id="add_component",
    tags=["pages"],
)
def add_component(page_id: int, payload: ComponentCreate, session: Session = Depends(get_session)) -> Component:
    page = get_or_404(session, Page, page_id, "page")
    if len(page.components) >= MAX_COMPONENTS_PER_PAGE:
        raise HTTPException(status_code=422, detail=f"a page can hold at most {MAX_COMPONENTS_PER_PAGE} components")
    component = Component(page_id=page.id, type=payload.type, props=payload.props, position=payload.position)
    session.add(component)
    session.flush()
    return component
