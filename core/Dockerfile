FROM python:3.11.9-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /usr/local/bin/uv

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY core/pyproject.toml core/uv.lock core/.python-version ./
RUN uv sync --frozen --group dev --group dataset

COPY core/configs ./configs
COPY core/assets ./assets
COPY core/scripts ./scripts
COPY core/data ./data
COPY core/src ./src
COPY core/tests ./tests
COPY contracts /contracts

RUN useradd --create-home core && chown -R core /app
USER core

CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "--threads=2", "--call", "hts_core.adapters.http:create_app"]
