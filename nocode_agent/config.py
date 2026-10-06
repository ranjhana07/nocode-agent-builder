from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_model: str = "claude-sonnet-5-5"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 2048

    embedding_backend: str = "sentence-transformers"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_cache_path: Path | None = None
    rerank_backend: str = "cross-encoder"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    docs_dir: Path = Path("docs")
    openapi_path: Path = Path("docs/openapi.json")
    docs_version: str = "1.4"

    chroma_path: Path = Path("chroma_data")
    chroma_host: str | None = None
    chroma_port: int = 8000
    chroma_collection: str = "nocode_docs"

    platform_url: str = "http://localhost:9000"
    platform_api_key: str | None = None
    platform_max_retries: int = Field(default=3, ge=0)
    checkpoint_db: Path = Path("checkpoints.db")

    chunk_max_chars: int = Field(default=900, ge=200)
    chunk_overlap_chars: int = Field(default=120, ge=0)

    retrieval_top_k: int = Field(default=5, ge=1)
    retrieval_fetch_k: int = Field(default=20, ge=1)
    rrf_k: int = Field(default=60, ge=1)
    dense_weight: float = Field(default=1.0, ge=0)
    sparse_weight: float = Field(default=1.0, ge=0)
    multi_query_count: int = Field(default=3, ge=1)

    grader_relevance_threshold: float = Field(default=0.5, ge=0, le=1)
    grader_min_relevant: int = Field(default=2, ge=1)
    max_retrieval_attempts: int = Field(default=3, ge=1)
    max_repair_attempts: int = Field(default=2, ge=0)

    langsmith_dataset: str = "nocode-agent-eval"
    eval_dataset_path: Path = Path("data/eval/questions.jsonl")
    retrieval_queries_path: Path = Path("data/eval/retrieval_queries.jsonl")


@lru_cache
def get_settings() -> Settings:
    return Settings()
