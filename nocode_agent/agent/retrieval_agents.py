from __future__ import annotations

from nocode_agent.agent.deps import RetrieverFn
from nocode_agent.rag.filters import MetadataFilter
from nocode_agent.rag.query_filters import infer_filter
from nocode_agent.rag.retriever import HybridRetriever

DOC_TYPES = ("guide", "reference")
SPEC_TYPES = ("api_spec", "openapi")


def make_docs_agent(retriever: HybridRetriever) -> RetrieverFn:
    def search(query: str, k: int, widen: bool):
        metadata_filter = MetadataFilter(doc_types=DOC_TYPES)
        limit = k * 2 if widen else k
        return retriever.hybrid(query, limit, metadata_filter, multi_query=widen).hits

    return search


def make_spec_agent(retriever: HybridRetriever, workflows: set[str]) -> RetrieverFn:
    def search(query: str, k: int, widen: bool):
        metadata_filter = MetadataFilter(doc_types=SPEC_TYPES)
        if not widen:
            mentioned = infer_filter(query, workflows)
            metadata_filter = MetadataFilter(doc_types=SPEC_TYPES, workflows=mentioned.workflows)
        limit = k * 2 if widen else k
        return retriever.hybrid(query, limit, metadata_filter, multi_query=widen).hits

    return search
