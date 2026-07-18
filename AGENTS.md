# Linee guida del repository

## Struttura del progetto e organizzazione dei moduli

InsightHub è un backend API-first basato su Python 3.11 e FastAPI. Il codice in `app/` segue un'architettura a livelli: gli handler in `api/v1/` chiamano `services/`, che opera sui modelli SQLAlchemy in `db/models/`. Gli schemi Pydantic appartengono a `schemas/`; configurazione, logging, dipendenze ed eccezioni a `core/`. Mantieni nelle route solo la logica HTTP e gestisci le transazioni nei servizi.

Le migrazioni sono in `alembic/versions/`. I test delle API sono sotto `tests/api/`, con fixture comuni in `tests/conftest.py`. I container sono configurati in `docker/`; dipendenze e strumenti in `pyproject.toml`.

## Comandi di build, test e sviluppo

- `poetry install`: installa tutte le dipendenze.
- `alembic upgrade head`: applica tutte le migrazioni del database.
- `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`: avvia l'API; Swagger UI è su `/docs`.
- `pytest tests/`: esegue tutti i test. Per un singolo test usa `pytest tests/api/test_projects.py::test_create_project`.
- `ruff check app/ tests/`: esegue il linting.
- `black --check app/ tests/`: verifica la formattazione; senza `--check` la applica.
- `mypy app/`: esegue i controlli statici dei tipi.

Esegui preferibilmente i comandi nel Dev Container. API e migrazioni richiedono un `DATABASE_URL` valido; usa `.env.example` come modello e non versionare segreti.

## Stile del codice e convenzioni di denominazione

Usa quattro spazi, formattazione Black e annotazioni di tipo per le funzioni pubbliche. Adotta `snake_case` per moduli, funzioni e variabili; `PascalCase` per classi ORM e Pydantic. Usa SQLAlchemy moderno con `Mapped[...]` e timestamp con timezone. Versiona le route sotto `/api/v1`. Assegna descrizioni concise alle revisioni, ad esempio `alembic revision --autogenerate -m "add profile status"`.

## Linee guida per i test

I test usano pytest e `TestClient` di FastAPI. La fixture automatica ricrea SQLite in memoria per ogni test: mantieni i test indipendenti. Nomina i file `test_<funzionalità>.py` e le funzioni `test_<comportamento>`. Copri successo, validazione, conflitti, risorse mancanti e persistenza. Non esiste una soglia di copertura; accompagna ogni correzione con un test di regressione.

## Commit e pull request

Segui il formato Conventional Commits già presente: `feat: ...`, `feat(projects): ...` o `chore(devcontainer): ...`. Crea commit mirati con oggetti brevi e in forma imperativa. Le pull request devono descrivere la modifica, indicare migrazioni o nuove configurazioni, collegare le issue pertinenti ed elencare i comandi di verifica. Per modifiche alle API includi esempi di richiesta e risposta; aggiungi screenshot solo per cambiamenti visivi alla documentazione.
