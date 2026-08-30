FROM node:22-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MATHARC_CODEX_WORKSPACE=/app \
    MATHARC_CODEX_SESSION_DIR=/app/.matharc/codex-sessions \
    MATHARC_CODEX_SANDBOX=read-only \
    MATHARC_CODEX_NETWORK=0 \
    MATHARC_CODEX_WEB_SEARCH=disabled

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv "$VIRTUAL_ENV" \
    && npm install -g @openai/codex

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir ".[research]" \
    && python -m unittest discover -s tests -v \
    && python -m matharc demo --out-dir artifacts/demo \
    && python -m matharc validate --run artifacts/demo/run.json \
    && python scripts/v0_1_acceptance.py \
    && mkdir -p /app/.matharc/codex-sessions /app/artifacts \
    && chown -R node:node /app

USER node
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"

CMD ["sh", "-c", "python -m matharc demo --out-dir artifacts/demo && python -m matharc serve --run artifacts/demo/run.json --workspace /app --host 0.0.0.0 --port 8000"]
