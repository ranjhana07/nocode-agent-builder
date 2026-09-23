from __future__ import annotations

from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel

from nocode_agent.config import Settings, get_settings
from nocode_agent.embeddings import build_embeddings
from nocode_agent.rag.bm25 import BM25Index
from nocode_agent.rag.ingest import load_corpus, splitter_config
from nocode_agent.rag.rerank import build_reranker
from nocode_agent.rag.retriever import HybridRetriever
from nocode_agent.rag.vector_store import ChromaVectorIndex, InMemoryVectorIndex, VectorIndex


@dataclass
class RagStack:
    index: VectorIndex
    retriever: HybridRetriever


def build_index(settings: Settings, persistent: bool = True) -> VectorIndex:
    embeddings = build_embeddings(settings)
    if persistent:
        return ChromaVectorIndex(embeddings, settings)
    return InMemoryVectorIndex(embeddings)


def build_rag_stack(
    settings: Settings | None = None,
    llm: BaseChatModel | None = None,
    persistent: bool = True,
) -> RagStack:
    settings = settings or get_settings()
    index = build_index(settings, persistent)
    if index.count() == 0:
        index.add(load_corpus(settings.docs_dir, settings.openapi_path, splitter_config(settings)))
    retriever = HybridRetriever(
        index,
        BM25Index(index.all_chunks()),
        reranker=build_reranker(settings),
        llm=llm,
        rrf_k=settings.rrf_k,
        fetch_k=settings.retrieval_fetch_k,
        multi_query_count=settings.multi_query_count,
    )
    return RagStack(index=index, retriever=retriever)
