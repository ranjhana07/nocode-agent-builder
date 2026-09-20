from __future__ import annotations

from pathlib import Path

import typer

from nocode_agent.config import get_settings
from nocode_agent.evals.retrieval_runner import run_retrieval_eval
from nocode_agent.rag.eval import format_table
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


@app.command()
def ask(question: str, thread: str | None = typer.Option(None, "--thread")) -> None:
    from nocode_agent.agent.runtime import build_runtime

    state = build_runtime().run(question, thread, intent="question")
    typer.echo(state["answer"])
    sources = sorted({document["metadata"].get("source", "") for document in state.get("documents", [])})
    if sources:
        typer.echo("sources: " + ", ".join(sources))


@app.command()
def run(
    request: str,
    thread: str | None = typer.Option(None, "--thread"),
    quiet: bool = typer.Option(False, "--quiet", help="Only print the final summary"),
) -> None:
    from nocode_agent.agent.runtime import build_runtime

    final: dict = {}
    for event in build_runtime().stream(request, thread, intent="build"):
        if event["node"] == "__end__":
            final = event["state"]
        elif not quiet:
            for line in event["trace"]:
                typer.echo(f"  {event['node']}: {line}")
    typer.echo(final.get("answer", ""))
    if final.get("status") == "failed":
        raise typer.Exit(code=1)


@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run("nocode_agent.api.app:build_app", host=host, port=port, factory=True)


@app.command("platform")
def run_platform(host: str = "0.0.0.0", port: int = 9000) -> None:
    import uvicorn

    uvicorn.run("mockplatform.main:build_default_app", host=host, port=port, factory=True)


@app.command()
def dataset() -> None:
    from nocode_agent.evals.dataset import generate_datasets

    settings = get_settings()
    questions, queries = generate_datasets(settings.docs_dir, settings.eval_dataset_path, settings.retrieval_queries_path)
    typer.echo(f"wrote {questions} questions and {queries} retrieval queries")


eval_app = typer.Typer(help="Run evaluations", no_args_is_help=True)
app.add_typer(eval_app, name="eval")


@eval_app.command("retrieval")
def eval_retrieval(
    in_memory: bool = typer.Option(False, "--in-memory"),
    multi_query: bool = typer.Option(False, "--multi-query", help="Include the multi-query system, needs an LLM key"),
    limit: int | None = typer.Option(None, "--limit"),
    results_dir: Path = typer.Option(Path("results"), "--results-dir"),
) -> None:
    settings = get_settings()
    llm = None
    if multi_query:
        from nocode_agent.llm import build_chat_model

        llm = build_chat_model(settings)
    stack = build_rag_stack(settings, llm=llm, persistent=not in_memory)
    results = run_retrieval_eval(stack.retriever, settings, multi_query, results_dir, limit)
    typer.echo(format_table(results))


@eval_app.command("agent")
def eval_agent(
    limit: int | None = typer.Option(None, "--limit"),
    local: bool = typer.Option(False, "--local", help="Score locally instead of through LangSmith"),
    results_dir: Path = typer.Option(Path("results"), "--results-dir"),
    experiment: str = typer.Option("corrective-rag", "--experiment"),
) -> None:
    from nocode_agent.agent.runtime import build_runtime
    from nocode_agent.evals.agent_target import make_target
    from nocode_agent.evals.langsmith_eval import run_langsmith_eval
    from nocode_agent.evals.local_eval import run_local_eval, write_summary
    from nocode_agent.llm import build_chat_model

    settings = get_settings()
    runtime = build_runtime(settings)
    judge = build_chat_model(settings)
    target = make_target(runtime)
    if local:
        summary = run_local_eval(target, judge, settings.eval_dataset_path, limit)
        write_summary(summary, results_dir / "agent_eval.json")
        for metric, value in summary["metrics"].items():
            typer.echo(f"{metric}: {value:.3f}")
        return
    run_langsmith_eval(target, judge, settings.eval_dataset_path, settings.langsmith_dataset, experiment, limit)


if __name__ == "__main__":
    app()
