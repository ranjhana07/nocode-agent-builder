from __future__ import annotations

import pytest

from nocode_agent.config import Settings
from nocode_agent.embeddings import HashingEmbeddings
from nocode_agent.rag.filters import MetadataFilter
from nocode_agent.rag.ingest import sync_corpus
from nocode_agent.rag.types import Chunk

chromadb = pytest.importorskip("chromadb")


@pytest.fixture()
def index(tmp_path):
    from nocode_agent.rag.vector_store import ChromaVectorIndex

    settings = Settings(chroma_path=tmp_path / "chroma", chroma_collection="test_docs")
    return ChromaVectorIndex(HashingEmbeddings(), settings)


def chunk(identifier: str, text: str, doc_type: str = "guide", workflow: str = "none") -> Chunk:
    return Chunk(identifier, text, {"source": f"{identifier}.md", "doc_type": doc_type, "workflow": workflow, "section": "s"})


def test_add_search_and_count(index) -> None:
    index.add([chunk("pub", "publish the site to production"), chunk("forms", "forms collect input from users")])
    assert index.count() == 2
    hits = index.search("publish production site", 2)
    assert hits[0].chunk.id == "pub"
    assert hits[0].score >= hits[1].score


def test_metadata_filters_are_pushed_down(index) -> None:
    index.add(
        [
            chunk("a", "publish site", "api_spec", "publish_site"),
            chunk("b", "publish site guide", "guide", "publish_site"),
            chunk("c", "publish other", "api_spec", "create_app"),
        ]
    )
    hits = index.search("publish", 5, MetadataFilter(doc_types=("api_spec",), workflows=("publish_site",)))
    assert [hit.chunk.id for hit in hits] == ["a"]


def test_upsert_delete_and_reset(index) -> None:
    index.add([chunk("a", "first"), chunk("b", "second")])
    index.add([chunk("a", "first edited")])
    assert index.count() == 2
    assert {item.id: item.text for item in index.all_chunks()}["a"] == "first edited"
    index.delete(["b"])
    assert index.count() == 1
    index.reset()
    assert index.count() == 0


def test_sync_works_against_chroma(index) -> None:
    report = sync_corpus(index, [chunk("a", "alpha"), chunk("b", "beta")])
    assert report.added == 2
    report = sync_corpus(index, [chunk("a", "alpha"), chunk("b", "beta edited")])
    assert (report.updated, report.unchanged) == (1, 1)
