from __future__ import annotations

from fastapi import FastAPI

from mockplatform import routes_app, routes_data, routes_ui
from mockplatform.db import database_url_from_env, make_engine, make_session_factory


def create_platform_app(database_url: str | None = None) -> FastAPI:
    app = FastAPI(
        title="Nocode Platform API",
        version="1.4.0",
        description="Workflow API of the Nocode platform: apps, pages, databases, forms, auth and publishing.",
    )
    engine = make_engine(database_url or database_url_from_env())
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)
    app.include_router(routes_ui.router)
    app.include_router(routes_data.router)
    app.include_router(routes_app.router)

    @app.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def build_default_app() -> FastAPI:
    return create_platform_app()
