# Stage 1: install dependencies
FROM python:3.14-alpine AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock LICENSE README.md ./
RUN uv sync --frozen --no-dev

# Stage 2: runtime
FROM python:3.14-alpine
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN addgroup -S woodpecker && adduser -S woodpecker -G woodpecker
COPY --from=builder /app /app
WORKDIR /app
USER woodpecker
EXPOSE 8080
ENTRYPOINT ["uv", "run", "woodpecker-mcp"]
