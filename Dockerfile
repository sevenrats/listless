# syntax=docker/dockerfile:1
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Copy only dependency files first for better caching
COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    apk add --no-cache \
        libgcc \
        libstdc++ \
        libffi && \
    apk add --no-cache --virtual .build-deps \
        build-base \
        gcc \
        musl-dev \
        cargo \
        rust \
        libffi-dev && \
    uv export --format requirements.txt --no-dev -o requirements.txt && \
    uv pip sync --system requirements.txt && \
    apk del .build-deps
# Now copy your app code
COPY . .

# Writable directory for SQLite database
RUN mkdir -p /app/data

# Run as non-root (recommended)
RUN adduser -D appuser && chown appuser:appuser /app/data
USER appuser

EXPOSE 8000
CMD ["python", "main.py"]
