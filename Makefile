PYTHON ?= python

.PHONY: install test platform api ingest dataset eval-retrieval eval-agent openapi clean

install:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e . --no-deps

test:
	$(PYTHON) -m pytest

platform:
	builder platform --port 9000

api:
	builder serve --port 8000

ingest:
	builder ingest --reset

dataset:
	builder dataset

eval-retrieval:
	builder eval retrieval --show-misses

eval-agent:
	builder eval agent

openapi:
	$(PYTHON) -m mockplatform.export docs/openapi.json

clean:
	rm -rf chroma_data checkpoints.db platform.db .pytest_cache
