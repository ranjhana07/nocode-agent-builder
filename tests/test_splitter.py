from __future__ import annotations

import json
from pathlib import Path

from nocode_agent.rag.openapi_splitter import split_openapi
from nocode_agent.rag.splitter import SplitterConfig, parse_front_matter, split_markdown, split_text

SAMPLE = "
".join(
    [
        '---',
        'title: Sample doc',
        'doc_type: guide',
        'workflow: create_app',
        'version: "1.4"',
        '---',
        '',
        '# Sample doc',
        '',
        'Intro paragraph.',
        '',
        '## Setup',
        '',
        'Step one.',
        '',
        '### Details',
        '',
        'Deep detail.',
        '',
        '## Limits',
        '',
        '```',
        '# not a heading',
        '```',
        '',
        'Limit text.',
    ]
) + "
"


def test_front_matter_is_parsed() -> None:
    metadata, body = parse_front_matter(SAMPLE)
    assert metadata["doc_type"] == "guide"
    assert metadata["version"] == "1.4"
    assert body.startswith("# Sample doc")


def test_sections_carry_heading_trail() -> None:
    chunks = split_markdown(SAMPLE, "guides/sample.md")
    sections = [chunk.metadata["section"] for chunk in chunks]
    assert "Sample doc" in sections
    assert "Sample doc > Setup > Details" in sections
    assert all(chunk.metadata["workflow"] == "create_app" for chunk in chunks)


def test_fenced_hash_lines_are_not_headings() -> None:
    chunks = split_markdown(SAMPLE, "guides/sample.md")
    limits = next(chunk for chunk in chunks if chunk.metadata["section"].endswith("Limits"))
    assert "# not a heading" in limits.text


def test_chunk_ids_are_unique_and_prefixed_with_source() -> None:
    chunks = split_markdown(SAMPLE, "guides/sample.md")
    assert len({chunk.id for chunk in chunks}) == len(chunks)
    assert all(chunk.id.startswith("guides/sample.md#") for chunk in chunks)


def test_long_sections_are_split_with_overlap() -> None:
    paragraphs = [f"Paragraph {index} " + "word " * 40 for index in range(12)]
    pieces = split_text("\n\n".join(paragraphs), SplitterConfig(max_chars=500, overlap_chars=60))
    assert len(pieces) > 2
    assert all(len(piece) <= 700 for piece in pieces)
    assert pieces[1].startswith(pieces[0][-60:].strip()[:20]) or pieces[0][-20:] in pieces[1]


def test_short_text_is_returned_whole() -> None:
    assert split_text("short", SplitterConfig()) == ["short"]


def test_openapi_chunks_one_per_operation() -> None:
    spec = json.loads(Path("docs/openapi.json").read_text(encoding="utf-8"))
    chunks = split_openapi(spec, "openapi.json")
    operations = [chunk for chunk in chunks if chunk.metadata["section"].startswith(("POST", "GET"))]
    assert len(operations) == 12
    create_table = next(chunk for chunk in operations if chunk.metadata["workflow"] == "create_table")
    assert "POST /databases/{database_id}/tables" in create_table.text
    assert "snake_case" in create_table.text
    assert create_table.metadata["doc_type"] == "openapi"
