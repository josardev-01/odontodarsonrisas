# syntax=docker/dockerfile:1
# Las imagenes deben validarse en la arquitectura OCI real y fijarse por digest
# antes de produccion. No se fuerza TARGETARCH para conservar un build nativo.
FROM ghcr.io/astral-sh/uv:0.8.22 AS uv
FROM python:3.12-slim AS builder

COPY --from=uv /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /build
COPY pyproject.toml uv.lock ./
COPY . ./
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --create-home app

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/alembic.ini /app/alembic.ini
COPY --from=builder /build/migrations /app/migrations

USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ready', timeout=2)"]

# Contrato provisional: el paquete debe exponer app.main:app.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
