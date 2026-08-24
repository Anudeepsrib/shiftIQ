FROM node:20-slim AS ui-builder

WORKDIR /app/ui
COPY ui/package*.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt pyproject.toml README.md LICENSE config.defaults.yaml ./
COPY src/ ./src/
COPY --from=ui-builder /app/ui/dist ./ui/dist

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && python -m pip install .

RUN mkdir -p /data/projects /data/shiftiq/workspaces /app/.migration-logs /app/.migration-checkpoints \
    && chown -R app:app /app /data/projects /data/shiftiq

USER app

ENV MIGRATION_SERVER__ENVIRONMENT=development \
    MIGRATION_SERVER__HOST=0.0.0.0 \
    MIGRATION_SERVER__PORT=8000 \
    MIGRATION_SERVER__DOCS_ENABLED=false \
    MIGRATION_SECURITY__ALLOWED_ROOTS='["/data/projects"]' \
    MIGRATION_OBSERVABILITY__LOG_FORMAT=json

EXPOSE 8000 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3).read()"

CMD ["uvicorn", "code_migration.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
