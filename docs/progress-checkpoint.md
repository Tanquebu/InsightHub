# Stato di avanzamento — InsightHub Roadmap

> Checkpoint per orchestrazione autonoma (subagent + rate-limit budget). Se una sessione viene
> interrotta, riprendere da qui: leggere la tabella, riprendere dal primo item non completato.
> Prima azione sempre: `bash ~/.claude/rate-limit.sh --fresh`.

Aggiornato: 2026-07-18T19:25 (pausa orchestrazione: budget 5h vicino a soglia + Milestone 5 richiede decisioni utente)

| Milestone | Stato | Note |
|---|---|---|
| 1 – Core Backend | ✅ completo | commit `ade1fe3` |
| 2 – Data Processing (Celery ingestion) | ✅ completo | commit `c56fae9` |
| 3 – Data Profiling | ✅ completo | commit `28f04af` — verificato (35/35 test, migration su Postgres reale) |
| 4 – Insight Engine | ✅ completo (tranne ML opzionale) | commit `8a9fdb7` — verificato (59/59 test, migration su Postgres reale). "Prime feature ML (opzionale)" lasciata non fatta, come da roadmap |
| 5 – Hardening | ⏸️ in pausa | **richiede decisioni utente prima di procedere** (vedi sotto) — non ancora spawnato alcun subagent |
| 6 – Testing & Quality | ⏳ da fare | |
| 7 – Frontend (opzionale) | ⏳ da fare | opzionale — confermare con l'utente prima di iniziare |

## Perché ci si è fermati qui

1. **Budget rate-limit**: 5h al 77% (soglia di stop nuovi spawn: 80%), 7d al 70%. Non ancora
   sopra soglia, ma abbastanza vicino da non voler avviare un altro subagent lungo senza
   prima far scendere la finestra o avere conferma dall'utente.
2. **Milestone 5 — Hardening richiede decisioni di prodotto/architettura che non sono nella
   roadmap**: non esiste ancora nessun modello `User`/sistema di autenticazione in questo
   progetto. "Autenticazione (JWT)" implica scelte reali (single-tenant o multi-utente,
   registrazione self-service o utenti pre-seedati, quali route proteggere, ruoli/permessi).
   "Rate limiting" implica una scelta di libreria/strategia (per-IP? per-API-key? backend
   Redis?). Il CI/CD è invece già deciso dalla roadmap stessa (GitHub Actions).

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
