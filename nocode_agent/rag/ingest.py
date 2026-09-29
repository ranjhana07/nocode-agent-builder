from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path

from nocode_agent.rag.openapi_splitter import split_openapi
from nocode_agent.rag.splitter import SplitterConfig, split_markdown
from nocode_agent.rag.types import Chunk
from nocode_agent.rag.vector_store import VectorIndex


def load_markdown_chunks(docs_dir: Path, config: SplitterConfig | None = None) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(docs_dir.rglob("*.md")):
        source = path.relative_to(docs_dir).as_posix()
        chunks.extend(split_markdown(path.read_text(encoding="utf-8"), source, config))
    return chunks


def load_openapi_chunks(openapi_path: Path, docs_dir: Path) -> list[Chunk]:
    if not openapi_path.exists():
        return []
    spec = json.loads(openapi_path.read_text(encoding="utf-8"))
    try:
        source = openapi_path.resolve().relative_to(docs_dir.resolve()).as_posix()
    except ValueError:
        source = openapi_path.name
    return split_openapi(spec, source)


def load_corpus(docs_dir: Path, openapi_path: Path, config: SplitterConfig | None = None) -> list[Chunk]:
    return load_markdown_chunks(docs_dir, config) + load_openapi_chunks(openapi_path, docs_dir)


def splitter_config(settings) -> SplitterConfig:
    return SplitterConfig(settings.chunk_max_chars, settings.chunk_overlap_chars)


def ingest_corpus(
    index: VectorIndex, docs_dir: Path, openapi_path: Path, reset: bool = False, config: SplitterConfig | None = None
) -> int:
    if reset:
        index.reset()
    chunks = load_corpus(docs_dir, openapi_path, config)
    index.add(chunks)
    return len(chunks)


@dataclass
class SyncReport:
    added: int
    updated: int
    removed: int
    unchanged: int


def with_content_hash(chunk: Chunk) -> Chunk:
    digest = hashlib.sha1(chunk.text.encode("utf-8")).hexdigest()[:12]
    return replace(chunk, metadata={**chunk.metadata, "content_hash": digest})


def sync_corpus(index: VectorIndex, chunks: list[Chunk]) -> SyncReport:
    incoming = {chunk.id: with_content_hash(chunk) for chunk in chunks}
    existing = {chunk.id: chunk.metadata.get("content_hash", "") for chunk in index.all_chunks()}
    stale = [chunk_id for chunk_id in existing if chunk_id not in incoming]
    changed = [chunk_id for chunk_id, chunk in incoming.items() if chunk_id in existing and existing[chunk_id] != chunk.metadata["content_hash"]]
    new = [chunk_id for chunk_id in incoming if chunk_id not in existing]
    index.delete(stale + changed)
    index.add([incoming[chunk_id] for chunk_id in new + changed])
    unchanged = len(incoming) - len(new) - len(changed)
    return SyncReport(added=len(new), updated=len(changed), removed=len(stale), unchanged=unchanged)
