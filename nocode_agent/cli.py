from __future__ import annotations

import typer

from nocode_agent.config import get_settings
from nocode_agent.rag.filters import MetadataFilter
from nocode_agent.rag.ingest import ingest_corpus
from nocode_agent.rag.service import build_index, build_rag_stack

app = typer.Typer(help="Build apps on the Nocode platform from plain English", no_args_is_help=True)


@app.command()
def ingest(
    reset: bool = typer.Option(False, "--reset", help="Drop the collection before ingesting"),
    in_memory: bool = typer.Option(False, "--in-memory", help="Use a throwaway in-memory index"),
) -> None:
    settings = get_settings()
    index = build_index(settings, persistent=not in_memory)
    count = ingest_corpus(index, settings.docs_dir, settings.openapi_path, reset=reset)
    typer.echo(f"ingested {count} chunks into {settings.chroma_collection}")


@app.command()
def search(
    query: str,
    k: int = typer.Option(5, "--k"),
    mode: str = typer.Option("hybrid", "--mode", help="vector or hybrid"),
    doc_type: str | None = typer.Option(None, "--doc-type"),
    workflow: str | None = typer.Option(None, "--workflow"),
) -> None:
    stack = build_rag_stack()
    metadata_filter = MetadataFilter(
        doc_types=(doc_type,) if doc_type else (), workflows=(workflow,) if workflow else ()
    )
    if mode == "vector":
        result = stack.retriever.vector_only(query, k, metadata_filter)
    else:
        result = stack.retriever.hybrid(query, k, metadata_filter, multi_query=False)
    for rank, hit in enumerate(result.hits, start=1):
        typer.echo(f"{rank}. [{hit.score:.3f}] {hit.chunk.id}  ({hit.chunk.metadata['section']})")


if __name__ == "__main__":
    app()
