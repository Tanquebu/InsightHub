FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git \
  && rm -rf /var/lib/apt/lists/*

# Poetry
ENV POETRY_VERSION=1.8.3
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /workspace

# Copy only dependency files first (better layer caching)
COPY pyproject.toml poetry.lock* /workspace/

# Install deps
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the code
COPY . /workspace
