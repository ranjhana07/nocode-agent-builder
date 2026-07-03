from __future__ import annotations

from pathlib import Path

from nocode_agent.embeddings import HashingEmbeddings
from nocode_agent.rag.filters import MetadataFilter
from nocode_agent.rag.ingest import ingest_corpus, load_corpus
from nocode_agent.rag.vector_store import InMemoryVectorIndex

DOCS = Path("docs")
OPENAPI = Path("docs/openapi.json")


def test_corpus_has_all_doc_types() -> None:
    chunks = load_corpus(DOCS, OPENAPI)
    doc_types = {chunk.metadata["doc_type"] for chunk in chunks}
    assert {"guide", "api_spec", "openapi", "reference"} <= doc_types
    sources = {chunk.source for chunk in chunks}
    assert len([source for source in sources if source.endswith(".md")]) >= 25


def test_every_chunk_has_required_metadata() -> None:
    for chunk in load_corpus(DOCS, OPENAPI):
        assert chunk.metadata["source"]
        assert chunk.metadata["doc_type"]
        assert "workflow" in chunk.metadata
        assert chunk.metadata["version"]
        assert chunk.metadata["section"]


def test_ingest_into_memory_index_and_search() -> None:
    index = InMemoryVectorIndex(HashingEmbeddings())
    count = ingest_corpus(index, DOCS, OPENAPI, reset=True)
    assert count == index.count() > 100
    hits = index.search("publish the site to production", 5)
    assert hits
    assert hits == sorted(hits, key=lambda hit: -hit.score)
    only_specs = index.search("publish the site", 5, MetadataFilter(doc_types=("api_spec",)))
    assert only_specs and all(hit.chunk.metadata["doc_type"] == "api_spec" for hit in only_specs)
