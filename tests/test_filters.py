from __future__ import annotations

from nocode_agent.rag.filters import MetadataFilter, apply_filter
from nocode_agent.rag.types import Chunk


def chunk(identifier: str, **metadata: str) -> Chunk:
    return Chunk(id=identifier, text=identifier, metadata=metadata)


CHUNKS = [
    chunk("a", doc_type="guide", workflow="create_app", version="1.4", section="Templates"),
    chunk("b", doc_type="api_spec", workflow="create_app", version="1.4", section="Errors"),
    chunk("c", doc_type="api_spec", workflow="create_page", version="1.3", section="Endpoint"),
    chunk("d", doc_type="openapi", workflow="none", version="1.4", section="POST /apps"),
]


def ids(chunks: list[Chunk]) -> list[str]:
    return [item.id for item in chunks]


def test_empty_filter_keeps_everything() -> None:
    assert ids(apply_filter(CHUNKS, MetadataFilter())) == ["a", "b", "c", "d"]
    assert ids(apply_filter(CHUNKS, None)) == ["a", "b", "c", "d"]


def test_doc_type_filter() -> None:
    result = apply_filter(CHUNKS, MetadataFilter(doc_types=("api_spec", "openapi")))
    assert ids(result) == ["b", "c", "d"]


def test_filters_combine_with_and() -> None:
    result = apply_filter(CHUNKS, MetadataFilter(doc_types=("api_spec",), workflows=("create_app",)))
    assert ids(result) == ["b"]


def test_version_and_section_filters() -> None:
    assert ids(apply_filter(CHUNKS, MetadataFilter(version="1.3"))) == ["c"]
    assert ids(apply_filter(CHUNKS, MetadataFilter(section_contains="errors"))) == ["b"]


def test_chroma_where_clause() -> None:
    assert MetadataFilter().to_chroma_where() is None
    assert MetadataFilter(version="1.4").to_chroma_where() == {"version": "1.4"}
    where = MetadataFilter(doc_types=("guide",), workflows=("create_app",)).to_chroma_where()
    assert where == {"$and": [{"doc_type": {"$in": ["guide"]}}, {"workflow": {"$in": ["create_app"]}}]}
