# Stato di avanzamento — InsightHub Roadmap

> Checkpoint per orchestrazione autonoma (subagent + rate-limit budget). Se una sessione viene
> interrotta, riprendere da qui: leggere la tabella, riprendere dal primo item non completato.
> Prima azione sempre: `bash ~/.claude/rate-limit.sh --fresh`.

Aggiornato: 2026-07-18T19:38 (pausa orchestrazione: soglia rate-limit 5h raggiunta — 80%)

| Milestone | Stato | Note |
|---|---|---|
| 1 – Core Backend | ✅ completo | commit `ade1fe3` |
| 2 – Data Processing (Celery ingestion) | ✅ completo | commit `c56fae9` |
| 3 – Data Profiling | ✅ completo | commit `28f04af` — verificato (35/35 test, migration su Postgres reale) |
| 4 – Insight Engine | ✅ completo (tranne ML opzionale) | commit `8a9fdb7` — verificato (59/59 test, migration su Postgres reale). "Prime feature ML (opzionale)" lasciata non fatta, come da roadmap |
| 5 – Hardening | ⏸️ **PROSSIMO — non ancora iniziato** | decisioni utente raccolte (vedi sotto), pronto per spawn del subagent appena il budget lo consente |
| 6 – Testing & Quality | ⏳ da fare | |
| 7 – Frontend (opzionale) | ⏳ da fare | opzionale — confermare con l'utente prima di iniziare |

## Perché ci si è fermati qui

Watchdog rate-limit ha segnalato **5h = 80% (soglia raggiunta)** alle 2026-07-18T19:38 UTC, reset
finestra alle **2026-07-18 22:40** (7d era al 70%, ben sotto la soglia di stop totale 85%).
Nessun subagent era in esecuzione al momento dello stop (Milestone 4 era già stata committata e
verificata) — non c'è nulla da segnare come "interrotto a metà".

Wakeup programmato via `pm-agent/add-wakeup.py` per **2026-07-18T22:45** (reset + 5 min).

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

## Se interrotto per soglia rate-limit

1. Fermare il subagent in corso (`TaskStop`), segnare la milestone come "🔄 interrotto" qui sotto.
2. Non fidarsi del report del subagent: verificare lo stato reale di file/test prima di riprendere.
3. Committare solo ciò che è effettivamente in stato buono (test passanti); altrimenti lasciare
   il working tree com'è e annotare qui cosa manca.
4. Wakeup programmato via `pm-agent/add-wakeup.py` con prompt che punta a questo file.
