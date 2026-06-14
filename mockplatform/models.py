from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class App(Base):
    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    template: Mapped[str] = mapped_column(String(40), default="blank")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    pages: Mapped[list[Page]] = relationship(back_populates="app", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"))
    title: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(80))
    layout: Mapped[str] = mapped_column(String(20), default="single")

    app: Mapped[App] = relationship(back_populates="pages")
    components: Mapped[list[Component]] = relationship(
        back_populates="page", cascade="all, delete-orphan", order_by="Component.position"
    )


class Component(Base):
    __tablename__ = "components"

    id: Mapped[int] = mapped_column(primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"))
    type: Mapped[str] = mapped_column(String(30))
    props: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    position: Mapped[int] = mapped_column(Integer, default=0)

    page: Mapped[Page] = relationship(back_populates="components")


class Database(Base):
    __tablename__ = "databases"

    id: Mapped[int] = mapped_column(primary_key=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"))
    name: Mapped[str] = mapped_column(String(80))

    tables: Mapped[list[Table]] = relationship(back_populates="database", cascade="all, delete-orphan")


class Table(Base):
    __tablename__ = "tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    database_id: Mapped[int] = mapped_column(ForeignKey("databases.id"))
    name: Mapped[str] = mapped_column(String(80))
    primary_key: Mapped[str] = mapped_column(String(80), default="id")

    database: Mapped[Database] = relationship(back_populates="tables")
    fields: Mapped[list[Field]] = relationship(back_populates="table", cascade="all, delete-orphan")
    records: Mapped[list[Record]] = relationship(back_populates="table", cascade="all, delete-orphan")


class Field(Base):
    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id"))
    name: Mapped[str] = mapped_column(String(80))
    type: Mapped[str] = mapped_column(String(20))
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    default: Mapped[Any] = mapped_column(JSON, nullable=True)
    enum_values: Mapped[list[str]] = mapped_column(JSON, default=list)

    table: Mapped[Table] = relationship(back_populates="fields")


class Relation(Base):
    __tablename__ = "relations"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_table_id: Mapped[int] = mapped_column(ForeignKey("tables.id"))
    to_table_id: Mapped[int] = mapped_column(ForeignKey("tables.id"))
    kind: Mapped[str] = mapped_column(String(20))
    field_name: Mapped[str] = mapped_column(String(80))


class Record(Base):
    __tablename__ = "records"

    id: Mapped[int] = mapped_column(primary_key=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id"))
    data: Mapped[dict[str, Any]] = mapped_column(JSON)

    table: Mapped[Table] = relationship(back_populates="records")


class Form(Base):
    __tablename__ = "forms"

    id: Mapped[int] = mapped_column(primary_key=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"))
    name: Mapped[str] = mapped_column(String(80))
    fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    submit_label: Mapped[str] = mapped_column(String(40), default="Submit")
    table_id: Mapped[int | None] = mapped_column(ForeignKey("tables.id"), nullable=True)
    field_mapping: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)


class AuthFlow(Base):
    __tablename__ = "auth_flows"

    id: Mapped[int] = mapped_column(primary_key=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), unique=True)
    method: Mapped[str] = mapped_column(String(30))
    require_verification: Mapped[bool] = mapped_column(Boolean, default=True)
    roles: Mapped[list[str]] = mapped_column(JSON, default=list)


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(primary_key=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"))
    environment: Mapped[str] = mapped_column(String(20))
    url: Mapped[str] = mapped_column(String(255))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
