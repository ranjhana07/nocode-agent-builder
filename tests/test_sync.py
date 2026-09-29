from __future__ import annotations

from nocode_agent.embeddings import HashingEmbeddings
from nocode_agent.rag.ingest import sync_corpus
from nocode_agent.rag.types import Chunk
from nocode_agent.rag.vector_store import InMemoryVectorIndex


def chunks(**texts: str) -> list[Chunk]:
    return [Chunk(chunk_id, text, {"source": f"{chunk_id}.md", "doc_type": "guide"}) for chunk_id, text in texts.items()]


def test_first_sync_adds_everything() -> None:
    index = InMemoryVectorIndex(HashingEmbeddings())
    report = sync_corpus(index, chunks(a="alpha text", b="beta text"))
    assert (report.added, report.updated, report.removed, report.unchanged) == (2, 0, 0, 0)
    assert index.count() == 2


def test_second_sync_skips_unchanged_chunks() -> None:
    index = InMemoryVectorIndex(HashingEmbeddings())
    sync_corpus(index, chunks(a="alpha text", b="beta text"))
    report = sync_corpus(index, chunks(a="alpha text", b="beta text"))
    assert (report.added, report.updated, report.removed, report.unchanged) == (0, 0, 0, 2)


def test_changed_and_removed_chunks_are_reconciled() -> None:
    index = InMemoryVectorIndex(HashingEmbeddings())
    sync_corpus(index, chunks(a="alpha text", b="beta text", c="gamma text"))
    report = sync_corpus(index, chunks(a="alpha text edited", c="gamma text", d="delta text"))
    assert (report.added, report.updated, report.removed, report.unchanged) == (1, 1, 1, 1)
    texts = {chunk.id: chunk.text for chunk in index.all_chunks()}
    assert texts == {"a": "alpha text edited", "c": "gamma text", "d": "delta text"}
    assert index.search("alpha text edited", 1)[0].chunk.id == "a"


def test_delete_everything_leaves_a_usable_index() -> None:
    index = InMemoryVectorIndex(HashingEmbeddings())
    sync_corpus(index, chunks(a="alpha"))
    index.delete(["a"])
    assert index.count() == 0
    assert index.search("alpha", 3) == []
