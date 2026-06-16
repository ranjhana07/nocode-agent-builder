from __future__ import annotations

from collections.abc import Iterator

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from mockplatform.db import session_scope


def get_session(request: Request) -> Iterator[Session]:
    yield from session_scope(request.app.state.session_factory)


def get_or_404[T](session: Session, model: type[T], object_id: int, label: str) -> T:
    instance = session.get(model, object_id)
    if instance is None:
        raise HTTPException(status_code=404, detail=f"{label} {object_id} not found")
    return instance
