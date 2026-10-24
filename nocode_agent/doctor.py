from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from nocode_agent.config import Settings


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def check_platform(settings: Settings) -> Check:
    try:
        response = httpx.get(f"{settings.platform_url}/health", timeout=3.0)
        return Check("platform", response.status_code == 200, f"{settings.platform_url} answered {response.status_code}")
    except httpx.HTTPError as error:
        return Check("platform", False, f"{settings.platform_url} unreachable: {error.__class__.__name__}")


def check_llm_key() -> Check:
    present = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return Check("llm key", present, "ANTHROPIC_API_KEY is set" if present else "ANTHROPIC_API_KEY is not set")


def check_docs(settings: Settings) -> Check:
    count = len(list(settings.docs_dir.rglob("*.md")))
    ok = count > 0 and settings.openapi_path.exists()
    return Check("docs", ok, f"{count} markdown files, openapi spec {'found' if settings.openapi_path.exists() else 'missing'}")


def check_index(settings: Settings) -> Check:
    try:
        from nocode_agent.rag.service import build_index

        count = build_index(settings).count()
    except Exception as error:
        return Check("index", False, f"cannot open the vector store: {error.__class__.__name__}")
    return Check("index", count > 0, f"{count} chunks in {settings.chroma_collection}")


def run_checks(settings: Settings) -> list[Check]:
    return [check_docs(settings), check_index(settings), check_platform(settings), check_llm_key()]
