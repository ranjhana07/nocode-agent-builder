FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/models

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY pyproject.toml README.md ./
COPY nocode_agent ./nocode_agent
COPY mockplatform ./mockplatform
COPY docs ./docs
COPY data ./data
RUN pip install --no-cache-dir --no-deps .

RUN useradd --create-home --uid 1000 builder && mkdir -p /data /models && chown -R builder /app /data /models
USER builder

EXPOSE 8000 9000

HEALTHCHECK --interval=15s --timeout=3s --retries=5     CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["builder", "serve", "--port", "8000"]
