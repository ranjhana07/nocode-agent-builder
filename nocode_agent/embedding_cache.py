from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from langchain_core.embeddings import Embeddings


class CachedEmbeddings(Embeddings):
    def __init__(self, inner: Embeddings, path: Path, namespace: str) -> None:
        self.inner = inner
        self.namespace = namespace
        self.connection = sqlite3.connect(str(path), check_same_thread=False)
        self.connection.execute("CREATE TABLE IF NOT EXISTS vectors (key TEXT PRIMARY KEY, vector TEXT NOT NULL)")
        self.hits = 0
        self.misses = 0

    def key(self, text: str) -> str:
        return hashlib.sha256(f"{self.namespace}\0{text}".encode("utf-8")).hexdigest()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        keys = [self.key(text) for text in texts]
        found: dict[str, list[float]] = {}
        for start in range(0, len(keys), 500):
            batch = keys[start : start + 500]
            marks = ",".join("?" * len(batch))
            rows = self.connection.execute(f"SELECT key, vector FROM vectors WHERE key IN ({marks})", batch).fetchall()
            found.update({key: json.loads(vector) for key, vector in rows})
        missing = [index for index, key in enumerate(keys) if key not in found]
        if missing:
            fresh = self.inner.embed_documents([texts[index] for index in missing])
            with self.connection:
                for index, vector in zip(missing, fresh):
                    found[keys[index]] = vector
                    self.connection.execute(
                        "INSERT OR REPLACE INTO vectors (key, vector) VALUES (?, ?)", (keys[index], json.dumps(vector))
                    )
        self.misses += len(missing)
        self.hits += len(texts) - len(missing)
        return [found[key] for key in keys]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
