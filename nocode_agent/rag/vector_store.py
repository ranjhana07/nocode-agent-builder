from __future__ import annotations

from typing import Protocol

import numpy as np
from langchain_core.embeddings import Embeddings

from nocode_agent.config import Settings
from nocode_agent.rag.filters import MetadataFilter, apply_filter
from nocode_agent.rag.types import Chunk, ScoredChunk


class VectorIndex(Protocol):
    def add(self, chunks: list[Chunk]) -> None: ...

    def search(self, query: str, k: int, metadata_filter: MetadataFilter | None = None) -> list[ScoredChunk]: ...

    def all_chunks(self) -> list[Chunk]: ...

    def count(self) -> int: ...

    def reset(self) -> None: ...


class InMemoryVectorIndex:
    def __init__(self, embeddings: Embeddings) -> None:
        self.embeddings = embeddings
        self.chunks: list[Chunk] = []
        self.matrix = np.zeros((0, 0), dtype=np.float32)

    def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        vectors = np.asarray(self.embeddings.embed_documents([chunk.text for chunk in chunks]), dtype=np.float32)
        self.matrix = vectors if not len(self.chunks) else np.vstack([self.matrix, vectors])
        self.chunks.extend(chunks)

    def search(self, query: str, k: int, metadata_filter: MetadataFilter | None = None) -> list[ScoredChunk]:
        if not self.chunks:
            return []
        query_vector = np.asarray(self.embeddings.embed_query(query), dtype=np.float32)
        scores = self.matrix @ query_vector
        order = np.argsort(-scores)
        results: list[ScoredChunk] = []
        for position in order:
            chunk = self.chunks[int(position)]
            if metadata_filter and not metadata_filter.matches(chunk.metadata):
                continue
            results.append(ScoredChunk(chunk, float(scores[position])))
            if len(results) == k:
                break
        return results

    def all_chunks(self) -> list[Chunk]:
        return list(self.chunks)

    def count(self) -> int:
        return len(self.chunks)

    def reset(self) -> None:
        self.chunks = []
        self.matrix = np.zeros((0, 0), dtype=np.float32)


class ChromaVectorIndex:
    def __init__(self, embeddings: Embeddings, settings: Settings) -> None:
        import chromadb

        self.embeddings = embeddings
        self.collection_name = settings.chroma_collection
        if settings.chroma_host:
            self.client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        else:
            self.client = chromadb.PersistentClient(path=str(settings.chroma_path))
        self.collection = self._open()

    def _open(self):
        return self.client.get_or_create_collection(self.collection_name, metadata={"hnsw:space": "cosine"})

    def add(self, chunks: list[Chunk], batch_size: int = 64) -> None:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            self.collection.upsert(
                ids=[chunk.id for chunk in batch],
                documents=[chunk.text for chunk in batch],
                metadatas=[chunk.metadata for chunk in batch],
                embeddings=self.embeddings.embed_documents([chunk.text for chunk in batch]),
            )

    def search(self, query: str, k: int, metadata_filter: MetadataFilter | None = None) -> list[ScoredChunk]:
        where = metadata_filter.to_chroma_where() if metadata_filter else None
        response = self.collection.query(
            query_embeddings=[self.embeddings.embed_query(query)],
            n_results=min(k, max(self.count(), 1)),
            where=where,
        )
        results: list[ScoredChunk] = []
        for identifier, text, metadata, distance in zip(
            response["ids"][0], response["documents"][0], response["metadatas"][0], response["distances"][0]
        ):
            chunk = Chunk(id=identifier, text=text, metadata=dict(metadata))
            if metadata_filter and metadata_filter.section_contains and not metadata_filter.matches(chunk.metadata):
                continue
            results.append(ScoredChunk(chunk, 1.0 - float(distance)))
        return results

    def all_chunks(self) -> list[Chunk]:
        payload = self.collection.get()
        return [
            Chunk(id=identifier, text=text, metadata=dict(metadata))
            for identifier, text, metadata in zip(payload["ids"], payload["documents"], payload["metadatas"])
        ]

    def count(self) -> int:
        return self.collection.count()

    def reset(self) -> None:
        self.client.delete_collection(self.collection_name)
        self.collection = self._open()


def select_chunks(chunks: list[Chunk], metadata_filter: MetadataFilter | None) -> list[Chunk]:
    return apply_filter(chunks, metadata_filter)
