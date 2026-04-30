# ── Stage 1: Python deps ──────────────────────────────────────────────────────
FROM python:3.12-slim AS python-builder

WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Webapp (Mini App) ────────────────────────────────────────────────
FROM oven/bun:1-slim AS webapp-builder

WORKDIR /webapp
COPY cabinet/package.json cabinet/bun.lock* ./
RUN bun install --frozen-lockfile
COPY cabinet/ ./
RUN bun run build

# ── Stage 3: Final image ──────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

COPY --from=python-builder /usr/local/lib/python3.12/site-packages \
                           /usr/local/lib/python3.12/site-packages

COPY . .
COPY --from=webapp-builder /cabinet/dist ./cabinet/dist

RUN rm -rf /root/.cache cabinet/node_modules

CMD ["python", "main.py"]
