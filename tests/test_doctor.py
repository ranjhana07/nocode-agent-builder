from __future__ import annotations

import httpx

from nocode_agent import doctor
from nocode_agent.config import Settings


def test_docs_check_counts_markdown_files() -> None:
    check = doctor.check_docs(Settings())
    assert check.ok
    assert "markdown files" in check.detail


def test_docs_check_fails_for_an_empty_folder(tmp_path) -> None:
    assert not doctor.check_docs(Settings(docs_dir=tmp_path, openapi_path=tmp_path / "openapi.json")).ok


def test_llm_key_check_reads_the_environment(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert not doctor.check_llm_key().ok
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert doctor.check_llm_key().ok


def test_platform_check_reports_status_and_failures(monkeypatch) -> None:
    monkeypatch.setattr(doctor.httpx, "get", lambda *args, **kwargs: httpx.Response(200))
    assert doctor.check_platform(Settings()).ok

    def refuse(*args, **kwargs):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(doctor.httpx, "get", refuse)
    result = doctor.check_platform(Settings())
    assert not result.ok and "ConnectError" in result.detail
