from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

Metadata = dict[str, str]


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    metadata: Metadata = field(default_factory=dict)

    @property
    def source(self) -> str:
        return self.metadata.get("source", "")

    @property
    def workflow(self) -> str:
        return self.metadata.get("workflow", "")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "text": self.text, "metadata": dict(self.metadata)}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Chunk:
        return cls(id=payload["id"], text=payload["text"], metadata=dict(payload.get("metadata", {})))


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: float
