# CLAUDE.md

Questo file fornisce indicazioni a Claude Code (claude.ai/code) quando lavora con il codice in questo repository.

## Panoramica del Progetto

InsightHub è un servizio API-first per il profiling dei dati e il calcolo di score di qualità, costruito con FastAPI, PostgreSQL e Redis. Il backend adotta un'architettura a livelli pulita (Routes → Services → DB models).

## Ambiente di Sviluppo

Il progetto utilizza **Dev Containers** (VS Code). Il dev container esegue lo stack completo tramite `docker-compose` (API sulla porta 8000, PostgreSQL su 5432, Redis su 6379).

Le dipendenze sono gestite con **Poetry**. Il Dockerfile installa le dipendenze al momento del build (nessun virtualenv all'interno del container, `virtualenvs.create false`).

## Comandi Comuni

```bash
# Installa le dipendenze (dentro il devcontainer)
poetry install

# Avvia il server API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Linting e formattazione
ruff check app/
black app/
mypy app/

# Migrazioni del database
alembic upgrade head
alembic revision --autogenerate -m "descrizione"
alembic downgrade -1

# Test (non ancora presenti)
pytest tests/
pytest tests/path/to/test_file.py::test_name  # singolo test
```

## Architettura

```
app/
├── main.py              # App FastAPI, registrazione dei router
├── api/v1/              # Livello HTTP: parsing delle richieste, codici di risposta, eccezioni HTTP
├── services/            # Business logic, eccezioni personalizzate, gestione transazioni DB
├── db/
│   ├── models/          # Modelli ORM SQLAlchemy 2.0 (sintassi Mapped)
│   ├── session.py       # Engine + SessionLocal
│   └── base.py          # DeclarativeBase
├── schemas/             # Modelli Pydantic per richieste/risposte
└── core/
    ├── config.py        # Settings tramite pydantic-settings (legge da .env)
    └── dependencies.py  # Dipendenza FastAPI get_db()
```

**Flusso delle richieste:** Route handler → valida l'input con lo schema Pydantic → chiama la funzione di servizio con `db: Session` → il servizio esegue commit/rollback → la route restituisce lo schema di risposta Pydantic.

**Pattern di gestione degli errori:** I servizi sollevano eccezioni personalizzate (es. `ProjectAlreadyExists`); le route le intercettano e sollevano `HTTPException` con i codici di stato appropriati.

## Convenzioni Principali

- Tutte le route API sono versionate sotto `/api/v1`
- I modelli SQLAlchemy usano la sintassi moderna `Mapped[type]`
- Tutti i timestamp sono timezone-aware (`DateTime(timezone=True)`) con default lato server
- Le funzioni di servizio gestiscono esplicitamente `db.commit()` / `db.rollback()` — le route non toccano le transazioni
- Gli schema di risposta Pydantic usano `model_config = ConfigDict(from_attributes=True)` per il mapping ORM→schema
- Gli endpoint PATCH usano schema con tutti i campi opzionali; le funzioni di servizio ignorano i valori `None`

## Note sull'Infrastruttura

- **Celery worker** e **Redis** sono definiti in docker-compose ma non ancora implementati (`app.workers.celery_app` non esiste)
- Le migrazioni si trovano in `alembic/versions/`; `alembic/env.py` importa `Base.metadata` e legge `DATABASE_URL` da `app.core.config.settings`
- `pool_pre_ping=True` è impostato sull'engine per gestire le connessioni non più valide
