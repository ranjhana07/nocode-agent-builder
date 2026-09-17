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

EXPOSE 8000 9000

CMD ["builder", "serve", "--port", "8000"]
