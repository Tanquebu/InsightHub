# InsightHub

API-first backend for data profiling and quality scoring, built with FastAPI and PostgreSQL.

## Tech stack

- Python 3.11 + Poetry
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (sync) + Alembic
- PostgreSQL · Redis
- structlog
- Docker / Dev Containers

## Getting started

The project runs inside a **Dev Container** (VS Code + Docker). Open the repo in VS Code and choose "Reopen in Container".

```bash
# Install dependencies
poetry install

# Apply DB migrations
alembic upgrade head

# Start the API (hot-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at `http://localhost:8000/docs`.

## Running tests

```bash
pytest tests/
```

## Project structure

```
app/
├── api/v1/          # Route handlers (HTTP layer only)
├── services/        # Business logic + custom exceptions
├── db/
│   ├── models/      # SQLAlchemy ORM models
│   └── session.py   # Engine + SessionLocal
├── schemas/         # Pydantic request/response models
└── core/
    ├── config.py    # Settings via pydantic-settings
    ├── dependencies.py
    ├── exceptions.py
    └── logging.py
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects` | List projects |
| GET | `/api/v1/projects/{id}` | Get project |
| PATCH | `/api/v1/projects/{id}` | Update project |
| DELETE | `/api/v1/projects/{id}` | Delete project |
| POST | `/api/v1/projects/{id}/datasets` | Create dataset |
| GET | `/api/v1/projects/{id}/datasets` | List datasets |
| GET | `/api/v1/projects/{id}/datasets/{did}` | Get dataset |
| PATCH | `/api/v1/projects/{id}/datasets/{did}` | Update dataset |
| DELETE | `/api/v1/projects/{id}/datasets/{did}` | Delete dataset |

## Status

Milestone 1 – Core Backend: complete.
