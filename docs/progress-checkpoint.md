# Stato di avanzamento — InsightHub Roadmap

> Checkpoint per orchestrazione autonoma (subagent + rate-limit budget). Se una sessione viene
> interrotta, riprendere da qui: leggere la tabella, riprendere dal primo item non completato.
> Prima azione sempre: `bash ~/.claude/rate-limit.sh --fresh`.

Aggiornato: 2026-07-19T00:20 — Milestone 6 verificata e committata (vedi sotto), nessuna pausa
rate-limit attiva (5h: 44%, 7d: 75% all'inizio della sessione, entrambi ben sotto soglia 85%).

| Milestone | Stato | Note |
|---|---|---|
| 1 – Core Backend | ✅ completo | commit `ade1fe3` |
| 2 – Data Processing (Celery ingestion) | ✅ completo | commit `c56fae9` |
| 3 – Data Profiling | ✅ completo | commit `28f04af` — verificato (35/35 test, migration su Postgres reale) |
| 4 – Insight Engine | ✅ completo (tranne ML opzionale) | commit `8a9fdb7` — verificato (59/59 test, migration su Postgres reale). "Prime feature ML (opzionale)" lasciata non fatta, come da roadmap |
| 5 – Hardening | ✅ completo | commit `2cb0f69` — verificato (67/67 test, migration su Postgres reale upgrade/downgrade/upgrade, ruff+mypy clean) |
| 6 – Testing & Quality | ✅ completo | commit `a12f6b5` — verificato (85/85 test, coverage 96.27% con pytest-cov, ruff+black+mypy puliti, CI GitHub Actions aggiunta) |
| 7 – Frontend (opzionale) | ⏳ da fare | opzionale — confermare con l'utente prima di iniziare |

## Milestone 6 — come è stata trovata e verificata (2026-07-19T00:20)

Punto di partenza: la suite pytest esisteva già in gran parte dalle milestone precedenti
(tests/api/*, tests/services/*, tests/workers/*, 67 test) ma mancavano ancora, rispetto ai 4 item
della roadmap: uno strumento di coverage effettivamente configurato e misurato, test dedicati al
livello DB (a differenza dei test API/service, che passano tutti attraverso un DB SQLite in-memory
sostitutivo), e una pipeline CI di linting.

- **Baseline**: `pytest tests/ -q` dentro il container `api` → **67/67 passati**, confermando
  quanto dichiarato nel checkpoint di Milestone 5 prima di aggiungere qualunque cosa.
- **Coverage**: aggiunta `pytest-cov` come dev-dependency (`poetry add --group dev pytest-cov`),
  configurato `[tool.coverage.run] source = ["app"]` in `pyproject.toml`. Prima misurazione: 89%.
  Individuati i gap reali (non semplice inseguimento del numero): endpoint `PATCH /projects/{id}`
  mai testato, ramo utente disattivato/token senza `sub`/utente sconosciuto in `get_current_user`
  mai esercitato, CLI `app/cli/seed_user.py` a 0%. Aggiunti test mirati
  (`tests/api/test_projects.py`, `tests/api/test_auth.py`, nuovo `tests/cli/test_seed_user.py`) →
  coverage finale **96.27%**, ben oltre la soglia 70% richiesta dalla roadmap.
- **Test DB**: nuovo pacchetto `tests/db/`. `test_models.py` usa un engine SQLite dedicato con
  `PRAGMA foreign_keys=ON` (SQLite non applica le FK di default, a differenza del suo motore
  reale) per verificare vincoli unique (`Project.name`, `User.email`, `DatasetProfile.dataset_id`),
  default (`Dataset.status`, `User.is_active`) e cascade delete (`Project → Dataset →
  DatasetProfile/DatasetQualityIssue`) — lo stesso comportamento `ondelete="CASCADE"` dichiarato
  nei modelli e nella migration. `test_real_db.py` è un test di integrazione contro il Postgres
  reale (container `db`, già migrato a `d4004c929afe`/head): verifica che `get_db`/`SessionLocal`
  — il codice di produzione mai esercitato dal resto della suite, che sovrascrive sempre
  `get_db` con SQLite — funzionino davvero, con skip automatico (`pytest.mark.skipif`) se Postgres
  non è raggiungibile, così la suite resta eseguibile offline.
- **Ruff/black/mypy**: `ruff check app/ tests/` puliti (un `E402` intenzionale in
  `tests/conftest.py`, silenziato con un `per-file-ignores` mirato e commentato, non un
  `# noqa` sparso). Il drift di formattazione **pre-esistente** segnalato nel checkpoint di
  Milestone 5 (16 file in `app/`, saliti a 24 includendo `tests/`) è stato risolto applicando
  `black app/ tests/` per davvero — necessario perché altrimenti il nuovo gate CI sarebbe stato
  rosso fin dal primo commit; nessuna modifica di logica, solo riformattazione (verificato riga
  per riga nel diff). `mypy app/` segnalava 6 errori pre-esistenti (non introdotti in questa
  sessione, confermato con `git stash` sullo stato committato precedente): due erano un residuo di
  `.mypy_cache` stantio (spariti con cache pulita), i restanti 4 erano falsi positivi noti
  (pydantic-settings che richiede `database_url`/`jwt_secret_key` senza default Python — valori
  letti da env — e le firme di `add_exception_handler` di slowapi/Starlette più strette dello
  stub). Risolti con `# type: ignore[...]` mirati e commentati, più uno `ignore_missing_imports`
  per `pandas`/`celery.*` in `[tool.mypy]` (mancano gli stub, non è un problema del codice).
- **CI**: nuovo `.github/workflows/ci.yml` (GitHub Actions, come già deciso nelle decisioni utente
  di Milestone 5) con service container Postgres 16 e Redis 7, che esegue: `ruff check`,
  `black --check`, `mypy app/`, `alembic upgrade head` contro il Postgres del job, poi
  `pytest --cov=app --cov-fail-under=70`. Non eseguibile localmente tramite `act`/runner reale in
  questa sessione (nessun accesso a GitHub Actions), ma ogni comando del workflow è stato
  rieseguito **negli stessi passi, nello stesso ordine**, dentro il container `api` contro lo
  stesso Postgres reale — quindi la logica è verificata anche se il runner CI stesso non è stato
  osservato in azione.
- `.gitignore`: aggiunte le cache di test/lint (`.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`,
  `.coverage`, `htmlcov/`), mai ignorate esplicitamente prima (erano untracked "per disciplina").

## Milestone 5 — come è stata trovata e verificata (2026-07-18T21:50)

Una sessione precedente era stata interrotta a forza (bug del watchdog, poi corretto) dopo aver
scritto il lavoro della Milestone 5 su disco ma **senza committarlo** e senza aggiornare questo
checkpoint. Invece di riscrivere da zero, il lavoro non committato è stato revisionato e
verificato indipendentemente:

- Confrontato ogni file (routes_auth.py, security.py, rate_limit.py, dependencies.py, modello
  User, schemas, service, CLI seed, migration, test) con le "Decisioni utente" qui sotto — coerente
  su tutti i punti: nessun endpoint di registrazione pubblica, tutte le route esistenti protette da
  `get_current_user`, rate limiting slowapi Redis-backed per-IP, `/health` e `/auth/login` pubblici.
- `poetry install` dentro il container `api` (build pulita, tutte le nuove dipendenze —
  argon2-cffi, pyjwt, python-multipart, slowapi — risolte senza conflitti).
- `alembic upgrade head` su Postgres reale (container `db`), verificato `\d users` nello schema
  effettivo, poi `alembic downgrade -1 && alembic upgrade head` per confermare la reversibilità.
- `pytest tests/ -q` → **67/67 passati**.
- `ruff check app/` e `mypy app/` puliti. `black --check app/` segnala 16 file da riformattare, ma
  è un drift pre-esistente **non introdotto da questa milestone** (confermato con `git stash` +
  `black --check` sullo stato committato precedente, stesso risultato) — non è stato toccato.
- Committato in `2cb0f69` (non pushato).

Nota operativa: il primo tentativo di verifica migration ha rifatto `docker compose run` senza il
file `docker-compose.override.yml`, causando la ricreazione di `devcontainer-db-1`/`redis-1` con le
porte host di default (5432/6379) invece di quelle remappate (5544/6389), in conflitto con un
container Postgres di un altro progetto già sulla 5432 dell'host. Risolto rilanciando `up -d db
redis` con **entrambi** i file compose (`-f docker-compose.yml -f docker-compose.override.yml`).
Dati persistenti nel volume nominato `insighthub_pg`, quindi nessuna perdita — ma da tenere a
mente: usare sempre entrambi i file compose per questo progetto, mai solo il base.

## Decisioni utente raccolte per la Milestone 5 — Hardening

Raccolte il 2026-07-18 prima della pausa, da applicare alla ripresa:

1. **Modello di autenticazione**: JWT con **utenti pre-seedati, solo login** — NESSUN endpoint
   di registrazione pubblica self-service. Serve comunque un modello `User` (email/username +
   password hash con bcrypt/argon2) e un modo per crearne (seed script o comando admin/CLI, non
   un endpoint `/auth/register` pubblico). Endpoint `/auth/login` restituisce access token JWT
   (+ eventualmente refresh token — dettaglio tecnico lasciato all'implementazione).
2. **Scope della protezione**: **tutte le route esistenti** (`/api/v1/projects`, `/api/v1/datasets`
   e i nuovi endpoint `/ingest`, `/profile`, `/insights`) devono richiedere un JWT valido.
   Nessuna route pubblica salvo `/auth/login` stesso (e probabilmente `/health` se esiste).
3. **Rate limiting**: **Redis-backed, per-IP** (Redis è già nello stack per Celery). Usare una
   libreria consolidata (es. `slowapi` o `fastapi-limiter`), limite su tutte le route API.
4. **CI/CD**: già deciso dalla roadmap stessa → GitHub Actions (nessuna ambiguità qui).
5. Non specificato dall'utente, lasciato a discrezione dell'implementazione: dettagli su
   scadenza/refresh dei token JWT, libreria di rate limiting specifica, struttura esatta del
   comando/seed per creare utenti. Se emergono ulteriori scelte di prodotto genuinamente
   ambigue (non tecniche), fermarsi e chiedere invece di decidere silenziosamente.

## Decisioni tecniche prese durante l'orchestrazione

- **Milestone 3**: il modello `Dataset` non aveva un campo che punti al file reale. Decisione:
  aggiunta una colonna `file_path` (nullable, locale) via migration Alembic, per rendere
  profilabile un file CSV reale. Storage esterno (S3/blob) è fuori scope, non richiesto dalla
  roadmap.
- **Milestone 3**: se `file_path` è assente, l'ingestion salta il profiling (log + no-op). Se
  `file_path` è impostato ma il file non esiste su disco, è trattato come un fallimento vero
  dell'ingestion (va nel retry/failed esistente) invece di un no-op silenzioso — scelta tecnica
  ragionevole, confermata in fase di verifica.
- pandas 3.0.3 riporta il dtype delle colonne stringa come `"str"` invece del classico
  `"object"` di pandas <3.0. Da tenere a mente se la Milestone 4 costruisce regole di qualità
  dati sopra ai dtype riportati dal profiling.
- **Milestone 6**: il drift di formattazione black lasciato intenzionalmente intoccato in
  Milestone 5 è stato risolto (solo formattazione, verificato nel diff) perché altrimenti il
  nuovo gate CI sarebbe stato rosso da subito — non è più "pre-esistente e fuori scope" una volta
  che esiste una pipeline che deve restare verde.
- **Milestone 6**: `.mypy_cache/` stantia può nascondere/mostrare errori diversi da quelli reali
  (visto un falso "6 errori" che si è ridotto a "2" solo pulendo la cache) — da ripulire prima di
  fidarsi di un risultato mypy sospetto.
- **Milestone 6**: i test DB usano SQLite con `PRAGMA foreign_keys=ON` per i vincoli/cascade
  (veloce, nessuna dipendenza esterna) e un test separato, skippabile, contro Postgres reale per
  il codice `get_db`/`SessionLocal` che il resto della suite sovrascrive sempre — scelta tecnica
  per coprire sia la velocità sia il path di produzione reale, senza appesantire tutta la suite
  con una dipendenza Postgres obbligatoria.

## Se interrotto per soglia rate-limit

1. Fermare il subagent in corso (`TaskStop`), segnare la milestone come "🔄 interrotto" qui sotto.
2. Non fidarsi del report del subagent: verificare lo stato reale di file/test prima di riprendere.
3. Committare solo ciò che è effettivamente in stato buono (test passanti); altrimenti lasciare
   il working tree com'è e annotare qui cosa manca.
4. Wakeup programmato via `pm-agent/add-wakeup.py` con prompt che punta a questo file.
