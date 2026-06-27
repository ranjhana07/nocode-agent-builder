from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from nocode_agent.rag.types import Chunk, Metadata

HEADING = re.compile(r"^(#{1,4})\s+(.*?)\s*$")
FENCE = re.compile(r"^```")


@dataclass(frozen=True)
class SplitterConfig:
    max_chars: int = 900
    overlap_chars: int = 120


def parse_front_matter(text: str) -> tuple[Metadata, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    header = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    values: Metadata = {}
    for line in header.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip().strip('"')
    return values, body


def iter_sections(body: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    trail: list[str] = []
    buffer: list[str] = []
    in_fence = False

    def flush() -> None:
        text = "\n".join(buffer).strip()
        if text:
            sections.append((" > ".join(trail), text))
        buffer.clear()

    for line in body.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
        match = None if in_fence else HEADING.match(line)
        if match:
            flush()
            level = len(match.group(1))
            del trail[level - 1 :]
            trail.append(match.group(2))
        else:
            buffer.append(line)
    flush()
    return sections


def split_text(text: str, config: SplitterConfig) -> list[str]:
    if len(text) <= config.max_chars:
        return [text]
    paragraphs = [part for part in re.split(r"\n\s*\n", text) if part.strip()]
    pieces: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= config.max_chars:
            current = candidate
            continue
        if current:
            pieces.append(current)
            tail = current[-config.overlap_chars :] if config.overlap_chars else ""
            current = f"{tail}\n\n{paragraph}" if tail else paragraph
        else:
            current = paragraph
        while len(current) > config.max_chars:
            pieces.append(current[: config.max_chars])
            current = current[config.max_chars - config.overlap_chars :]
    if current.strip():
        pieces.append(current)
    return pieces


def split_markdown(text: str, source: str, config: SplitterConfig | None = None) -> list[Chunk]:
    config = config or SplitterConfig()
    front_matter, body = parse_front_matter(text)
    title = front_matter.get("title", Path(source).stem)
    base: Metadata = {
        "source": source,
        "title": title,
        "doc_type": front_matter.get("doc_type", "guide"),
        "workflow": front_matter.get("workflow", "none"),
        "version": front_matter.get("version", ""),
    }
    chunks: list[Chunk] = []
    for section, section_text in iter_sections(body):
        for part_index, part in enumerate(split_text(section_text, config)):
            heading = section or title
            chunk_text = f"{title} | {heading}\n{part}"
            chunk_id = f"{source}#{len(chunks)}"
            chunks.append(Chunk(id=chunk_id, text=chunk_text, metadata={**base, "section": heading, "part": str(part_index)}))
    return chunks
