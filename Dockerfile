# Stage 1: install dependencies and the application
FROM python:3.14-alpine AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.17 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock LICENSE README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

# Stage 2: runtime
FROM python:3.14-alpine
RUN addgroup -S woodpecker && adduser -S woodpecker -G woodpecker
COPY --from=builder --chown=woodpecker:woodpecker /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
USER woodpecker
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/up', timeout=3)"]
ENTRYPOINT ["/app/.venv/bin/woodpecker-mcp"]
CMD ["--host", "0.0.0.0"]
