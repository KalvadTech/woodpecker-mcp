# Stage 1: install dependencies
FROM python:3.14-alpine AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Stage 2: runtime
FROM python:3.14-alpine
RUN addgroup -S woodpecker && adduser -S woodpecker -G woodpecker
COPY --from=builder /app /app
WORKDIR /app
USER woodpecker
EXPOSE 8080
ENTRYPOINT ["uv", "run", "woodpecker-mcp"]
