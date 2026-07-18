# Stato di avanzamento — InsightHub Roadmap

> Checkpoint per orchestrazione autonoma (subagent + rate-limit budget). Se una sessione viene
> interrotta, riprendere da qui: leggere la tabella, riprendere dal primo item non completato.
> Prima azione sempre: `bash ~/.claude/rate-limit.sh --fresh`.

Aggiornato: 2026-07-18T19:20 (Milestone 3 completata e verificata)

| Milestone | Stato | Note |
|---|---|---|
| 1 – Core Backend | ✅ completo | commit `ade1fe3` |
| 2 – Data Processing (Celery ingestion) | ✅ completo | commit `c56fae9` |
| 3 – Data Profiling | ✅ completo | verificato indipendentemente (35/35 test, migration upgrade/downgrade/upgrade su Postgres reale) — pronto per commit |
| 4 – Insight Engine | ⏳ prossimo | |
| 5 – Hardening | ⏳ da fare | probabile checkpoint utente (strategia auth JWT, provider CI/CD) |
| 6 – Testing & Quality | ⏳ da fare | |
| 7 – Frontend (opzionale) | ⏳ da fare | opzionale — confermare con l'utente prima di iniziare |

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
