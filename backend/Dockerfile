# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install ".[dev]" 2>/dev/null || pip install --no-cache-dir --prefix=/install .

COPY . .

FROM python:3.12-slim AS runtime
WORKDIR /app

RUN groupadd -r civicpulse && useradd -r -g civicpulse civicpulse

COPY --from=builder /install /usr/local
COPY --from=builder /build/app ./app
COPY --from=builder /build/alembic ./alembic
COPY --from=builder /build/alembic.ini ./alembic.ini
COPY --from=builder /build/scripts ./scripts

RUN chown -R civicpulse:civicpulse /app
USER civicpulse

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://localhost:8000/health', timeout=2).status==200 else sys.exit(1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "20"]
