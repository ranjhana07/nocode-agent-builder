from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nocode_agent.rag.types import Chunk, Metadata

FILTER_FIELDS = ("doc_type", "workflow", "version", "source")


@dataclass(frozen=True)
class MetadataFilter:
    doc_types: tuple[str, ...] = ()
    workflows: tuple[str, ...] = ()
    version: str | None = None
    source: str | None = None
    section_contains: str | None = None

    def is_empty(self) -> bool:
        return not (self.doc_types or self.workflows or self.version or self.source or self.section_contains)

    def matches(self, metadata: Metadata) -> bool:
        if self.doc_types and metadata.get("doc_type") not in self.doc_types:
            return False
        if self.workflows and metadata.get("workflow") not in self.workflows:
            return False
        if self.version and metadata.get("version") != self.version:
            return False
        if self.source and metadata.get("source") != self.source:
            return False
        if self.section_contains and self.section_contains.lower() not in metadata.get("section", "").lower():
            return False
        return True

    def to_chroma_where(self) -> dict[str, Any] | None:
        clauses: list[dict[str, Any]] = []
        if self.doc_types:
            clauses.append({"doc_type": {"$in": list(self.doc_types)}})
        if self.workflows:
            clauses.append({"workflow": {"$in": list(self.workflows)}})
        if self.version:
            clauses.append({"version": self.version})
        if self.source:
            clauses.append({"source": self.source})
        if not clauses:
            return None
        return clauses[0] if len(clauses) == 1 else {"$and": clauses}

    def with_doc_types(self, *doc_types: str) -> MetadataFilter:
        return MetadataFilter(doc_types, self.workflows, self.version, self.source, self.section_contains)


def apply_filter(chunks: list[Chunk], metadata_filter: MetadataFilter | None) -> list[Chunk]:
    if metadata_filter is None or metadata_filter.is_empty():
        return list(chunks)
    return [chunk for chunk in chunks if metadata_filter.matches(chunk.metadata)]
