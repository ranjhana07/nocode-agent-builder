# nocode-agent-builder

Agents that build apps, websites and databases on a no-code platform from plain English.

A LangGraph graph takes a request such as "build me a customer portal with a customers table and email sign in", plans the build, looks up the relevant platform documentation and API specs before every call, checks the call arguments against the OpenAPI schema, and runs the platform's workflows as tools. The platform here is a small FastAPI mock with 12 workflows backed by SQLite, so the whole pipeline runs locally.

## How it works

```
                      request
                         |
                    [classify]
                    /         \
               build           question
                 |                |
            [planner]        [prepare_question]
                 |                |
          plan checker            |
         (replan on error)        |
                 |                |
          [prepare_step] <--+     |
                 |          |     |
                 v          |     v
        +------------------------------------+
        |        corrective RAG subgraph      |
        |                                     |
        |  [retrieve_docs] [retrieve_specs]   |
        |        \            /               |
        |           [merge]                   |
        |              |                      |
        |           [grade] -- rewrite -----> [rewrite] --+
        |              |    \- retrieve again > [widen] --+
        |              |                      |    (back to both retrievers)
        |           proceed / give up         |
        +--------------|----------------------+
                 |              |
                 v              v
          [generate_call]   [answer]
                 |              |
                 v             END
            [validate] --- errors, repairs left ---> [generate_call]
                 |
                 v
            [execute] ---- platform rejects, repairs left ---> [generate_call]
                 |
                 v
            [advance] -- more steps --> [prepare_step]
                 |
                 v
            [finalize] --> END
```

The shared state is a typed dict (`nocode_agent/agent/state.py`). Nodes only return the keys they change; `results` and `trace` use list-append reducers. Every run is checkpointed to SQLite, so a thread can be read back after it finishes.

Retrieval stack:

- Markdown aware splitting with front matter. Every chunk carries `doc_type`, `workflow`, `section`, `version` and `source`. The OpenAPI file is split per operation and per schema.
- ChromaDB for dense vectors, `rank_bm25` over the same chunks for sparse search, merged with reciprocal rank fusion.
- Optional multi-query expansion with the LLM, a cross-encoder reranker (falls back to a lexical reranker if the model cannot load), and metadata filters. The filters can be inferred from workflow names that appear in the query.

Corrective RAG:

- A docs agent (guides and references) and an API spec agent (spec pages and OpenAPI chunks) retrieve in parallel and their hits are interleaved.
- A grader scores every chunk from 0 to 1 with structured output. If enough chunks pass the threshold the step proceeds with only those chunks. If none pass, the query is rewritten. If only some pass, the search is repeated wider (more results, no workflow filter, multi-query on). After `MAX_RETRIEVAL_ATTEMPTS` the step proceeds with what it has, or gives up if nothing was relevant.
- Before a call is made, its arguments are checked against the JSON schema derived from the OpenAPI spec. Invalid calls, calls to a workflow other than the planned one, and calls the platform rejects go back to the drafting node with the error, up to `MAX_REPAIR_ATTEMPTS` times.

## Setup

Python 3.12 is required.

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps
cp .env.example .env
```

Set `ANTHROPIC_API_KEY` in `.env`. On CPU only machines install torch from the CPU index first:

```
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Docker:

```
docker compose up --build
```

This starts the mock platform on 9000, ChromaDB on 8001 and the agent API on 8000.

## Configuration

Everything is read from environment variables or `.env`. The ones you are most likely to change:

| variable | default | meaning |
| --- | --- | --- |
| `LLM_MODEL` | `claude-sonnet-5-5` | chat model used by the planner, grader, drafter and judges |
| `EMBEDDING_BACKEND` | `sentence-transformers` | `sentence-transformers` or `hashing` (offline, no model download) |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | model for the dense index |
| `RERANK_BACKEND` | `cross-encoder` | `cross-encoder` or `lexical` |
| `RERANK_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | cross-encoder checkpoint |
| `CHROMA_PATH` / `CHROMA_HOST` | `chroma_data` / unset | local persistent store, or a Chroma server |
| `PLATFORM_URL` | `http://localhost:9000` | where the 12 workflows are called |
| `RETRIEVAL_TOP_K`, `RETRIEVAL_FETCH_K` | 5, 20 | chunks per retriever, candidates before reranking |
| `GRADER_RELEVANCE_THRESHOLD`, `GRADER_MIN_RELEVANT` | 0.5, 2 | when the grader lets a step proceed |
| `MAX_RETRIEVAL_ATTEMPTS`, `MAX_REPAIR_ATTEMPTS`, `MAX_REPLANS` | 3, 2, 2 | loop caps |
| `API_TOKEN` | unset | if set, `/rag/query` and `/agent/*` need a bearer token |
| `EMBEDDING_CACHE_PATH` | unset | sqlite file that caches embeddings by model and text |

## Usage

Start the platform and index the docs:

```
builder platform --port 9000
builder ingest --reset
```

`builder ingest --sync` only embeds chunks whose text changed.

Ask a question about the platform:

```
builder ask "which workflow binds a form to a table, and what does it need?"
```

Build something:

```
builder run "build me a customer portal with a customers table, a signup form that saves into it, and email sign in"
builder run "build me a blog with an authors table" --dry-run
```

`--dry-run` plans, retrieves, drafts and validates every call, but does not call the platform. Ids returned by earlier steps are simulated so later steps can still refer to them. In drafted arguments a string such as `$app.id` is replaced with the id saved under the alias `app`.

Inspect retrieval:

```
builder search "make my site live" --mode hybrid --k 5
builder search "slug rules" --doc-type guide
builder doctor
```

API:

```
builder serve --port 8000
curl -N -X POST localhost:8000/agent/run -H 'content-type: application/json' \
  -d '{"request": "build me a todo app with a tasks table"}'
curl -X POST localhost:8000/rag/query -H 'content-type: application/json' \
  -d '{"query": "how do I publish to production", "k": 3}'
```

`/agent/run` streams server sent events: one `step` event per graph node (with its trace lines and elapsed milliseconds) and a final `final` event with the status, answer and the workflow calls made. Pass `"stream": false` for a single JSON response.

## Evaluation

Regenerate the datasets from the docs (deterministic, seed 7):

```
builder dataset
```

This writes `data/eval/questions.jsonl` (150 questions with reference answers, expected sources and, where it applies, the expected workflow) and `data/eval/retrieval_queries.jsonl` (the 150 questions plus 60 informal task phrasings, 12 workflows with 5 each).

Retrieval:

```
builder ingest --reset
builder eval retrieval --show-misses
```

Agent, scored by LLM-as-judge on groundedness and correctness, plus the wrong-tool-call rate and whether an expected source was retrieved. Needs `ANTHROPIC_API_KEY`; with `LANGSMITH_API_KEY` set it uploads the dataset and runs a LangSmith experiment, `--local` scores in-process and writes `results/agent_eval.json`:

```
builder eval agent
builder eval agent --local --limit 30
```

## Results

RESULTS_PLACEHOLDER

## Project layout

```
mockplatform/        FastAPI mock of the platform, 12 workflows, SQLAlchemy models
nocode_agent/
  config.py          settings
  llm.py             chat model and structured output helpers
  embeddings.py      sentence-transformers and hashing backends
  openapi.py         operation extraction and argument validation
  rag/               splitters, vector index, bm25, fusion, rerank, retriever, metrics
  agent/             state, planner, plan checker, crag subgraph, grader, executor, graph, runtime
  api/               FastAPI service with SSE streaming
  evals/             dataset generator, judges, scoring, langsmith and local runners
  cli.py             the builder command
docs/                knowledge base: guides, per-workflow API specs, openapi.json
data/eval/           generated question sets
results/             raw numbers from the eval scripts
tests/               pytest suite
```

`docs/openapi.json` is exported from the mock platform with `make openapi`.

## Testing

```
python -m pytest
```

The suite needs no API key and no network. It covers the splitters, BM25, metadata filters, RRF, reranker fallback, the retriever, the grader's routing decisions and the corrective subgraph with a fake LLM, graph routing with fake tools, the platform endpoints through `TestClient`, OpenAPI argument validation, the API and SSE stream, and the eval scoring. The Chroma tests are skipped if `chromadb` is not installed.
